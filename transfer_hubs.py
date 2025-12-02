# -*- coding: utf-8 -*-
"""
中转枢纽配置模块
基于《中国综合交通枢纽节点配置》文档
为 Go-home 智能行程规划系统提供中转枢纽数据支持
"""

from dataclasses import dataclass
from typing import List, Dict, Set, Optional
from enum import Enum


class HubType(Enum):
    """枢纽类型"""
    AVIATION = "aviation"          # 航空枢纽
    RAILWAY = "railway"            # 铁路枢纽
    AIR_RAIL = "air_rail"          # 空铁联运枢纽


class HubLevel(Enum):
    """枢纽等级"""
    LEVEL_1 = 1  # 最高级别：北京、上海、广州
    LEVEL_2 = 2  # 高级：深圳、成都、重庆、西安、武汉、郑州
    LEVEL_3 = 3  # 中级：南京、杭州、长沙、昆明、沈阳、哈尔滨
    LEVEL_4 = 4  # 区域级：其他省会城市


class AirRailTier(Enum):
    """空铁联运枢纽等级"""
    TIER_1 = 1  # 一体化零换乘，MCT 60-90分钟
    TIER_2 = 2  # 轨道交通紧密连接，MCT 120分钟
    TIER_3 = 3  # 摆渡车接驳，MCT 150分钟


@dataclass
class TransferHub:
    """中转枢纽信息"""
    city: str                      # 城市名
    airport_codes: List[str]       # 机场代码列表
    railway_stations: List[str]    # 铁路站点列表
    hub_types: Set[HubType]        # 支持的枢纽类型
    level: HubLevel                # 枢纽等级
    air_rail_tier: Optional[AirRailTier] = None  # 空铁联运等级
    region: str = ""               # 所属区域
    description: str = ""          # 战略定位描述


# =================== 国际航空枢纽（10个）===================
INTERNATIONAL_AVIATION_HUBS = {
    "北京": TransferHub(
        city="北京",
        airport_codes=["PEK", "PKX"],
        railway_stations=["北京南站", "北京西站", "北京站", "北京丰台站", "北京朝阳站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY, HubType.AIR_RAIL},
        level=HubLevel.LEVEL_1,
        air_rail_tier=AirRailTier.TIER_1,
        region="华北",
        description="华北门户，政务商务中心"
    ),
    "上海": TransferHub(
        city="上海",
        airport_codes=["PVG", "SHA"],
        railway_stations=["上海虹桥站", "上海站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY, HubType.AIR_RAIL},
        level=HubLevel.LEVEL_1,
        air_rail_tier=AirRailTier.TIER_1,
        region="华东",
        description="华东门户，经济中心"
    ),
    "广州": TransferHub(
        city="广州",
        airport_codes=["CAN"],
        railway_stations=["广州南站", "广州站", "广州东站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY},
        level=HubLevel.LEVEL_1,
        region="中南",
        description="华南门户，2023年吞吐量全国第一"
    ),
    "成都": TransferHub(
        city="成都",
        airport_codes=["CTU", "TFU"],
        railway_stations=["成都东站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY, HubType.AIR_RAIL},
        level=HubLevel.LEVEL_2,
        air_rail_tier=AirRailTier.TIER_1,
        region="西南",
        description="西南门户，双机场城市"
    ),
    "深圳": TransferHub(
        city="深圳",
        airport_codes=["SZX"],
        railway_stations=["深圳北站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY, HubType.AIR_RAIL},
        level=HubLevel.LEVEL_2,
        air_rail_tier=AirRailTier.TIER_2,
        region="中南",
        description="粤港澳大湾区核心，海空联运"
    ),
    "重庆": TransferHub(
        city="重庆",
        airport_codes=["CKG"],
        railway_stations=["重庆北站", "重庆西站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY},
        level=HubLevel.LEVEL_2,
        region="西南",
        description="西南出海通道"
    ),
    "昆明": TransferHub(
        city="昆明",
        airport_codes=["KMG"],
        railway_stations=["昆明南站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY},
        level=HubLevel.LEVEL_3,
        region="西南",
        description="面向南亚、东南亚门户"
    ),
    "西安": TransferHub(
        city="西安",
        airport_codes=["XIY"],
        railway_stations=["西安北站", "西安站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY},
        level=HubLevel.LEVEL_2,
        region="西北",
        description="丝绸之路空中起点，连接中亚"
    ),
    "乌鲁木齐": TransferHub(
        city="乌鲁木齐",
        airport_codes=["URC"],
        railway_stations=["乌鲁木齐站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY},
        level=HubLevel.LEVEL_3,
        region="西北",
        description="亚欧大陆核心，连接欧洲中东"
    ),
    "哈尔滨": TransferHub(
        city="哈尔滨",
        airport_codes=["HRB"],
        railway_stations=["哈尔滨西站", "哈尔滨站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY},
        level=HubLevel.LEVEL_3,
        region="东北",
        description="面向东北亚、北美门户"
    ),
}

# =================== 区域航空枢纽（29个）===================
REGIONAL_AVIATION_HUBS = {
    # 华北（4个）
    "天津": TransferHub(
        city="天津",
        airport_codes=["TSN"],
        railway_stations=["天津站", "天津西站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY},
        level=HubLevel.LEVEL_4,
        region="华北",
        description="京津城际交汇"
    ),
    "石家庄": TransferHub(
        city="石家庄",
        airport_codes=["SJW"],
        railway_stations=["石家庄站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY, HubType.AIR_RAIL},
        level=HubLevel.LEVEL_4,
        air_rail_tier=AirRailTier.TIER_3,
        region="华北",
        description="京广高铁、石太客专交汇"
    ),
    "太原": TransferHub(
        city="太原",
        airport_codes=["TYN"],
        railway_stations=[],
        hub_types={HubType.AVIATION},
        level=HubLevel.LEVEL_4,
        region="华北"
    ),
    "呼和浩特": TransferHub(
        city="呼和浩特",
        airport_codes=["HET"],
        railway_stations=[],
        hub_types={HubType.AVIATION},
        level=HubLevel.LEVEL_4,
        region="华北"
    ),
    # 东北（3个）
    "大连": TransferHub(
        city="大连",
        airport_codes=["DLC"],
        railway_stations=[],
        hub_types={HubType.AVIATION},
        level=HubLevel.LEVEL_4,
        region="东北"
    ),
    "沈阳": TransferHub(
        city="沈阳",
        airport_codes=["SHE"],
        railway_stations=["沈阳北站", "沈阳站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY},
        level=HubLevel.LEVEL_3,
        region="东北",
        description="哈大、京沈高铁枢纽"
    ),
    "长春": TransferHub(
        city="长春",
        airport_codes=["CGQ"],
        railway_stations=["长春站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY},
        level=HubLevel.LEVEL_4,
        region="东北",
        description="京哈线核心节点"
    ),
    # 华东（11个）
    "杭州": TransferHub(
        city="杭州",
        airport_codes=["HGH"],
        railway_stations=["杭州东站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY},
        level=HubLevel.LEVEL_3,
        region="华东",
        description="沪昆、杭甬、宁杭高铁交汇"
    ),
    "南京": TransferHub(
        city="南京",
        airport_codes=["NKG"],
        railway_stations=["南京南站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY},
        level=HubLevel.LEVEL_3,
        region="华东",
        description="京沪、沪汉蓉、宁杭高铁交汇（华东超级枢纽）"
    ),
    "青岛": TransferHub(
        city="青岛",
        airport_codes=["TAO"],
        railway_stations=[],
        hub_types={HubType.AVIATION, HubType.AIR_RAIL},
        level=HubLevel.LEVEL_4,
        air_rail_tier=AirRailTier.TIER_1,
        region="华东",
        description="综合换乘中心（济青高铁）"
    ),
    "厦门": TransferHub(
        city="厦门",
        airport_codes=["XMN"],
        railway_stations=[],
        hub_types={HubType.AVIATION},
        level=HubLevel.LEVEL_4,
        region="华东"
    ),
    "宁波": TransferHub(
        city="宁波",
        airport_codes=["NGB"],
        railway_stations=[],
        hub_types={HubType.AVIATION},
        level=HubLevel.LEVEL_4,
        region="华东"
    ),
    "合肥": TransferHub(
        city="合肥",
        airport_codes=["HFE"],
        railway_stations=["合肥南站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY},
        level=HubLevel.LEVEL_4,
        region="华东",
        description="沪汉蓉、合福、合蚌高铁交汇（米字型枢纽）"
    ),
    "南昌": TransferHub(
        city="南昌",
        airport_codes=["KHN"],
        railway_stations=["南昌西站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY},
        level=HubLevel.LEVEL_4,
        region="华东",
        description="沪昆高铁节点"
    ),
    "济南": TransferHub(
        city="济南",
        airport_codes=["TNA"],
        railway_stations=["济南西站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY},
        level=HubLevel.LEVEL_4,
        region="华东",
        description="京沪高铁五大始发站之一"
    ),
    "温州": TransferHub(
        city="温州",
        airport_codes=["WNZ"],
        railway_stations=[],
        hub_types={HubType.AVIATION},
        level=HubLevel.LEVEL_4,
        region="华东"
    ),
    "烟台": TransferHub(
        city="烟台",
        airport_codes=["YNT"],
        railway_stations=[],
        hub_types={HubType.AVIATION},
        level=HubLevel.LEVEL_4,
        region="华东"
    ),
    "福州": TransferHub(
        city="福州",
        airport_codes=["FOC"],
        railway_stations=[],
        hub_types={HubType.AVIATION},
        level=HubLevel.LEVEL_4,
        region="华东"
    ),
    # 中南（7个）
    "郑州": TransferHub(
        city="郑州",
        airport_codes=["CGO"],
        railway_stations=["郑州东站", "郑州站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY, HubType.AIR_RAIL},
        level=HubLevel.LEVEL_2,
        air_rail_tier=AirRailTier.TIER_1,
        region="中原",
        description="京广与徐兰高铁双十字中心（全国高铁心脏）"
    ),
    "武汉": TransferHub(
        city="武汉",
        airport_codes=["WUH"],
        railway_stations=["武汉站", "汉口站", "武昌站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY, HubType.AIR_RAIL},
        level=HubLevel.LEVEL_2,
        air_rail_tier=AirRailTier.TIER_1,
        region="华中",
        description="京广高铁枢纽，沪汉蓉铁路枢纽"
    ),
    "长沙": TransferHub(
        city="长沙",
        airport_codes=["CSX"],
        railway_stations=["长沙南站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY, HubType.AIR_RAIL},
        level=HubLevel.LEVEL_3,
        air_rail_tier=AirRailTier.TIER_2,
        region="中南",
        description="京广与沪昆高铁黄金十字"
    ),
    "南宁": TransferHub(
        city="南宁",
        airport_codes=["NNG"],
        railway_stations=["南宁东站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY},
        level=HubLevel.LEVEL_4,
        region="中南",
        description="面向东盟国际铁路通道起点"
    ),
    "海口": TransferHub(
        city="海口",
        airport_codes=["HAK"],
        railway_stations=["美兰站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY, HubType.AIR_RAIL},
        level=HubLevel.LEVEL_4,
        air_rail_tier=AirRailTier.TIER_1,
        region="中南",
        description="地下直连（环岛高铁）"
    ),
    "三亚": TransferHub(
        city="三亚",
        airport_codes=["SYX"],
        railway_stations=["凤凰机场站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY, HubType.AIR_RAIL},
        level=HubLevel.LEVEL_4,
        air_rail_tier=AirRailTier.TIER_1,
        region="中南",
        description="连廊连接（环岛高铁）"
    ),
    "桂林": TransferHub(
        city="桂林",
        airport_codes=["KWL"],
        railway_stations=[],
        hub_types={HubType.AVIATION},
        level=HubLevel.LEVEL_4,
        region="中南"
    ),
    # 西南（2个）
    "贵阳": TransferHub(
        city="贵阳",
        airport_codes=["KWE"],
        railway_stations=["贵阳北站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY, HubType.AIR_RAIL},
        level=HubLevel.LEVEL_4,
        air_rail_tier=AirRailTier.TIER_1,
        region="西南",
        description="沪昆、贵广、成贵十字交汇"
    ),
    "拉萨": TransferHub(
        city="拉萨",
        airport_codes=["LXA"],
        railway_stations=[],
        hub_types={HubType.AVIATION},
        level=HubLevel.LEVEL_4,
        region="西南"
    ),
    # 西北（3个）
    "兰州": TransferHub(
        city="兰州",
        airport_codes=["LHW"],
        railway_stations=["兰州西站"],
        hub_types={HubType.AVIATION, HubType.RAILWAY, HubType.AIR_RAIL},
        level=HubLevel.LEVEL_4,
        air_rail_tier=AirRailTier.TIER_1,
        region="西北",
        description="徐兰高铁终点，兰新高铁起点（进疆必经）"
    ),
    "银川": TransferHub(
        city="银川",
        airport_codes=["INC"],
        railway_stations=[],
        hub_types={HubType.AVIATION},
        level=HubLevel.LEVEL_4,
        region="西北"
    ),
    "西宁": TransferHub(
        city="西宁",
        airport_codes=["XNN"],
        railway_stations=[],
        hub_types={HubType.AVIATION},
        level=HubLevel.LEVEL_4,
        region="西北"
    ),
}

# =================== 纯铁路枢纽 ===================
RAILWAY_ONLY_HUBS = {
    "徐州": TransferHub(
        city="徐州",
        airport_codes=["XUZ"],
        railway_stations=["徐州东站"],
        hub_types={HubType.RAILWAY},
        level=HubLevel.LEVEL_4,
        region="华东",
        description="京沪与徐兰高铁十字交叉（中转神器）"
    ),
    "无锡": TransferHub(
        city="无锡",
        airport_codes=["WUX"],
        railway_stations=["无锡站"],
        hub_types={HubType.RAILWAY},
        level=HubLevel.LEVEL_4,
        region="华东",
        description="沪宁线核心大站"
    ),
    "常州": TransferHub(
        city="常州",
        airport_codes=["CZX"],
        railway_stations=["常州站"],
        hub_types={HubType.RAILWAY},
        level=HubLevel.LEVEL_4,
        region="华东",
        description="沪宁线核心大站"
    ),
    "衡阳": TransferHub(
        city="衡阳",
        airport_codes=[],
        railway_stations=["衡阳东站"],
        hub_types={HubType.RAILWAY},
        level=HubLevel.LEVEL_4,
        region="中南",
        description="京广高铁节点"
    ),
    "山海关": TransferHub(
        city="秦皇岛",
        airport_codes=["BPE"],
        railway_stations=["山海关站"],
        hub_types={HubType.RAILWAY},
        level=HubLevel.LEVEL_4,
        region="东北",
        description="关内外界限咽喉"
    ),
}

# =================== 合并所有枢纽 ===================
ALL_HUBS: Dict[str, TransferHub] = {}
ALL_HUBS.update(INTERNATIONAL_AVIATION_HUBS)
ALL_HUBS.update(REGIONAL_AVIATION_HUBS)
ALL_HUBS.update(RAILWAY_ONLY_HUBS)


# =================== 双机场城市配置 ===================
DUAL_AIRPORT_CITIES = {
    "北京": {
        "airports": ["PEK", "PKX"],
        "cross_airport_mct": 240,  # 跨机场最小中转时间（分钟）
        "penalty_factor": 2.0
    },
    "上海": {
        "airports": ["PVG", "SHA"],
        "cross_airport_mct": 240,
        "penalty_factor": 2.0
    },
    "成都": {
        "airports": ["CTU", "TFU"],
        "cross_airport_mct": 200,
        "penalty_factor": 2.0
    },
}


# =================== 中转时间配置 ===================
TRANSFER_TIME_CONFIG = {
    # 空铁一体化（第一梯队）
    AirRailTier.TIER_1: {"min_mct": 60, "max_mct": 90},
    # 轨道交通连接（第二梯队）
    AirRailTier.TIER_2: {"min_mct": 120, "max_mct": 120},
    # 摆渡车接驳（第三梯队）
    AirRailTier.TIER_3: {"min_mct": 150, "max_mct": 150},
    # 同机场航班中转
    "same_airport_flight": {"min_mct": 90, "max_mct": 120},
    # 同城跨机场中转
    "cross_airport": {"min_mct": 240, "max_mct": 240},
    # 同城跨火车站中转
    "cross_station": {"min_mct": 90, "max_mct": 120},
    # 铁路同站换乘
    "same_station_train": {"min_mct": 30, "max_mct": 60},
}


# =================== 区域中转策略 ===================
REGIONAL_STRATEGIES = {
    "华北减压阀": {
        "description": "北京票价过高或售罄时的替代方案",
        "primary": "北京",
        "alternatives": [
            {"city": "天津", "connection": "京津城际30分钟"},
            {"city": "石家庄", "connection": "京石高铁"}
        ]
    },
    "西北扇形辐射": {
        "description": "前往新疆、青海、甘肃",
        "priority": ["西安", "兰州", "乌鲁木齐"]
    },
    "长三角多点互备": {
        "description": "上海机票昂贵时的替代方案",
        "primary": "上海",
        "alternatives": [
            {"city": "杭州", "connection": "高铁至上海"},
            {"city": "无锡", "connection": "高铁至上海"},
            {"city": "南京", "connection": "高铁至上海"}
        ]
    },
    "国际入境中转": {
        "description": "国际航班转国内小城市",
        "priority_1": ["北京", "上海", "广州"],
        "priority_2": ["成都", "深圳", "西安"],
        "priority_3": ["郑州", "武汉", "长沙"]
    }
}


class TransferHubManager:
    """中转枢纽管理器"""

    def __init__(self):
        self.hubs = ALL_HUBS
        self.dual_airport_cities = DUAL_AIRPORT_CITIES
        self.transfer_time_config = TRANSFER_TIME_CONFIG
        self.regional_strategies = REGIONAL_STRATEGIES

    def get_aviation_hubs(self, level: Optional[HubLevel] = None) -> List[TransferHub]:
        """获取航空枢纽列表"""
        hubs = [h for h in self.hubs.values() if HubType.AVIATION in h.hub_types]
        if level:
            hubs = [h for h in hubs if h.level == level]
        return sorted(hubs, key=lambda x: x.level.value)

    def get_railway_hubs(self, level: Optional[HubLevel] = None) -> List[TransferHub]:
        """获取铁路枢纽列表"""
        hubs = [h for h in self.hubs.values() if HubType.RAILWAY in h.hub_types]
        if level:
            hubs = [h for h in hubs if h.level == level]
        return sorted(hubs, key=lambda x: x.level.value)

    def get_air_rail_hubs(self, tier: Optional[AirRailTier] = None) -> List[TransferHub]:
        """获取空铁联运枢纽列表"""
        hubs = [h for h in self.hubs.values() if HubType.AIR_RAIL in h.hub_types]
        if tier:
            hubs = [h for h in hubs if h.air_rail_tier == tier]
        return sorted(hubs, key=lambda x: (x.level.value, x.air_rail_tier.value if x.air_rail_tier else 99))

    def get_hubs_by_region(self, region: str) -> List[TransferHub]:
        """按区域获取枢纽"""
        return [h for h in self.hubs.values() if h.region == region]

    def get_hub_by_city(self, city: str) -> Optional[TransferHub]:
        """按城市名获取枢纽"""
        return self.hubs.get(city)

    def get_recommended_transfer_cities(
        self,
        transport_type: str = "all",  # "flight", "train", "all"
        max_count: int = 10
    ) -> List[str]:
        """
        获取推荐的中转城市列表

        Args:
            transport_type: 交通类型 - "flight"(仅航空), "train"(仅铁路), "all"(全部)
            max_count: 返回的最大城市数量

        Returns:
            按优先级排序的城市名列表
        """
        if transport_type == "flight":
            hubs = self.get_aviation_hubs()
        elif transport_type == "train":
            hubs = self.get_railway_hubs()
        else:
            # 优先选择同时支持航空和铁路的枢纽
            hubs = sorted(
                self.hubs.values(),
                key=lambda x: (
                    x.level.value,
                    -len(x.hub_types),  # 支持类型越多越靠前
                    x.air_rail_tier.value if x.air_rail_tier else 99
                )
            )

        return [h.city for h in hubs[:max_count]]

    def get_transfer_prompt_info(self, transport_type: str = "all") -> str:
        """
        获取用于 AI 系统提示词的中转枢纽信息

        Args:
            transport_type: 交通类型

        Returns:
            格式化的中转枢纽信息文本
        """
        if transport_type == "flight":
            cities = self.get_recommended_transfer_cities("flight", 15)
            return f"""【推荐航空中转枢纽】
优先级从高到低：{', '.join(cities)}

【空铁联运枢纽】（可从飞机转高铁）
第一梯队（零换乘，60-90分钟）：上海虹桥、北京大兴、郑州新郑、海口美兰、成都双流/天府、贵阳龙洞堡
第二梯队（轨道连接，120分钟）：长沙黄花、深圳宝安"""

        elif transport_type == "train":
            cities = self.get_recommended_transfer_cities("train", 15)
            return f"""【推荐铁路中转枢纽】
优先级从高到低：{', '.join(cities)}

【重要铁路节点说明】
- 郑州东站：京广与徐兰高铁双十字中心（全国高铁心脏）
- 徐州东站：京沪与徐兰高铁十字交叉（中转神器）
- 武汉站/汉口站：京广与沪汉蓉交汇
- 长沙南站：京广与沪昆高铁黄金十字
- 南京南站：京沪、沪汉蓉、宁杭高铁交汇（华东超级枢纽）
- 贵阳北站：沪昆、贵广、成贵十字交汇"""

        else:
            aviation_cities = self.get_recommended_transfer_cities("flight", 10)
            railway_cities = self.get_recommended_transfer_cities("train", 10)
            air_rail_cities = [h.city for h in self.get_air_rail_hubs(AirRailTier.TIER_1)]

            return f"""【推荐航空中转枢纽】
{', '.join(aviation_cities)}

【推荐铁路中转枢纽】
{', '.join(railway_cities)}

【空铁联运枢纽】（飞机↔高铁零换乘或快速换乘）
第一梯队（60-90分钟换乘）：{', '.join(air_rail_cities)}

【双机场城市提醒】
- 北京（首都PEK/大兴PKX）、上海（浦东PVG/虹桥SHA）、成都（双流CTU/天府TFU）
- 跨机场中转需预留至少4小时，惩罚系数2.0x

【区域中转策略】
- 华北减压：北京票紧时可选 天津(京津城际30分钟)、石家庄
- 长三角互备：上海票贵时可选 杭州、南京、无锡 + 高铁至上海
- 西北扇形：进疆进藏优先 西安 → 兰州 → 乌鲁木齐"""

    def is_dual_airport_city(self, city: str) -> bool:
        """检查是否为双机场城市"""
        return city in self.dual_airport_cities

    def get_cross_airport_penalty(self, city: str) -> float:
        """获取跨机场中转惩罚系数"""
        if city in self.dual_airport_cities:
            return self.dual_airport_cities[city]["penalty_factor"]
        return 1.0


# 创建全局管理器实例
hub_manager = TransferHubManager()


def get_transfer_hub_prompt(transport_type: str = "all", enabled: bool = True) -> str:
    """
    获取中转枢纽模式的系统提示词补充内容

    Args:
        transport_type: 交通类型 ("flight", "train", "all")
        enabled: 是否启用中转枢纽模式

    Returns:
        系统提示词补充内容
    """
    if not enabled:
        return ""

    hub_info = hub_manager.get_transfer_prompt_info(transport_type)

    return f"""
【中转枢纽模式 - 已启用】
当无直达方案或直达票价过高时，系统将自动通过以下枢纽节点计算最优中转组合：

{hub_info}

【中转查询策略】
1. 首先尝试查询直达票务
2. 如果无直达或票价过高，自动查询通过上述枢纽的中转方案
3. 对于机票中转，使用 flight_getTransferFlightsByThreePlace 工具，需指定中转城市
4. 对于火车票中转，使用 train_get-interline-tickets 工具
5. 比较直达与中转方案，综合考虑价格、时间、换乘便利性给出推荐

【中转时间要求】
- 同站火车换乘：预留 30-60 分钟
- 空铁一体化换乘：预留 60-90 分钟
- 跨站/跨机场换乘：预留 120-240 分钟

【输出格式要求】
对于中转方案，请清晰标注：
- 第一程：出发地 → 中转地（时间、票价）
- 中转等待时间
- 第二程：中转地 → 目的地（时间、票价）
- 总耗时、总票价
"""


if __name__ == "__main__":
    # 测试代码
    manager = TransferHubManager()

    print("=" * 50)
    print("中转枢纽管理器测试")
    print("=" * 50)

    print("\n航空枢纽（Level 1-2）:")
    for hub in manager.get_aviation_hubs():
        if hub.level.value <= 2:
            print(f"  {hub.city}: {hub.airport_codes} - {hub.description}")

    print("\n铁路枢纽（Level 1-2）:")
    for hub in manager.get_railway_hubs():
        if hub.level.value <= 2:
            print(f"  {hub.city}: {hub.railway_stations} - {hub.description}")

    print("\n空铁联运枢纽（第一梯队）:")
    for hub in manager.get_air_rail_hubs(AirRailTier.TIER_1):
        print(f"  {hub.city}: {hub.airport_codes} + {hub.railway_stations}")

    print("\n推荐中转城市（全类型）:")
    print(f"  {manager.get_recommended_transfer_cities('all', 15)}")

    print("\n" + "=" * 50)
    print("系统提示词补充（飞机+火车）:")
    print("=" * 50)
    print(get_transfer_hub_prompt("all", True))
