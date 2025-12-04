# -*- coding: utf-8 -*-
"""
路线计算引擎
负责根据原始航班/火车数据，计算所有可行的出行方案

核心功能：
1. 解析原始数据，提取结构化的航班/火车信息
2. 计算14种场景的所有可行组合
3. 按价格/时长排序，输出计算好的结果给AI

场景列表（14种）：
- 直达（2种）：直达航班、直达火车
- 两段中转（4种）：飞机→飞机、飞机→火车、火车→飞机、火车→火车
- 三段中转（8种）：所有3段组合
"""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class TransportType(Enum):
    """交通类型"""
    FLIGHT = "flight"
    TRAIN = "train"


@dataclass
class TransportSegment:
    """一段交通的结构化信息"""
    transport_type: TransportType
    # 基本信息
    carrier: str  # 航空公司/铁路局
    number: str  # 航班号/车次（如 CX337/CX872 或 G1234）
    # 时间信息
    departure_time: str  # 出发时间 HH:MM
    arrival_time: str  # 到达时间 HH:MM
    # 以下是有默认值的字段
    number_list: List[str] = field(default_factory=list)  # 中转航班的航班号列表
    duration_minutes: int = 0  # 总时长（分钟）
    cross_days: int = 0  # 跨天数（0表示当天到达）
    # 地点信息
    departure_city: str = ""
    departure_station: str = ""  # 机场/火车站名
    arrival_city: str = ""
    arrival_station: str = ""
    # 价格信息
    price: int = 0  # 价格（元）
    # 航班特有信息
    flight_type: str = ""  # 直达/中转（航班本身的经停信息）
    transfer_city: str = ""  # 经停城市（航班本身的经停）
    transfer_wait: str = ""  # 经停等待时间
    # 火车特有信息
    train_type: str = ""  # G/D/C/K 等
    seat_types: Dict[str, int] = field(default_factory=dict)  # 座位类型及价格
    # 原始数据
    raw_data: Dict = field(default_factory=dict)

    def get_departure_datetime(self, base_date: str) -> datetime:
        """获取出发日期时间"""
        return datetime.strptime(f"{base_date} {self.departure_time}", "%Y-%m-%d %H:%M")

    def get_arrival_datetime(self, base_date: str) -> datetime:
        """获取到达日期时间（考虑跨天）"""
        dt = datetime.strptime(f"{base_date} {self.arrival_time}", "%Y-%m-%d %H:%M")
        return dt + timedelta(days=self.cross_days)


@dataclass
class RoutePlan:
    """一个完整的出行方案"""
    segments: List[TransportSegment]  # 各段交通
    transfer_cities: List[str]  # 中转城市列表
    min_transfer_hours: int  # 使用的最小换乘时间（2或3小时）
    # 计算结果
    total_price: int = 0  # 总价格
    total_duration_minutes: int = 0  # 总时长（分钟）
    accommodation_fee: int = 0  # 住宿费
    transfer_wait_minutes: List[int] = field(default_factory=list)  # 各中转等待时间
    # 分类标签
    route_type: str = ""  # 如 "flight_direct", "flight_train", "train_flight_train" 等
    feasible: bool = True  # 是否可行
    infeasible_reason: str = ""  # 不可行原因

    def get_description(self) -> str:
        """生成路线描述"""
        parts = []
        for i, seg in enumerate(self.segments):
            if i == 0:
                parts.append(seg.departure_city)
            icon = "✈️" if seg.transport_type == TransportType.FLIGHT else "🚄"
            parts.append(f"→{icon}→")
            parts.append(seg.arrival_city)
        return "".join(parts)

    def get_type_description(self) -> str:
        """获取类型描述"""
        types = [seg.transport_type.value for seg in self.segments]
        if len(types) == 1:
            return "直达航班" if types[0] == "flight" else "直达火车"
        type_names = {"flight": "飞机", "train": "火车"}
        return " → ".join([type_names[t] for t in types])


class RouteCalculator:
    """
    路线计算引擎

    负责：
    1. 解析原始MCP返回的数据
    2. 计算所有可行的路线组合
    3. 排序和筛选结果
    """

    # 住宿费相关配置
    DEFAULT_ACCOMMODATION_FEE = 200  # 默认住宿费
    NIGHT_START_HOUR = 22  # 夜间开始时间
    NIGHT_END_HOUR = 6  # 夜间结束时间
    LONG_WAIT_THRESHOLD_HOURS = 12  # 超长等待阈值（无论何时都需要住宿）

    def __init__(
        self,
        accommodation_threshold_hours: int = 6,
        accommodation_enabled: bool = True
    ):
        """
        初始化计算引擎

        Args:
            accommodation_threshold_hours: 触发住宿费的等待小时数阈值
            accommodation_enabled: 是否启用住宿费计算
        """
        self.accommodation_threshold_hours = accommodation_threshold_hours
        self.accommodation_enabled = accommodation_enabled

    # ==================== 数据解析 ====================

    def parse_flight_data(self, raw_data: str, departure_city: str, arrival_city: str) -> List[TransportSegment]:
        """
        解析航班原始数据

        Args:
            raw_data: MCP返回的原始JSON字符串
            departure_city: 出发城市
            arrival_city: 到达城市

        Returns:
            解析后的航班列表
        """
        segments = []
        if not raw_data:
            return segments

        try:
            # 尝试解析JSON
            data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data

            # 处理不同的数据格式
            flights = []
            if isinstance(data, dict):
                if "flights" in data:
                    flights = data["flights"]
                elif "data" in data:
                    flights = data["data"] if isinstance(data["data"], list) else []
                elif "航班" in str(data):
                    # 可能是直接的航班列表
                    flights = [data] if "航班号" in data else []
            elif isinstance(data, list):
                flights = data

            for flight in flights:
                seg = self._parse_single_flight(flight, departure_city, arrival_city)
                if seg:
                    segments.append(seg)

        except json.JSONDecodeError:
            # 尝试用正则提取信息
            segments = self._parse_flight_from_text(raw_data, departure_city, arrival_city)
        except Exception as e:
            print(f"解析航班数据出错: {e}")

        return segments

    def _parse_single_flight(self, flight: Dict, departure_city: str, arrival_city: str) -> Optional[TransportSegment]:
        """解析单个航班数据"""
        try:
            # 提取航班号
            flight_no = flight.get("航班号", flight.get("flight_no", ""))
            if not flight_no:
                return None

            # 提取价格
            price = 0
            price_str = flight.get("价格", flight.get("price", "0"))
            if isinstance(price_str, str):
                price_match = re.search(r'(\d+)', price_str.replace(",", ""))
                if price_match:
                    price = int(price_match.group(1))
            else:
                price = int(price_str) if price_str else 0

            # 提取时间
            dep_time = flight.get("出发时间", flight.get("departure_time", ""))
            arr_time = flight.get("到达时间", flight.get("arrival_time", ""))

            # 清理时间格式
            dep_time = self._clean_time(dep_time)
            arr_time = self._clean_time(arr_time)

            # 提取跨天信息
            cross_days = flight.get("跨天", 0)
            if not cross_days:
                arr_time_raw = flight.get("到达时间", "")
                if "+1" in str(arr_time_raw):
                    cross_days = 1
                elif "+2" in str(arr_time_raw):
                    cross_days = 2

            # 提取时长
            duration_minutes = flight.get("总时长分钟", 0)
            if not duration_minutes:
                duration_str = flight.get("总时长", "")
                duration_minutes = self._parse_duration(duration_str)

            # 提取航班类型
            flight_type = flight.get("航班类型", "直达")
            transfer_city = flight.get("中转城市", "")
            transfer_wait = flight.get("中转等待", "")

            # 航班号列表
            number_list = flight.get("航班号列表", [])
            if not number_list and "/" in flight_no:
                number_list = flight_no.split("/")

            return TransportSegment(
                transport_type=TransportType.FLIGHT,
                carrier=flight.get("航空公司", flight.get("airline", "")),
                number=flight_no,
                number_list=number_list,
                departure_time=dep_time,
                arrival_time=arr_time,
                duration_minutes=duration_minutes,
                cross_days=cross_days,
                departure_city=departure_city,
                departure_station=flight.get("出发机场", flight.get("departure_airport", "")),
                arrival_city=arrival_city,
                arrival_station=flight.get("到达机场", flight.get("arrival_airport", "")),
                price=price,
                flight_type=flight_type,
                transfer_city=transfer_city,
                transfer_wait=transfer_wait,
                raw_data=flight
            )
        except Exception as e:
            print(f"解析单个航班出错: {e}")
            return None

    def _parse_flight_from_text(self, text: str, departure_city: str, arrival_city: str) -> List[TransportSegment]:
        """从文本中提取航班信息（备用方案）"""
        segments = []
        # 简单的正则匹配
        # 匹配类似: CA1234 08:00-11:00 ¥1000
        pattern = r'([A-Z]{2}\d{3,4})\s+(\d{1,2}:\d{2})[^\d]*(\d{1,2}:\d{2})[^\d¥]*[¥￥]?(\d+)'
        matches = re.findall(pattern, text)
        for match in matches:
            flight_no, dep_time, arr_time, price = match
            segments.append(TransportSegment(
                transport_type=TransportType.FLIGHT,
                carrier="",
                number=flight_no,
                departure_time=dep_time,
                arrival_time=arr_time,
                departure_city=departure_city,
                arrival_city=arrival_city,
                price=int(price),
                flight_type="直达"
            ))
        return segments

    def parse_train_data(self, raw_data: str, departure_city: str, arrival_city: str) -> List[TransportSegment]:
        """
        解析火车票原始数据

        Args:
            raw_data: MCP返回的原始JSON字符串
            departure_city: 出发城市
            arrival_city: 到达城市

        Returns:
            解析后的火车票列表
        """
        segments = []
        if not raw_data:
            return segments

        try:
            data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data

            # 处理不同格式
            trains = []
            if isinstance(data, dict):
                if "trains" in data:
                    trains = data["trains"]
                elif "data" in data:
                    trains = data["data"] if isinstance(data["data"], list) else []
                elif "车次" in str(data):
                    trains = [data]
            elif isinstance(data, list):
                trains = data

            for train in trains:
                seg = self._parse_single_train(train, departure_city, arrival_city)
                if seg:
                    segments.append(seg)

        except json.JSONDecodeError:
            segments = self._parse_train_from_text(raw_data, departure_city, arrival_city)
        except Exception as e:
            print(f"解析火车数据出错: {e}")

        return segments

    def _parse_single_train(self, train: Dict, departure_city: str, arrival_city: str) -> Optional[TransportSegment]:
        """解析单个火车数据"""
        try:
            # 提取车次
            train_no = train.get("车次", train.get("train_no", train.get("trainNo", "")))
            if not train_no:
                return None

            # 提取时间
            dep_time = train.get("出发时间", train.get("departure_time", train.get("startTime", "")))
            arr_time = train.get("到达时间", train.get("arrival_time", train.get("arriveTime", "")))
            dep_time = self._clean_time(dep_time)
            arr_time = self._clean_time(arr_time)

            # 提取时长
            duration_str = train.get("历时", train.get("duration", train.get("runTime", "")))
            duration_minutes = self._parse_duration(duration_str)

            # 跨天处理
            cross_days = 0
            day_diff = train.get("跨天", train.get("dayDiff", 0))
            if day_diff:
                cross_days = int(day_diff) if isinstance(day_diff, (int, str)) else 0

            # 提取价格（取最低价或二等座价格）
            price = 0
            seat_types = {}

            # 尝试多种价格字段
            price_fields = [
                ("二等座", "secondSeat"),
                ("一等座", "firstSeat"),
                ("硬座", "hardSeat"),
                ("软座", "softSeat"),
                ("硬卧", "hardSleeper"),
                ("软卧", "softSleeper"),
                ("商务座", "businessSeat"),
                ("无座", "noSeat"),
            ]

            for cn_name, en_name in price_fields:
                p = train.get(cn_name, train.get(en_name, ""))
                if p and p != "--" and p != "无":
                    try:
                        p_val = int(re.search(r'(\d+)', str(p).replace(",", "")).group(1))
                        seat_types[cn_name] = p_val
                        if price == 0 or p_val < price:
                            price = p_val
                    except:
                        pass

            # 如果没找到价格，尝试通用价格字段
            if price == 0:
                price_str = train.get("价格", train.get("price", "0"))
                if isinstance(price_str, str):
                    match = re.search(r'(\d+)', price_str.replace(",", ""))
                    if match:
                        price = int(match.group(1))
                elif isinstance(price_str, (int, float)):
                    price = int(price_str)

            # 判断火车类型
            train_type = ""
            if train_no:
                first_char = train_no[0].upper()
                if first_char == "G":
                    train_type = "高铁"
                elif first_char == "D":
                    train_type = "动车"
                elif first_char == "C":
                    train_type = "城际"
                elif first_char == "K":
                    train_type = "快速"
                elif first_char == "T":
                    train_type = "特快"
                elif first_char == "Z":
                    train_type = "直达"

            return TransportSegment(
                transport_type=TransportType.TRAIN,
                carrier=train_type,
                number=train_no,
                departure_time=dep_time,
                arrival_time=arr_time,
                duration_minutes=duration_minutes,
                cross_days=cross_days,
                departure_city=departure_city,
                departure_station=train.get("出发站", train.get("fromStation", "")),
                arrival_city=arrival_city,
                arrival_station=train.get("到达站", train.get("toStation", "")),
                price=price,
                train_type=train_type,
                seat_types=seat_types,
                raw_data=train
            )
        except Exception as e:
            print(f"解析单个火车出错: {e}")
            return None

    def _parse_train_from_text(self, text: str, departure_city: str, arrival_city: str) -> List[TransportSegment]:
        """从文本中提取火车信息（备用方案）"""
        segments = []
        # 匹配类似: G1234 08:00-11:00 ¥500
        pattern = r'([GDCKTZ]\d{1,4})\s+(\d{1,2}:\d{2})[^\d]*(\d{1,2}:\d{2})[^\d¥]*[¥￥]?(\d+)'
        matches = re.findall(pattern, text)
        for match in matches:
            train_no, dep_time, arr_time, price = match
            segments.append(TransportSegment(
                transport_type=TransportType.TRAIN,
                carrier="",
                number=train_no,
                departure_time=dep_time,
                arrival_time=arr_time,
                departure_city=departure_city,
                arrival_city=arrival_city,
                price=int(price)
            ))
        return segments

    def _clean_time(self, time_str: str) -> str:
        """清理时间字符串，提取 HH:MM 格式"""
        if not time_str:
            return ""
        # 移除跨天标记
        time_str = re.sub(r'\+\d+天?', '', str(time_str)).strip()
        # 提取时间
        match = re.search(r'(\d{1,2}):(\d{2})', time_str)
        if match:
            return f"{int(match.group(1)):02d}:{match.group(2)}"
        return time_str

    def _parse_duration(self, duration_str: str) -> int:
        """解析时长字符串，返回分钟数"""
        if not duration_str:
            return 0
        total_minutes = 0
        # 匹配小时
        hour_match = re.search(r'(\d+)\s*[小时hH]', str(duration_str))
        if hour_match:
            total_minutes += int(hour_match.group(1)) * 60
        # 匹配分钟
        min_match = re.search(r'(\d+)\s*[分钟mM]', str(duration_str))
        if min_match:
            total_minutes += int(min_match.group(1))
        return total_minutes

    # ==================== 路线计算 ====================

    def calculate_all_routes(
        self,
        origin: str,
        destination: str,
        date: str,
        segment_data: Dict[str, Tuple[str, str]],  # segment_id -> (transport_type, raw_data)
        hub_cities: List[str]
    ) -> List[RoutePlan]:
        """
        计算所有可行的路线方案

        Args:
            origin: 出发城市
            destination: 目的城市
            date: 出发日期
            segment_data: 各段查询结果 {segment_id: (transport_type, raw_data)}
            hub_cities: 中转城市列表

        Returns:
            所有可行的路线方案列表
        """
        all_routes = []

        # 1. 解析所有原始数据为结构化数据
        parsed_segments = self._parse_all_segments(segment_data, origin, destination, hub_cities)

        # 2. 计算直达方案
        direct_routes = self._calculate_direct_routes(parsed_segments, origin, destination, date)
        all_routes.extend(direct_routes)

        # 3. 计算两段中转方案（2小时和3小时两种版本）
        for min_transfer_hours in [2, 3]:
            two_leg_routes = self._calculate_two_leg_routes(
                parsed_segments, origin, destination, hub_cities, date, min_transfer_hours
            )
            all_routes.extend(two_leg_routes)

        # 4. 计算三段中转方案（2小时和3小时两种版本）
        for min_transfer_hours in [2, 3]:
            three_leg_routes = self._calculate_three_leg_routes(
                parsed_segments, origin, destination, hub_cities, date, min_transfer_hours
            )
            all_routes.extend(three_leg_routes)

        # 5. 过滤不可行方案，排序
        feasible_routes = [r for r in all_routes if r.feasible]
        feasible_routes.sort(key=lambda r: (r.total_price, r.total_duration_minutes))

        return feasible_routes

    def _parse_all_segments(
        self,
        segment_data: Dict[str, Tuple[str, str]],
        origin: str,
        destination: str,
        hub_cities: List[str]
    ) -> Dict[str, List[TransportSegment]]:
        """
        解析所有段的原始数据

        Returns:
            {segment_key: [TransportSegment, ...]}
            segment_key 格式: "from_to_type" 如 "北京_上海_flight"
        """
        parsed = {}

        for segment_id, (transport_type, raw_data) in segment_data.items():
            # 从 segment_id 解析出发地和目的地
            # segment_id 格式可能是: "origin_to_hub1_flight" 或类似
            parts = segment_id.split("_")

            # 确定出发地和目的地
            from_city, to_city = self._extract_cities_from_segment_id(
                segment_id, origin, destination, hub_cities
            )

            if not from_city or not to_city:
                continue

            key = f"{from_city}_{to_city}_{transport_type}"

            if transport_type == "flight":
                segments = self.parse_flight_data(raw_data, from_city, to_city)
            else:
                segments = self.parse_train_data(raw_data, from_city, to_city)

            if key not in parsed:
                parsed[key] = []
            parsed[key].extend(segments)

        return parsed

    def _extract_cities_from_segment_id(
        self,
        segment_id: str,
        origin: str,
        destination: str,
        hub_cities: List[str]
    ) -> Tuple[str, str]:
        """
        从 segment_id 提取出发城市和到达城市

        segment_id 格式:
        - "direct_{mode}" - 直达 (origin → destination)
        - "leg1_{hub}_{mode}" - 第一程 (origin → hub)
        - "leg2_{hub}_{mode}" - 第二程 (hub → destination)
        - "{from_city}_{to_city}_{mode}" - 通用格式
        """
        parts = segment_id.split("_")

        # 格式1: direct_{mode}
        if parts[0] == "direct":
            return origin, destination

        # 格式2: leg1_{hub}_{mode}
        if parts[0] == "leg1" and len(parts) >= 3:
            hub = parts[1]
            # 在 hub_cities 中查找匹配的城市
            for city in hub_cities:
                if city == hub or city.lower() == hub.lower():
                    return origin, city
            # 如果没找到，直接用 hub 作为城市名
            return origin, hub

        # 格式3: leg2_{hub}_{mode}
        if parts[0] == "leg2" and len(parts) >= 3:
            hub = parts[1]
            for city in hub_cities:
                if city == hub or city.lower() == hub.lower():
                    return city, destination
            return hub, destination

        # 格式4: {from_city}_{to_city}_{mode} - 通用格式
        if len(parts) >= 3:
            # 最后一部分是 mode (flight/train)
            mode = parts[-1]
            if mode in ["flight", "train"]:
                # 中间部分是城市名（可能包含下划线）
                city_parts = parts[:-1]
                # 尝试找到分隔点
                for i in range(1, len(city_parts)):
                    from_city = "_".join(city_parts[:i])
                    to_city = "_".join(city_parts[i:])
                    # 检查是否匹配已知城市
                    all_cities = [origin, destination] + hub_cities
                    from_match = any(c == from_city or c in from_city or from_city in c for c in all_cities)
                    to_match = any(c == to_city or c in to_city or to_city in c for c in all_cities)
                    if from_match and to_match:
                        # 标准化城市名
                        for c in all_cities:
                            if c == from_city or c in from_city or from_city in c:
                                from_city = c
                                break
                        for c in all_cities:
                            if c == to_city or c in to_city or to_city in c:
                                to_city = c
                                break
                        return from_city, to_city

        return "", ""

    def _calculate_direct_routes(
        self,
        parsed_segments: Dict[str, List[TransportSegment]],
        origin: str,
        destination: str,
        date: str
    ) -> List[RoutePlan]:
        """计算直达方案"""
        routes = []

        for transport_type in ["flight", "train"]:
            key = f"{origin}_{destination}_{transport_type}"
            segments = parsed_segments.get(key, [])

            for seg in segments:
                if seg.price <= 0:
                    continue

                route = RoutePlan(
                    segments=[seg],
                    transfer_cities=[],
                    min_transfer_hours=0,
                    total_price=seg.price,
                    total_duration_minutes=seg.duration_minutes,
                    route_type=f"{transport_type}_direct",
                    feasible=True
                )
                routes.append(route)

        return routes

    def _calculate_two_leg_routes(
        self,
        parsed_segments: Dict[str, List[TransportSegment]],
        origin: str,
        destination: str,
        hub_cities: List[str],
        date: str,
        min_transfer_hours: int
    ) -> List[RoutePlan]:
        """
        计算两段中转方案

        4种组合：
        - flight -> flight
        - flight -> train
        - train -> flight
        - train -> train
        """
        routes = []
        transport_combos = [
            ("flight", "flight"),
            ("flight", "train"),
            ("train", "flight"),
            ("train", "train"),
        ]

        for hub in hub_cities:
            for type1, type2 in transport_combos:
                key1 = f"{origin}_{hub}_{type1}"
                key2 = f"{hub}_{destination}_{type2}"

                segments1 = parsed_segments.get(key1, [])
                segments2 = parsed_segments.get(key2, [])

                # 对每个第一段，找可行的第二段
                for seg1 in segments1:
                    if seg1.price <= 0:
                        continue

                    for seg2 in segments2:
                        if seg2.price <= 0:
                            continue

                        # 检查换乘可行性
                        feasible, wait_minutes, reason = self._check_transfer_feasibility(
                            seg1, seg2, date, min_transfer_hours
                        )

                        # 计算住宿费
                        accommodation = 0
                        if feasible and self.accommodation_enabled:
                            accommodation = self._calculate_accommodation_fee(
                                seg1, seg2, date, wait_minutes
                            )

                        total_price = seg1.price + seg2.price + accommodation
                        total_duration = seg1.duration_minutes + wait_minutes + seg2.duration_minutes

                        route = RoutePlan(
                            segments=[seg1, seg2],
                            transfer_cities=[hub],
                            min_transfer_hours=min_transfer_hours,
                            total_price=total_price,
                            total_duration_minutes=total_duration,
                            accommodation_fee=accommodation,
                            transfer_wait_minutes=[wait_minutes],
                            route_type=f"{type1}_{type2}",
                            feasible=feasible,
                            infeasible_reason=reason
                        )
                        routes.append(route)

        return routes

    def _calculate_three_leg_routes(
        self,
        parsed_segments: Dict[str, List[TransportSegment]],
        origin: str,
        destination: str,
        hub_cities: List[str],
        date: str,
        min_transfer_hours: int
    ) -> List[RoutePlan]:
        """
        计算三段中转方案

        8种组合
        """
        routes = []
        transport_types = ["flight", "train"]

        # 生成所有3段组合
        combos = []
        for t1 in transport_types:
            for t2 in transport_types:
                for t3 in transport_types:
                    combos.append((t1, t2, t3))

        # 需要两个中转城市
        if len(hub_cities) < 2:
            return routes

        # 遍历所有两两中转城市组合
        for i, hub1 in enumerate(hub_cities):
            for hub2 in hub_cities:
                if hub1 == hub2:
                    continue

                for type1, type2, type3 in combos:
                    key1 = f"{origin}_{hub1}_{type1}"
                    key2 = f"{hub1}_{hub2}_{type2}"
                    key3 = f"{hub2}_{destination}_{type3}"

                    segments1 = parsed_segments.get(key1, [])
                    segments2 = parsed_segments.get(key2, [])
                    segments3 = parsed_segments.get(key3, [])

                    # 限制每段只取前3个选项，避免组合爆炸
                    for seg1 in segments1[:3]:
                        if seg1.price <= 0:
                            continue

                        for seg2 in segments2[:3]:
                            if seg2.price <= 0:
                                continue

                            # 检查第一次换乘
                            feasible1, wait1, reason1 = self._check_transfer_feasibility(
                                seg1, seg2, date, min_transfer_hours
                            )
                            if not feasible1:
                                continue

                            for seg3 in segments3[:3]:
                                if seg3.price <= 0:
                                    continue

                                # 计算seg2到达日期（考虑跨天）
                                seg2_date = self._get_arrival_date(seg1, seg2, date, wait1)

                                # 检查第二次换乘
                                feasible2, wait2, reason2 = self._check_transfer_feasibility(
                                    seg2, seg3, seg2_date, min_transfer_hours
                                )

                                feasible = feasible1 and feasible2
                                reason = reason1 or reason2

                                # 计算住宿费
                                accommodation = 0
                                if feasible and self.accommodation_enabled:
                                    acc1 = self._calculate_accommodation_fee(seg1, seg2, date, wait1)
                                    acc2 = self._calculate_accommodation_fee(seg2, seg3, seg2_date, wait2)
                                    accommodation = acc1 + acc2

                                total_price = seg1.price + seg2.price + seg3.price + accommodation
                                total_duration = (seg1.duration_minutes + wait1 +
                                                  seg2.duration_minutes + wait2 +
                                                  seg3.duration_minutes)

                                route = RoutePlan(
                                    segments=[seg1, seg2, seg3],
                                    transfer_cities=[hub1, hub2],
                                    min_transfer_hours=min_transfer_hours,
                                    total_price=total_price,
                                    total_duration_minutes=total_duration,
                                    accommodation_fee=accommodation,
                                    transfer_wait_minutes=[wait1, wait2],
                                    route_type=f"{type1}_{type2}_{type3}",
                                    feasible=feasible,
                                    infeasible_reason=reason
                                )
                                routes.append(route)

        return routes

    def _check_transfer_feasibility(
        self,
        seg1: TransportSegment,
        seg2: TransportSegment,
        base_date: str,
        min_transfer_hours: int
    ) -> Tuple[bool, int, str]:
        """
        检查换乘可行性

        Args:
            seg1: 第一段交通
            seg2: 第二段交通
            base_date: 第一段出发日期
            min_transfer_hours: 最小换乘时间（小时）

        Returns:
            (是否可行, 等待分钟数, 不可行原因)
        """
        try:
            # 计算第一段到达时间
            arr_dt = seg1.get_arrival_datetime(base_date)

            # 计算最早可乘坐第二段的时间
            min_transfer_minutes = min_transfer_hours * 60
            earliest_dep = arr_dt + timedelta(minutes=min_transfer_minutes)

            # 第二段出发时间（可能是当天或次日）
            dep_time_str = seg2.departure_time
            dep_hour, dep_min = map(int, dep_time_str.split(":"))

            # 尝试当天和次日
            for day_offset in range(3):  # 最多看后3天
                dep_dt = arr_dt.replace(hour=dep_hour, minute=dep_min, second=0, microsecond=0)
                dep_dt += timedelta(days=day_offset)

                if dep_dt >= earliest_dep:
                    wait_minutes = int((dep_dt - arr_dt).total_seconds() / 60)

                    # 检查等待时间是否合理（不超过24小时）
                    if wait_minutes <= 24 * 60:
                        return True, wait_minutes, ""
                    else:
                        return False, wait_minutes, f"等待时间过长({wait_minutes // 60}小时)"

            return False, 0, "未找到可行的换乘班次"

        except Exception as e:
            return False, 0, f"计算换乘出错: {str(e)}"

    def _get_arrival_date(
        self,
        seg1: TransportSegment,
        seg2: TransportSegment,
        base_date: str,
        wait_minutes: int
    ) -> str:
        """获取第二段出发日期"""
        try:
            arr_dt = seg1.get_arrival_datetime(base_date)
            dep_dt = arr_dt + timedelta(minutes=wait_minutes)
            return dep_dt.strftime("%Y-%m-%d")
        except:
            return base_date

    def _calculate_accommodation_fee(
        self,
        seg1: TransportSegment,
        seg2: TransportSegment,
        base_date: str,
        wait_minutes: int
    ) -> int:
        """
        计算住宿费

        规则：
        1. 等待时间 >= threshold 且 跨夜间（22:00-06:00）
        2. 等待时间 >= 12小时（无论何时）
        """
        if wait_minutes < self.accommodation_threshold_hours * 60:
            # 不满足时间阈值
            if wait_minutes < self.LONG_WAIT_THRESHOLD_HOURS * 60:
                return 0

        # 检查是否跨夜间
        try:
            arr_dt = seg1.get_arrival_datetime(base_date)
            dep_dt = arr_dt + timedelta(minutes=wait_minutes)

            # 检查等待期间是否包含夜间时段
            current = arr_dt
            while current < dep_dt:
                hour = current.hour
                if hour >= self.NIGHT_START_HOUR or hour < self.NIGHT_END_HOUR:
                    return self.DEFAULT_ACCOMMODATION_FEE
                current += timedelta(hours=1)

            # 超长等待也需要住宿
            if wait_minutes >= self.LONG_WAIT_THRESHOLD_HOURS * 60:
                return self.DEFAULT_ACCOMMODATION_FEE

        except:
            pass

        return 0

    # ==================== 结果输出 ====================

    def format_routes_for_ai(
        self,
        routes: List[RoutePlan],
        origin: str,
        destination: str,
        date: str,
        top_n: int = 20
    ) -> str:
        """
        将计算结果格式化为给AI的文本

        Args:
            routes: 计算好的路线列表
            origin: 出发城市
            destination: 目的城市
            date: 出发日期
            top_n: 返回前N个方案

        Returns:
            格式化的文本
        """
        lines = [
            f"# {date} {origin} → {destination} 出行方案计算结果",
            "",
            f"以下是程序计算出的可行方案（共{len(routes)}个，显示前{min(len(routes), top_n)}个）：",
            ""
        ]

        # 按类型分组
        direct_routes = [r for r in routes if len(r.segments) == 1]
        two_leg_routes = [r for r in routes if len(r.segments) == 2]
        three_leg_routes = [r for r in routes if len(r.segments) == 3]

        # 直达方案
        if direct_routes:
            lines.append("## 一、直达方案")
            lines.append("")
            for i, route in enumerate(direct_routes[:5], 1):
                lines.extend(self._format_single_route(route, i))
            lines.append("")

        # 两段中转方案
        if two_leg_routes:
            lines.append("## 二、两段中转方案（1次中转）")
            lines.append("")

            # 按换乘时间分组
            routes_2h = [r for r in two_leg_routes if r.min_transfer_hours == 2][:10]
            routes_3h = [r for r in two_leg_routes if r.min_transfer_hours == 3][:10]

            if routes_2h:
                lines.append("### 最小换乘时间2小时版本")
                for i, route in enumerate(routes_2h[:5], 1):
                    lines.extend(self._format_single_route(route, i))
                lines.append("")

            if routes_3h:
                lines.append("### 最小换乘时间3小时版本")
                for i, route in enumerate(routes_3h[:5], 1):
                    lines.extend(self._format_single_route(route, i))
                lines.append("")

        # 三段中转方案
        if three_leg_routes:
            lines.append("## 三、三段中转方案（2次中转）")
            lines.append("")

            routes_2h = [r for r in three_leg_routes if r.min_transfer_hours == 2][:5]
            routes_3h = [r for r in three_leg_routes if r.min_transfer_hours == 3][:5]

            if routes_2h:
                lines.append("### 最小换乘时间2小时版本")
                for i, route in enumerate(routes_2h[:3], 1):
                    lines.extend(self._format_single_route(route, i))
                lines.append("")

            if routes_3h:
                lines.append("### 最小换乘时间3小时版本")
                for i, route in enumerate(routes_3h[:3], 1):
                    lines.extend(self._format_single_route(route, i))
                lines.append("")

        # 添加说明
        lines.extend([
            "---",
            "",
            "## 请根据以上计算结果，为用户推荐：",
            "1. **最便宜方案** - 总价最低",
            "2. **最快方案** - 总时长最短",
            "3. **性价比最高方案** - 综合价格和时间",
            "",
            "请用自然语言描述推荐的方案，包括具体的航班号/车次、时间、价格等信息。",
        ])

        return "\n".join(lines)

    def _format_single_route(self, route: RoutePlan, index: int) -> List[str]:
        """格式化单个路线"""
        lines = []

        # 标题
        type_desc = route.get_type_description()
        route_desc = route.get_description()
        lines.append(f"**方案{index}**: {route_desc}")
        lines.append(f"- 类型: {type_desc}")
        lines.append(f"- 总价: ¥{route.total_price}" +
                     (f"（含住宿费¥{route.accommodation_fee}）" if route.accommodation_fee > 0 else ""))
        lines.append(f"- 总时长: {route.total_duration_minutes // 60}小时{route.total_duration_minutes % 60}分钟")

        if route.transfer_cities:
            lines.append(f"- 中转城市: {' → '.join(route.transfer_cities)}")
            wait_str = ", ".join([f"{w // 60}小时{w % 60}分" for w in route.transfer_wait_minutes])
            lines.append(f"- 中转等待: {wait_str}")

        # 各段详情
        lines.append("- 行程详情:")
        for i, seg in enumerate(route.segments, 1):
            icon = "✈️" if seg.transport_type == TransportType.FLIGHT else "🚄"
            cross_day = f"(+{seg.cross_days}天)" if seg.cross_days > 0 else ""
            flight_info = ""
            if seg.flight_type == "中转" and seg.transfer_city:
                flight_info = f" [经{seg.transfer_city}停留{seg.transfer_wait}]"

            lines.append(
                f"  {i}. {icon} {seg.number}: {seg.departure_time}({seg.departure_station or seg.departure_city})"
                f" → {seg.arrival_time}{cross_day}({seg.arrival_station or seg.arrival_city})"
                f" | ¥{seg.price}{flight_info}"
            )

        lines.append("")
        return lines
