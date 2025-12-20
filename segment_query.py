# -*- coding: utf-8 -*-
"""
分段查询引擎
实现分段式多模式交通查询和智能组合

核心设计：
1. 每个线程只负责查询一段行程（A→B）
2. 支持多模式组合：飞机→飞机、飞机→高铁、高铁→飞机、高铁→高铁
3. 结果存储后由程序/AI智能组合出最优方案
4. 国际城市只查机票，不查火车票
5. 智能路线类型检测：自动识别国内、国际路线，选择合适的中转枢纽
"""

import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

# 导入中转枢纽管理器
from transfer_hubs import (
    hub_manager,
    detect_route_type,
    get_route_type_description,
    RouteType
)

# 导入路线计算引擎
from route_calculator import RouteCalculator, RoutePlan, TransportSegment


# 国际城市列表（这些城市没有中国火车站代码）
INTERNATIONAL_CITIES: Set[str] = {
    # 东南亚
    "曼谷", "新加坡", "吉隆坡", "雅加达", "马尼拉", "河内", "胡志明市",
    "金边", "万象", "仰光", "清迈", "普吉岛", "芭提雅", "苏梅岛",
    "巴厘岛", "岘港", "芽庄", "暹粒", "槟城", "兰卡威", "沙巴", "文莱",
    # 东亚
    "东京", "大阪", "名古屋", "福冈", "札幌", "冲绳",
    "首尔", "釜山", "济州岛", "乌兰巴托",
    # 南亚
    "新德里", "孟买", "班加罗尔", "加尔各答", "金奈",
    "科伦坡", "马尔代夫", "加德满都", "达卡", "卡拉奇", "伊斯兰堡",
    # 中东
    "迪拜", "阿布扎比", "多哈", "利雅得", "吉达", "科威特", "巴林",
    "马斯喀特", "特拉维夫", "安曼", "贝鲁特", "伊斯坦布尔", "安卡拉", "德黑兰",
    # 欧洲
    "伦敦", "巴黎", "法兰克福", "阿姆斯特丹", "慕尼黑", "苏黎世",
    "罗马", "米兰", "马德里", "巴塞罗那", "维也纳", "布鲁塞尔", "日内瓦",
    "莫斯科", "圣彼得堡", "赫尔辛基", "斯德哥尔摩", "哥本哈根", "奥斯陆",
    "华沙", "布拉格", "布达佩斯", "雅典", "里斯本", "都柏林", "爱丁堡", "曼彻斯特",
    # 北美
    "纽约", "洛杉矶", "旧金山", "芝加哥", "西雅图", "波士顿",
    "华盛顿", "达拉斯", "休斯顿", "亚特兰大", "迈阿密", "拉斯维加斯",
    "檀香山", "丹佛", "凤凰城", "底特律", "费城", "明尼阿波利斯",
    "温哥华", "多伦多", "蒙特利尔", "卡尔加里", "渥太华",
    # 中南美洲
    "墨西哥城", "坎昆", "圣保罗", "里约热内卢", "布宜诺斯艾利斯",
    "圣地亚哥", "利马", "波哥大", "巴拿马城", "哈瓦那",
    # 大洋洲
    "悉尼", "墨尔本", "布里斯班", "珀斯", "阿德莱德",
    "奥克兰", "惠灵顿", "基督城", "斐济", "关岛", "塞班岛", "帕劳",
    # 非洲
    "开罗", "约翰内斯堡", "开普敦", "内罗毕", "卡萨布兰卡",
    "拉各斯", "亚的斯亚贝巴", "毛里求斯", "塞舌尔",
}


def is_international_city(city: str) -> bool:
    """
    检查城市是否是国际城市（无法查询中国火车票）

    Args:
        city: 城市名

    Returns:
        True 如果是国际城市，False 如果是中国国内城市
    """
    # 精确匹配
    if city in INTERNATIONAL_CITIES:
        return True
    # 包含匹配（处理带机场名的情况，如"曼谷素万那普"）
    for intl_city in INTERNATIONAL_CITIES:
        if intl_city in city or city in intl_city:
            return True
    return False


class TransportMode(Enum):
    """交通方式"""
    FLIGHT = "flight"
    TRAIN = "train"


@dataclass
class SegmentQuery:
    """一段行程的查询请求"""
    from_city: str
    to_city: str
    date: str
    mode: TransportMode
    segment_id: str = ""  # 唯一标识，如 "origin_to_hub1_flight"


@dataclass
class SegmentResult:
    """一段行程的查询结果"""
    segment_id: str
    from_city: str
    to_city: str
    mode: TransportMode
    success: bool
    data: str = ""  # MCP 返回的原始数据
    error: str = ""
    query_time: float = 0.0  # 查询耗时（秒）


@dataclass
class RouteOption:
    """一条完整路线（可能包含多段）"""
    segments: List[SegmentResult]
    total_legs: int  # 总段数
    description: str = ""  # 路线描述，如 "曼谷→✈️→北京→🚄→长治"


class SegmentQueryEngine:
    """
    分段查询引擎

    架构说明：
    - 将整个行程拆分为多个"段"
    - 火车票查询：低并发执行（12306 有一定反爬限制，建议 5 并发）
    - 机票查询：串行执行（携程反爬严格，需避免并发冲突）
    - 结果收集后组合成完整路线
    """

    def __init__(
        self,
        mcp_manager,  # MCPServiceManager 实例
        log_callback: Optional[Callable[[str], None]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        accommodation_threshold_hours: int = 6,
        accommodation_enabled: bool = True
    ):
        self.mcp_manager = mcp_manager
        self.log_callback = log_callback or (lambda msg: None)
        self.progress_callback = progress_callback or (lambda cur, total, desc: None)

        # 线程安全的结果存储
        self._results_lock = threading.Lock()
        self._segment_results: Dict[str, SegmentResult] = {}

        # 站点代码缓存（避免重复查询）
        self._station_cache: Dict[str, str] = {}
        self._station_cache_lock = threading.Lock()

        # 机票服务预热状态
        self._flight_warmed_up = False

        # 路线信息缓存（用于UI显示）
        self._route_info: Optional[Dict] = None

        # 路线计算引擎
        self._route_calculator = RouteCalculator(
            accommodation_threshold_hours=accommodation_threshold_hours,
            accommodation_enabled=accommodation_enabled
        )

    def _is_valid_response(self, data: str) -> bool:
        """
        检查MCP返回的数据是否有效

        Args:
            data: MCP工具返回的字符串数据

        Returns:
            True 如果数据有效，False 如果是错误或超时
        """
        if not data:
            return False

        # 转为小写进行检查
        data_lower = data.lower()

        # 检查常见的错误标识
        error_indicators = [
            "超时",
            "timeout",
            "error",
            "failed",
            "失败",
            "异常",
            "exception",
            "无法",
            "cannot",
            "未找到",
            "not found",
            "无数据",
            "no data",
            "查询失败"
        ]

        for indicator in error_indicators:
            if indicator in data_lower:
                return False

        # 检查是否包含有效数据的标识（JSON格式或结构化数据）
        # 火车票和机票数据通常包含这些关键字
        valid_indicators = [
            "flight",
            "train",
            "航班",
            "车次",
            "price",
            "价格",
            "departure",
            "arrival",
            "出发",
            "到达"
        ]

        # 至少包含一个有效标识才认为是有效数据
        has_valid_indicator = any(indicator in data_lower for indicator in valid_indicators)

        return has_valid_indicator

    def get_smart_hub_cities(
        self,
        origin: str,
        destination: str,
        max_count: int = 15,
        transport_type: str = "all",
        use_international_hubs: bool = True
    ) -> Tuple[List[str], RouteType, str]:
        """
        智能获取中转枢纽城市

        根据出发地和目的地自动检测路线类型，返回最合适的中转枢纽。

        Args:
            origin: 出发城市
            destination: 目的城市
            max_count: 最大枢纽数量
            transport_type: 交通方式 ("all", "flight", "train")
            use_international_hubs: 是否使用国际枢纽（国内↔国外路线时有效）

        Returns:
            Tuple[List[str], RouteType, str]:
                - 推荐的中转城市列表
                - 检测到的路线类型
                - 提示信息（用于UI显示）
        """
        hubs, route_type, tip = hub_manager.get_hubs_for_route(
            origin, destination, max_count, transport_type, use_international_hubs
        )

        # 缓存路线信息
        self._route_info = {
            "route_type": route_type,
            "route_type_name": get_route_type_description(route_type),
            "is_international": route_type != RouteType.DOMESTIC,
            "hub_count": len(hubs),
            "hubs": hubs,
            "tip_message": tip,
        }

        return hubs, route_type, tip

    def get_route_info(self) -> Optional[Dict]:
        """
        获取当前路线信息（用于UI显示）

        Returns:
            包含路线类型、国际化状态、枢纽信息的字典，如果未执行过查询则返回 None
        """
        return self._route_info

    def log(self, message: str):
        """记录日志"""
        self.log_callback(message)

    def warmup_flight_service(
        self,
        test_from: str = "北京",
        test_to: str = "上海",
        test_date: str = None,
        timeout: float = 150
    ) -> bool:
        """
        预热机票服务：执行一次查询以触发验证码处理

        在开始批量查询前调用此方法，确保：
        1. 浏览器 Cookie 已保存
        2. 验证码已被用户处理
        3. 后续查询可以正常进行

        Args:
            test_from: 测试出发城市（默认北京）
            test_to: 测试目的城市（默认上海）
            test_date: 测试日期（默认明天）
            timeout: 超时时间（秒），默认150秒，需要足够时间让用户处理验证码

        Returns:
            True 如果预热成功，False 如果失败
        """
        if self._flight_warmed_up:
            self.log("[预热] 机票服务已预热，跳过")
            return True

        if not self.mcp_manager.flight_running:
            self.log("[预热] 机票服务未启动，跳过预热")
            return False

        # 默认使用明天的日期
        if not test_date:
            test_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        self.log(f"[预热] 开始预热机票服务（{test_from}→{test_to}）...")
        self.log("[预热] ⏳ 正在启动浏览器并加载页面...")
        self.log("[预热] =" * 25)
        self.log("[预热] ⚠️ 如果弹出浏览器窗口，请完成验证码验证！")
        self.log("[预热] ⚠️ 最多等待 120 秒，请耐心操作")
        self.log("[预热] =" * 25)

        try:
            # 执行一次机票查询，触发验证码检测
            # 给足够的时间：浏览器启动 + 页面加载 + 可能的验证码处理
            result = self.mcp_manager.call_tool(
                "flight_searchFlightRoutes",
                {
                    "departure_city": test_from,
                    "destination_city": test_to,
                    "departure_date": test_date
                },
                timeout=timeout
            )

            # 检查结果是否有效
            if result and "超时" not in result and "error" not in result.lower():
                self._flight_warmed_up = True
                self.log("[预热] ✅ 机票服务预热成功！后续查询将更快")
                return True
            elif "超时" in result:
                self.log("[预热] ⚠️ 预热超时，可能是页面加载较慢或验证码未处理")
                self.log("[预热] 💡 将继续尝试查询，如遇验证码请及时处理")
                # 超时不算完全失败，可能只是第一次慢
                return False
            else:
                self.log(f"[预热] ⚠️ 预热返回异常: {result[:200] if result else '空结果'}")
                return False

        except Exception as e:
            self.log(f"[预热] ❌ 预热失败: {str(e)}")
            return False

    def get_station_code(self, city: str) -> str:
        """
        获取城市的火车站代码（带缓存）

        Args:
            city: 城市名

        Returns:
            站点代码，如果无法获取则返回空字符串
        """
        # 检查缓存
        with self._station_cache_lock:
            if city in self._station_cache:
                return self._station_cache[city]

        # 查询
        if not self.mcp_manager.train_running:
            return ""

        try:
            result = self.mcp_manager.call_tool(
                "train_get-station-code-of-citys",
                {"citys": city}
            )
            stations = json.loads(result)
            code = stations.get(city, {}).get("station_code", "")

            # 缓存结果
            with self._station_cache_lock:
                self._station_cache[city] = code

            return code
        except Exception as e:
            self.log(f"[站点代码] {city} 查询失败: {e}")
            return ""

    def query_single_segment(
        self,
        query: SegmentQuery,
        train_date: str = None  # 火车票可能需要不同日期（12306限制）
    ) -> SegmentResult:
        """
        查询单段行程

        Args:
            query: 查询请求
            train_date: 火车票查询日期（处理12306的15天限制）

        Returns:
            查询结果
        """
        start_time = datetime.now()
        segment_id = query.segment_id or f"{query.from_city}_{query.to_city}_{query.mode.value}"

        result = SegmentResult(
            segment_id=segment_id,
            from_city=query.from_city,
            to_city=query.to_city,
            mode=query.mode,
            success=False
        )

        try:
            if query.mode == TransportMode.FLIGHT:
                # 查询机票
                if not self.mcp_manager.flight_running:
                    result.error = "机票服务未启动"
                    return result

                # 【新增】航班查询失败自动重试机制（最多重试2次）
                max_retries = 2
                retry_count = 0
                data = None

                while retry_count <= max_retries:
                    if retry_count > 0:
                        self.log(f"[✈️ {query.from_city}→{query.to_city}] 第{retry_count}次重试...")

                    # 【修复】使用更长的超时时间（120秒），给浏览器足够时间处理反爬机制
                    data = self.mcp_manager.call_tool(
                        "flight_searchFlightRoutes",
                        {
                            "departure_city": query.from_city,
                            "destination_city": query.to_city,
                            "departure_date": query.date
                        },
                        timeout=120  # 增加到120秒
                    )

                    # 检查返回的数据是否有效
                    if self._is_valid_response(data):
                        # 进一步检查：确保不是返回0条航班
                        if "找到 0 条航班" not in data and "0条航班" not in data:
                            result.success = True
                            result.data = data
                            if retry_count > 0:
                                self.log(f"[✈️ {query.from_city}→{query.to_city}] ✅ 重试成功")
                            break
                        else:
                            # 返回0条航班，可能是反爬或页面问题，尝试重试
                            if retry_count < max_retries:
                                self.log(f"[✈️ {query.from_city}→{query.to_city}] ⚠️ 返回0条航班，将重试...")
                                retry_count += 1
                                continue
                            else:
                                # 已达到最大重试次数
                                result.success = False
                                result.data = data
                                result.error = "查询返回0条航班（已重试2次）"
                                self.log(f"[✈️ {query.from_city}→{query.to_city}] ❌ 重试{max_retries}次后仍返回0条航班")
                                break
                    else:
                        # 查询失败或超时
                        if retry_count < max_retries:
                            self.log(f"[✈️ {query.from_city}→{query.to_city}] ⚠️ 查询失败，将重试...")
                            retry_count += 1
                            continue
                        else:
                            result.success = False
                            result.data = data
                            result.error = "查询失败或超时（已重试2次）"
                            self.log(f"[✈️ {query.from_city}→{query.to_city}] ❌ 重试{max_retries}次后仍失败")
                            break

            elif query.mode == TransportMode.TRAIN:
                # 查询火车票
                if not self.mcp_manager.train_running:
                    result.error = "火车票服务未启动"
                    return result

                # 获取站点代码
                from_station = self.get_station_code(query.from_city)
                to_station = self.get_station_code(query.to_city)

                if not from_station:
                    result.error = f"无法获取 {query.from_city} 的站点代码（可能是国际城市）"
                    return result
                if not to_station:
                    result.error = f"无法获取 {query.to_city} 的站点代码（可能是国际城市）"
                    return result

                # 使用火车票日期（可能因12306限制而调整）
                use_date = train_date or query.date

                # 【新增】火车票查询失败自动重试机制（最多重试2次，共3次尝试）
                max_retries = 2
                retry_count = 0
                data = None

                while retry_count <= max_retries:
                    if retry_count > 0:
                        self.log(f"[🚄 {query.from_city}→{query.to_city}] 第{retry_count}次重试...")

                    data = self.mcp_manager.call_tool(
                        "train_get-tickets",
                        {
                            "date": use_date,
                            "fromStation": from_station,
                            "toStation": to_station
                        }
                    )

                    # 检查返回的数据是否有效
                    if self._is_valid_response(data):
                        result.success = True
                        result.data = data
                        if retry_count > 0:
                            self.log(f"[🚄 {query.from_city}→{query.to_city}] ✅ 重试成功")
                        break
                    else:
                        # 查询失败或超时
                        if retry_count < max_retries:
                            self.log(f"[🚄 {query.from_city}→{query.to_city}] ⚠️ 查询失败，将重试...")
                            retry_count += 1
                            continue
                        else:
                            result.success = False
                            result.data = data
                            result.error = "查询失败或超时（已重试2次）"
                            self.log(f"[🚄 {query.from_city}→{query.to_city}] ❌ 重试{max_retries}次后仍失败")
                            break

        except Exception as e:
            result.error = str(e)

        finally:
            result.query_time = (datetime.now() - start_time).total_seconds()

        return result

    def build_segment_queries(
        self,
        origin: str,
        destination: str,
        date: str,
        hub_cities: List[str],
        include_direct: bool = True,
        transport_filter: str = "all"  # "all", "flight", "train"
    ) -> List[SegmentQuery]:
        """
        构建所有需要查询的分段请求

        Args:
            origin: 出发城市
            destination: 目的城市
            date: 出发日期
            hub_cities: 中转枢纽城市列表
            include_direct: 是否包含直达查询
            transport_filter: 交通方式过滤

        Returns:
            所有分段查询请求列表
        """
        queries = []

        def get_available_modes(from_city: str, to_city: str) -> List[TransportMode]:
            """
            根据出发地和目的地确定可用的交通方式

            规则：
            - 如果任一端是国际城市，只能查机票
            - 如果两端都是国内城市，可以查机票和火车票
            """
            available = []

            # 机票：只要用户没限制只查火车票，就可以查
            if transport_filter in ["all", "flight"]:
                available.append(TransportMode.FLIGHT)

            # 火车票：只有两端都是国内城市才能查
            if transport_filter in ["all", "train"]:
                from_is_intl = is_international_city(from_city)
                to_is_intl = is_international_city(to_city)
                if not from_is_intl and not to_is_intl:
                    available.append(TransportMode.TRAIN)

            return available

        # 1. 直达查询
        if include_direct:
            direct_modes = get_available_modes(origin, destination)
            for mode in direct_modes:
                queries.append(SegmentQuery(
                    from_city=origin,
                    to_city=destination,
                    date=date,
                    mode=mode,
                    segment_id=f"direct_{mode.value}"
                ))

        # 2. 中转查询 - 每个中转城市生成多个分段
        for hub in hub_cities:
            if hub == origin or hub == destination:
                continue

            # 第一程：出发地 → 中转城市
            # 例如：曼谷→北京，曼谷是国际城市，只能查机票
            leg1_modes = get_available_modes(origin, hub)
            for mode in leg1_modes:
                queries.append(SegmentQuery(
                    from_city=origin,
                    to_city=hub,
                    date=date,
                    mode=mode,
                    segment_id=f"leg1_{hub}_{mode.value}"
                ))

            # 第二程：中转城市 → 目的地
            # 例如：北京→长治，都是国内城市，可以查机票和火车票
            leg2_modes = get_available_modes(hub, destination)
            for mode in leg2_modes:
                queries.append(SegmentQuery(
                    from_city=hub,
                    to_city=destination,
                    date=date,
                    mode=mode,
                    segment_id=f"leg2_{hub}_{mode.value}"
                ))

        return queries

    def execute_parallel_queries(
        self,
        queries: List[SegmentQuery],
        train_date: str = None,
        max_workers: int = 15
    ) -> Dict[str, SegmentResult]:
        """
        执行所有分段查询（火车票并行，机票串行）

        策略说明：
        - 火车票查询：并行执行（12306 无严格反爬限制）
        - 机票查询：串行执行（携程反爬严格，避免并发冲突和验证码问题）

        Args:
            queries: 查询请求列表
            train_date: 火车票查询日期
            max_workers: 火车票最大并行线程数

        Returns:
            segment_id -> SegmentResult 的映射
        """
        self._segment_results.clear()

        # 分离机票和火车票查询
        flight_queries = [q for q in queries if q.mode == TransportMode.FLIGHT]
        train_queries = [q for q in queries if q.mode == TransportMode.TRAIN]

        total = len(queries)
        completed = [0]

        self.log(f"[查询引擎] 共 {total} 个查询任务（✈️机票 {len(flight_queries)} 个串行，🚄火车票 {len(train_queries)} 个并行）")

        def update_progress(query: SegmentQuery, result: SegmentResult):
            """更新进度"""
            with self._results_lock:
                completed[0] += 1
                self._segment_results[result.segment_id] = result

            mode_icon = "✈️" if query.mode == TransportMode.FLIGHT else "🚄"
            status = "✅" if result.success else "❌"
            self.log(f"[{mode_icon} {query.from_city}→{query.to_city}] {status} ({result.query_time:.1f}s)")
            self.progress_callback(completed[0], total, f"{query.from_city}→{query.to_city}")

        # 第一阶段：并行执行火车票查询
        if train_queries:
            self.log(f"[查询引擎] 🚄 开始并行查询 {len(train_queries)} 个火车票...")

            def train_worker(query: SegmentQuery) -> SegmentResult:
                self.log(f"[🚄 {query.from_city}→{query.to_city}] 开始查询...")
                result = self.query_single_segment(query, train_date)
                update_progress(query, result)
                return result

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(train_worker, q): q for q in train_queries}
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        query = futures[future]
                        self.log(f"[查询引擎] {query.segment_id} 异常: {e}")

        # 第二阶段：串行执行机票查询
        if flight_queries:
            self.log(f"[查询引擎] ✈️ 开始串行查询 {len(flight_queries)} 个机票（避免验证码冲突）...")

            for i, query in enumerate(flight_queries, 1):
                self.log(f"[✈️ {query.from_city}→{query.to_city}] 开始查询 ({i}/{len(flight_queries)})...")
                try:
                    result = self.query_single_segment(query, train_date)
                    update_progress(query, result)
                except Exception as e:
                    self.log(f"[查询引擎] {query.segment_id} 异常: {e}")
                    # 创建失败结果
                    result = SegmentResult(
                        segment_id=query.segment_id,
                        from_city=query.from_city,
                        to_city=query.to_city,
                        mode=query.mode,
                        success=False,
                        error=str(e)
                    )
                    update_progress(query, result)

        self.log(f"[查询引擎] 所有查询完成，成功 {sum(1 for r in self._segment_results.values() if r.success)}/{total}")

        return self._segment_results.copy()

    def combine_routes(
        self,
        origin: str,
        destination: str,
        hub_cities: List[str],
        results: Dict[str, SegmentResult]
    ) -> List[RouteOption]:
        """
        组合所有可能的路线

        Args:
            origin: 出发城市
            destination: 目的城市
            hub_cities: 中转城市列表
            results: 查询结果

        Returns:
            所有可能的路线组合
        """
        routes = []

        # 1. 直达路线
        for mode in [TransportMode.FLIGHT, TransportMode.TRAIN]:
            segment_id = f"direct_{mode.value}"
            if segment_id in results and results[segment_id].success:
                mode_icon = "✈️" if mode == TransportMode.FLIGHT else "🚄"
                routes.append(RouteOption(
                    segments=[results[segment_id]],
                    total_legs=1,
                    description=f"{origin} {mode_icon}→ {destination} (直达)"
                ))

        # 2. 单中转路线（2段）
        for hub in hub_cities:
            if hub == origin or hub == destination:
                continue

            # 所有可能的模式组合
            mode_combinations = [
                (TransportMode.FLIGHT, TransportMode.FLIGHT),  # 飞机 + 飞机
                (TransportMode.FLIGHT, TransportMode.TRAIN),   # 飞机 + 高铁
                (TransportMode.TRAIN, TransportMode.FLIGHT),   # 高铁 + 飞机
                (TransportMode.TRAIN, TransportMode.TRAIN),    # 高铁 + 高铁
            ]

            for mode1, mode2 in mode_combinations:
                leg1_id = f"leg1_{hub}_{mode1.value}"
                leg2_id = f"leg2_{hub}_{mode2.value}"

                leg1 = results.get(leg1_id)
                leg2 = results.get(leg2_id)

                # 两段都查询成功才组成有效路线
                if leg1 and leg2 and leg1.success and leg2.success:
                    icon1 = "✈️" if mode1 == TransportMode.FLIGHT else "🚄"
                    icon2 = "✈️" if mode2 == TransportMode.FLIGHT else "🚄"

                    routes.append(RouteOption(
                        segments=[leg1, leg2],
                        total_legs=2,
                        description=f"{origin} {icon1}→ {hub} {icon2}→ {destination}"
                    ))

        return routes

    def build_summary_for_ai(
        self,
        origin: str,
        destination: str,
        date: str,
        routes: List[RouteOption],
        results: Dict[str, SegmentResult],
        hub_cities: List[str] = None
    ) -> str:
        """
        构建给 AI 分析的汇总消息（使用程序计算结果）

        新版本：程序完成所有价格/时长计算，AI只负责自然语言描述

        Args:
            origin: 出发城市
            destination: 目的城市
            date: 出发日期
            routes: 所有可能的路线（旧版兼容）
            results: 原始查询结果
            hub_cities: 中转城市列表

        Returns:
            格式化的汇总消息（包含程序计算结果）
        """
        # 将 SegmentResult 转换为计算引擎需要的格式
        segment_data = {}
        for seg_id, seg_result in results.items():
            if seg_result.success and seg_result.data:
                transport_type = "flight" if seg_result.mode == TransportMode.FLIGHT else "train"
                segment_data[seg_id] = (transport_type, seg_result.data)

        # 使用程序计算所有可行路线
        if hub_cities is None:
            hub_cities = []

        self.log("[计算引擎] 开始计算所有可行路线组合...")

        calculated_routes = self._route_calculator.calculate_all_routes(
            origin=origin,
            destination=destination,
            date=date,
            segment_data=segment_data,
            hub_cities=hub_cities
        )

        self.log(f"[计算引擎] 计算完成，共 {len(calculated_routes)} 个可行方案")

        # 使用计算引擎格式化输出
        return self._route_calculator.format_routes_for_ai(
            routes=calculated_routes,
            origin=origin,
            destination=destination,
            date=date,
            top_n=30
        )

    def build_summary_for_ai_legacy(
        self,
        origin: str,
        destination: str,
        date: str,
        routes: List[RouteOption],
        results: Dict[str, SegmentResult]
    ) -> str:
        """
        构建给 AI 分析的汇总消息（旧版本，保留用于调试对比）

        这是原始版本，把所有原始数据扔给AI进行计算
        """
        lines = [
            f"# {date} 从 {origin} 到 {destination} 的出行方案查询结果",
            "",
            f"共查询到 {len(routes)} 条可行路线，请分析并推荐最优方案。",
            "",
            "=" * 60,
        ]

        # 按段数分组
        direct_routes = [r for r in routes if r.total_legs == 1]
        transfer_routes = [r for r in routes if r.total_legs > 1]

        # 直达方案
        if direct_routes:
            lines.append("")
            lines.append("## 一、直达方案")
            lines.append("")
            for route in direct_routes:
                seg = route.segments[0]
                mode_name = "机票" if seg.mode == TransportMode.FLIGHT else "火车票"
                lines.append(f"### {route.description}")
                lines.append(f"**交通方式**: {mode_name}")
                lines.append(f"**查询结果**:")
                lines.append("```")
                lines.append(seg.data[:3000] if seg.data else "无数据")
                lines.append("```")
                lines.append("")

        # 中转方案（按中转城市分组）
        if transfer_routes:
            lines.append("")
            lines.append("## 二、中转方案")
            lines.append("")

            # 按中转城市分组
            hub_groups: Dict[str, List[RouteOption]] = {}
            for route in transfer_routes:
                # 从第一段的目的地获取中转城市
                hub = route.segments[0].to_city
                if hub not in hub_groups:
                    hub_groups[hub] = []
                hub_groups[hub].append(route)

            for hub, hub_routes in hub_groups.items():
                lines.append(f"### 经 {hub} 中转")
                lines.append("")

                for route in hub_routes:
                    lines.append(f"#### {route.description}")

                    for i, seg in enumerate(route.segments):
                        mode_name = "机票" if seg.mode == TransportMode.FLIGHT else "火车票"
                        leg_num = "第一程" if i == 0 else "第二程"
                        lines.append(f"**{leg_num}** ({seg.from_city}→{seg.to_city}, {mode_name}):")
                        lines.append("```")
                        # 限制每段数据长度
                        lines.append(seg.data[:1500] if seg.data else "无数据")
                        lines.append("```")
                    lines.append("")

        # 添加分析要求
        lines.append("")
        lines.append("=" * 60)
        lines.append("")
        lines.append("## 分析要求")
        lines.append("")
        lines.append("请根据以上数据，推荐最优的 3 个出行方案：")
        lines.append("1. **性价比最高** - 综合考虑价格和时间")
        lines.append("2. **时间最短** - 总耗时最少的方案")
        lines.append("3. **价格最低** - 最便宜的方案")
        lines.append("")
        lines.append("对于每个推荐方案，请说明：")
        lines.append("- 具体行程安排（航班号/车次、出发到达时间）")
        lines.append("- 总价格估算")
        lines.append("- 总耗时（包括中转等待时间）")
        lines.append("- 推荐理由")
        lines.append("")
        lines.append("**注意**：")
        lines.append("- 中转方案需要考虑换乘衔接时间（建议预留 2-3 小时）")
        lines.append("- 如果某些查询结果为空或报错，请忽略该方案")
        lines.append("- 火车票数据可能受12306的15天查询限制，实际购票请以官方为准")

        return "\n".join(lines)


def calculate_adjusted_train_date(query_date: str) -> str:
    """
    计算调整后的火车票查询日期（处理12306的15天限制）

    Args:
        query_date: 用户请求的日期

    Returns:
        调整后的查询日期
    """
    today = datetime.now()
    max_date = today + timedelta(days=14)

    try:
        target_date = datetime.strptime(query_date, "%Y-%m-%d")
        if target_date > max_date:
            return max_date.strftime("%Y-%m-%d")
    except:
        pass

    return query_date
