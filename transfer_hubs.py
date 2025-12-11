# -*- coding: utf-8 -*-
"""
中转枢纽配置模块
基于《中国综合交通枢纽节点配置》文档
为 Go-home 智能行程规划系统提供中转枢纽数据支持

支持功能：
1. 国内中转枢纽（44个）
2. 国际中转枢纽（按区域划分）
3. 智能路线类型检测
4. 基于路线类型的枢纽推荐
"""

from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Tuple
from enum import Enum


# =================== 区域定义 ===================

class Region(Enum):
    """地理区域"""
    # 中国国内区域
    CHINA_NORTH = "华北"      # 北京、天津、河北、山西、内蒙古
    CHINA_NORTHEAST = "东北"  # 辽宁、吉林、黑龙江
    CHINA_EAST = "华东"       # 上海、江苏、浙江、安徽、福建、江西、山东
    CHINA_CENTRAL = "华中"    # 河南、湖北、湖南
    CHINA_SOUTH = "华南"      # 广东、广西、海南
    CHINA_SOUTHWEST = "西南"  # 重庆、四川、贵州、云南、西藏
    CHINA_NORTHWEST = "西北"  # 陕西、甘肃、青海、宁夏、新疆
    # 国际区域
    SOUTHEAST_ASIA = "东南亚"
    EAST_ASIA = "东亚"
    SOUTH_ASIA = "南亚"
    MIDDLE_EAST = "中东"
    EUROPE = "欧洲"
    NORTH_AMERICA = "北美"
    SOUTH_AMERICA = "南美"
    OCEANIA = "大洋洲"
    AFRICA = "非洲"
    HK_MACAO_TAIWAN = "港澳台"


class RouteType(Enum):
    """路线类型"""
    DOMESTIC = "domestic"                    # 国内 → 国内
    DOMESTIC_TO_SOUTHEAST_ASIA = "domestic_to_southeast_asia"  # 国内 → 东南亚
    DOMESTIC_TO_EAST_ASIA = "domestic_to_east_asia"            # 国内 → 东亚
    DOMESTIC_TO_LONG_HAUL = "domestic_to_long_haul"            # 国内 → 欧美/大洋洲等远程
    SOUTHEAST_ASIA_TO_DOMESTIC = "southeast_asia_to_domestic"  # 东南亚 → 国内
    EAST_ASIA_TO_DOMESTIC = "east_asia_to_domestic"            # 东亚 → 国内
    INTERNATIONAL_TO_DOMESTIC = "international_to_domestic"     # 其他国际 → 国内
    INTERNATIONAL = "international"          # 国际 → 国际


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


# =================== 国际中转枢纽配置 ===================

# 城市到区域的映射
CITY_TO_REGION: Dict[str, Region] = {
    # 中国国内城市
    "北京": Region.CHINA_NORTH, "天津": Region.CHINA_NORTH, "石家庄": Region.CHINA_NORTH,
    "太原": Region.CHINA_NORTH, "呼和浩特": Region.CHINA_NORTH,
    "沈阳": Region.CHINA_NORTHEAST, "大连": Region.CHINA_NORTHEAST, "长春": Region.CHINA_NORTHEAST,
    "哈尔滨": Region.CHINA_NORTHEAST,
    "上海": Region.CHINA_EAST, "南京": Region.CHINA_EAST, "杭州": Region.CHINA_EAST,
    "合肥": Region.CHINA_EAST, "福州": Region.CHINA_EAST, "南昌": Region.CHINA_EAST,
    "济南": Region.CHINA_EAST, "青岛": Region.CHINA_EAST, "厦门": Region.CHINA_EAST,
    "宁波": Region.CHINA_EAST, "温州": Region.CHINA_EAST, "烟台": Region.CHINA_EAST,
    "徐州": Region.CHINA_EAST, "无锡": Region.CHINA_EAST, "常州": Region.CHINA_EAST,
    "郑州": Region.CHINA_CENTRAL, "武汉": Region.CHINA_CENTRAL, "长沙": Region.CHINA_CENTRAL,
    "广州": Region.CHINA_SOUTH, "深圳": Region.CHINA_SOUTH, "南宁": Region.CHINA_SOUTH,
    "海口": Region.CHINA_SOUTH, "三亚": Region.CHINA_SOUTH, "桂林": Region.CHINA_SOUTH,
    "重庆": Region.CHINA_SOUTHWEST, "成都": Region.CHINA_SOUTHWEST, "贵阳": Region.CHINA_SOUTHWEST,
    "昆明": Region.CHINA_SOUTHWEST, "拉萨": Region.CHINA_SOUTHWEST,
    "西安": Region.CHINA_NORTHWEST, "兰州": Region.CHINA_NORTHWEST, "西宁": Region.CHINA_NORTHWEST,
    "银川": Region.CHINA_NORTHWEST, "乌鲁木齐": Region.CHINA_NORTHWEST,

    # 东南亚
    "曼谷": Region.SOUTHEAST_ASIA, "新加坡": Region.SOUTHEAST_ASIA, "吉隆坡": Region.SOUTHEAST_ASIA,
    "雅加达": Region.SOUTHEAST_ASIA, "马尼拉": Region.SOUTHEAST_ASIA, "河内": Region.SOUTHEAST_ASIA,
    "胡志明市": Region.SOUTHEAST_ASIA, "金边": Region.SOUTHEAST_ASIA, "万象": Region.SOUTHEAST_ASIA,
    "仰光": Region.SOUTHEAST_ASIA, "清迈": Region.SOUTHEAST_ASIA, "普吉岛": Region.SOUTHEAST_ASIA,
    "巴厘岛": Region.SOUTHEAST_ASIA, "岘港": Region.SOUTHEAST_ASIA, "暹粒": Region.SOUTHEAST_ASIA,

    # 东亚
    "东京": Region.EAST_ASIA, "大阪": Region.EAST_ASIA, "名古屋": Region.EAST_ASIA,
    "福冈": Region.EAST_ASIA, "札幌": Region.EAST_ASIA, "冲绳": Region.EAST_ASIA,
    "首尔": Region.EAST_ASIA, "釜山": Region.EAST_ASIA, "济州岛": Region.EAST_ASIA,

    # 港澳台
    "香港": Region.HK_MACAO_TAIWAN, "中国香港": Region.HK_MACAO_TAIWAN,
    "澳门": Region.HK_MACAO_TAIWAN, "中国澳门": Region.HK_MACAO_TAIWAN,
    "台北": Region.HK_MACAO_TAIWAN, "中国台北": Region.HK_MACAO_TAIWAN,
    "高雄": Region.HK_MACAO_TAIWAN, "中国高雄": Region.HK_MACAO_TAIWAN,

    # 南亚
    "新德里": Region.SOUTH_ASIA, "孟买": Region.SOUTH_ASIA, "班加罗尔": Region.SOUTH_ASIA,
    "科伦坡": Region.SOUTH_ASIA, "马尔代夫": Region.SOUTH_ASIA, "加德满都": Region.SOUTH_ASIA,

    # 中东
    "迪拜": Region.MIDDLE_EAST, "阿布扎比": Region.MIDDLE_EAST, "多哈": Region.MIDDLE_EAST,
    "利雅得": Region.MIDDLE_EAST, "伊斯坦布尔": Region.MIDDLE_EAST,

    # 欧洲
    "伦敦": Region.EUROPE, "巴黎": Region.EUROPE, "法兰克福": Region.EUROPE,
    "阿姆斯特丹": Region.EUROPE, "慕尼黑": Region.EUROPE, "苏黎世": Region.EUROPE,
    "罗马": Region.EUROPE, "米兰": Region.EUROPE, "马德里": Region.EUROPE,
    "巴塞罗那": Region.EUROPE, "维也纳": Region.EUROPE, "莫斯科": Region.EUROPE,
    "赫尔辛基": Region.EUROPE,

    # 北美
    "纽约": Region.NORTH_AMERICA, "洛杉矶": Region.NORTH_AMERICA, "旧金山": Region.NORTH_AMERICA,
    "芝加哥": Region.NORTH_AMERICA, "西雅图": Region.NORTH_AMERICA, "波士顿": Region.NORTH_AMERICA,
    "华盛顿": Region.NORTH_AMERICA, "温哥华": Region.NORTH_AMERICA, "多伦多": Region.NORTH_AMERICA,

    # 大洋洲
    "悉尼": Region.OCEANIA, "墨尔本": Region.OCEANIA, "奥克兰": Region.OCEANIA,

    # 非洲
    "开罗": Region.AFRICA, "约翰内斯堡": Region.AFRICA,
}

# 国际中转枢纽城市（按区域分组）- 扩展版，覆盖全球主要航空枢纽
INTERNATIONAL_HUBS: Dict[str, List[str]] = {
    # =================== 亚洲区域 ===================
    # 亚洲门户枢纽（用于国内↔欧美长途）- 扩展到10个
    "亚洲门户": [
        "香港", "东京", "首尔", "台北", "新加坡",
        "大阪", "名古屋", "福冈", "釜山", "澳门"
    ],

    # 东南亚枢纽（用于国内↔东南亚）- 扩展到15个
    "东南亚枢纽": [
        "曼谷", "新加坡", "吉隆坡", "雅加达", "马尼拉",
        "河内", "胡志明市", "金边", "万象", "仰光",
        "清迈", "普吉岛", "巴厘岛", "岘港", "暹粒"
    ],

    # =================== 中东区域 ===================
    # 中东枢纽（用于国内↔欧洲/非洲）- 扩展到10个
    "中东枢纽": [
        "迪拜", "多哈", "阿布扎比", "利雅得", "吉达",
        "科威特", "巴林", "马斯喀特", "伊斯坦布尔", "安曼"
    ],

    # =================== 欧洲区域 ===================
    # 欧洲枢纽（用于欧洲内部中转）- 扩展到20个
    "欧洲枢纽": [
        "伦敦", "巴黎", "法兰克福", "阿姆斯特丹", "慕尼黑",
        "苏黎世", "罗马", "米兰", "马德里", "巴塞罗那",
        "维也纳", "布鲁塞尔", "赫尔辛基", "莫斯科", "圣彼得堡",
        "斯德哥尔摩", "哥本哈根", "华沙", "布拉格", "都柏林"
    ],

    # =================== 北美区域 ===================
    # 北美枢纽（用于北美内部中转）- 扩展到15个
    "北美枢纽": [
        "洛杉矶", "旧金山", "西雅图", "温哥华", "纽约",
        "芝加哥", "波士顿", "华盛顿", "达拉斯", "休斯顿",
        "亚特兰大", "迈阿密", "多伦多", "蒙特利尔", "丹佛"
    ],

    # =================== 大洋洲区域 ===================
    # 大洋洲枢纽 - 新增8个
    "大洋洲枢纽": [
        "悉尼", "墨尔本", "布里斯班", "珀斯", "奥克兰",
        "斐济", "关岛", "檀香山"
    ],

    # =================== 南亚区域 ===================
    # 南亚枢纽 - 新增8个
    "南亚枢纽": [
        "新德里", "孟买", "班加罗尔", "科伦坡", "马尔代夫",
        "加德满都", "达卡", "卡拉奇"
    ],

    # =================== 非洲区域 ===================
    # 非洲枢纽 - 新增6个
    "非洲枢纽": [
        "开罗", "约翰内斯堡", "开普敦", "内罗毕", "卡萨布兰卡",
        "亚的斯亚贝巴"
    ],

    # =================== 中南美区域 ===================
    # 中南美枢纽 - 新增6个
    "中南美枢纽": [
        "墨西哥城", "圣保罗", "布宜诺斯艾利斯", "利马",
        "波哥大", "巴拿马城"
    ],

    # =================== 国内门户 ===================
    # 国内出境门户（用于出国首选）- 扩展到10个
    "国内出境门户": [
        "北京", "上海", "广州", "香港", "成都",
        "昆明", "深圳", "西安", "重庆", "杭州"
    ],

    # 国内入境门户（用于回国首选）- 扩展到8个
    "国内入境门户": [
        "北京", "上海", "广州", "深圳", "成都",
        "西安", "杭州", "南京"
    ],
}

# 路线类型 → 推荐中转区域策略（扩展版 - 支持50+枢纽）
ROUTE_TRANSFER_STRATEGY: Dict[RouteType, Dict[str, any]] = {
    RouteType.DOMESTIC: {
        "description": "国内到国内",
        "use_domestic_hubs": True,
        "use_international_hubs": False,
        "hub_groups": [],  # 使用原有的44个国内枢纽
    },
    RouteType.DOMESTIC_TO_SOUTHEAST_ASIA: {
        "description": "国内到东南亚",
        "use_domestic_hubs": True,  # 华南门户（广州、昆明、深圳）有大量东南亚航线
        "use_international_hubs": True,
        "domestic_regions": [Region.CHINA_SOUTH, Region.CHINA_SOUTHWEST],  # 优先华南、西南
        "hub_groups": ["东南亚枢纽", "亚洲门户", "国内出境门户"],
        "recommended_domestic": ["广州", "昆明", "深圳", "香港", "南宁", "成都", "重庆"],
    },
    RouteType.DOMESTIC_TO_EAST_ASIA: {
        "description": "国内到东亚（日韩港澳台）",
        "use_domestic_hubs": True,
        "use_international_hubs": True,
        "domestic_regions": [Region.CHINA_EAST, Region.CHINA_NORTH, Region.CHINA_NORTHEAST],
        "hub_groups": ["亚洲门户", "国内出境门户"],
        "recommended_domestic": ["上海", "北京", "青岛", "大连", "沈阳", "天津", "杭州", "南京"],
    },
    RouteType.DOMESTIC_TO_LONG_HAUL: {
        "description": "国内到欧美/大洋洲等远程",
        "use_domestic_hubs": True,  # 改为True，国内大门户有直飞欧美航班
        "use_international_hubs": True,
        # 使用所有相关的国际枢纽组，不再限制recommended_international
        "hub_groups": [
            "亚洲门户",      # 10个：香港、东京、首尔、新加坡等
            "中东枢纽",      # 10个：迪拜、多哈、阿布扎比等
            "欧洲枢纽",      # 20个：伦敦、巴黎、法兰克福等
            "北美枢纽",      # 15个：洛杉矶、纽约、芝加哥等
            "大洋洲枢纽",    # 8个：悉尼、墨尔本等
            "国内出境门户",  # 10个：北京、上海、广州等
        ],
        # 不设置 recommended_international，让 get_hubs_for_route 使用所有 hub_groups
    },
    RouteType.SOUTHEAST_ASIA_TO_DOMESTIC: {
        "description": "东南亚回国内",
        "use_domestic_hubs": True,
        "use_international_hubs": True,
        "hub_groups": ["东南亚枢纽", "亚洲门户", "国内入境门户"],
        "recommended_domestic": ["广州", "深圳", "昆明", "南宁", "香港", "成都", "上海", "北京"],
    },
    RouteType.EAST_ASIA_TO_DOMESTIC: {
        "description": "东亚回国内",
        "use_domestic_hubs": True,
        "use_international_hubs": True,
        "hub_groups": ["亚洲门户", "国内入境门户"],
        "recommended_domestic": ["上海", "北京", "青岛", "大连", "沈阳", "天津", "杭州", "南京"],
    },
    RouteType.INTERNATIONAL_TO_DOMESTIC: {
        "description": "远程国际回国内",
        "use_domestic_hubs": True,  # 国内大门户接国际航班
        "use_international_hubs": True,
        "hub_groups": [
            "亚洲门户",
            "中东枢纽",
            "欧洲枢纽",
            "北美枢纽",
            "国内入境门户",
        ],
        "recommended_domestic": ["北京", "上海", "广州", "深圳", "成都", "西安", "杭州", "南京"],
    },
    RouteType.INTERNATIONAL: {
        "description": "国际到国际",
        "use_domestic_hubs": False,
        "use_international_hubs": True,
        # 国际到国际，使用全球所有主要枢纽
        "hub_groups": [
            "亚洲门户",
            "中东枢纽",
            "欧洲枢纽",
            "北美枢纽",
            "大洋洲枢纽",
            "南亚枢纽",
            "非洲枢纽",
            "中南美枢纽",
        ],
    },
}


def get_city_region(city: str) -> Optional[Region]:
    """
    获取城市所属区域

    Args:
        city: 城市名

    Returns:
        区域枚举值，如果未找到返回 None
    """
    # 精确匹配
    if city in CITY_TO_REGION:
        return CITY_TO_REGION[city]

    # 模糊匹配（处理带后缀的城市名，如"曼谷素万那普"）
    for city_name, region in CITY_TO_REGION.items():
        if city_name in city or city in city_name:
            return region

    return None


def is_chinese_domestic(city: str) -> bool:
    """
    检查城市是否是中国国内城市

    Args:
        city: 城市名

    Returns:
        True 如果是中国国内城市
    """
    region = get_city_region(city)
    if region is None:
        # 未知城市，假设是国内
        return True

    chinese_regions = {
        Region.CHINA_NORTH, Region.CHINA_NORTHEAST, Region.CHINA_EAST,
        Region.CHINA_CENTRAL, Region.CHINA_SOUTH, Region.CHINA_SOUTHWEST,
        Region.CHINA_NORTHWEST
    }
    return region in chinese_regions


def detect_route_type(from_city: str, to_city: str) -> RouteType:
    """
    检测路线类型

    Args:
        from_city: 出发城市
        to_city: 目的城市

    Returns:
        路线类型
    """
    from_domestic = is_chinese_domestic(from_city)
    to_domestic = is_chinese_domestic(to_city)

    from_region = get_city_region(from_city)
    to_region = get_city_region(to_city)

    # 国内 → 国内
    if from_domestic and to_domestic:
        return RouteType.DOMESTIC

    # 国内 → 国际
    if from_domestic and not to_domestic:
        # 判断目的地区域
        if to_region == Region.SOUTHEAST_ASIA:
            return RouteType.DOMESTIC_TO_SOUTHEAST_ASIA
        elif to_region == Region.EAST_ASIA:
            return RouteType.DOMESTIC_TO_EAST_ASIA
        elif to_region == Region.HK_MACAO_TAIWAN:
            return RouteType.DOMESTIC_TO_EAST_ASIA  # 港澳台视为东亚
        else:
            return RouteType.DOMESTIC_TO_LONG_HAUL

    # 国际 → 国内
    if not from_domestic and to_domestic:
        # 判断出发地区域
        if from_region == Region.SOUTHEAST_ASIA:
            return RouteType.SOUTHEAST_ASIA_TO_DOMESTIC
        elif from_region == Region.EAST_ASIA:
            return RouteType.EAST_ASIA_TO_DOMESTIC
        elif from_region == Region.HK_MACAO_TAIWAN:
            return RouteType.EAST_ASIA_TO_DOMESTIC  # 港澳台视为东亚
        else:
            return RouteType.INTERNATIONAL_TO_DOMESTIC

    # 国际 → 国际
    return RouteType.INTERNATIONAL


def get_route_type_description(route_type: RouteType) -> str:
    """获取路线类型的中文描述"""
    descriptions = {
        RouteType.DOMESTIC: "国内航线",
        RouteType.DOMESTIC_TO_SOUTHEAST_ASIA: "国内→东南亚",
        RouteType.DOMESTIC_TO_EAST_ASIA: "国内→东亚",
        RouteType.DOMESTIC_TO_LONG_HAUL: "国内→远程国际",
        RouteType.SOUTHEAST_ASIA_TO_DOMESTIC: "东南亚→国内",
        RouteType.EAST_ASIA_TO_DOMESTIC: "东亚→国内",
        RouteType.INTERNATIONAL_TO_DOMESTIC: "远程国际→国内",
        RouteType.INTERNATIONAL: "国际航线",
    }
    return descriptions.get(route_type, "未知")


class TransferHubManager:
    """中转枢纽管理器"""

    def __init__(self):
        self.hubs = ALL_HUBS
        self.dual_airport_cities = DUAL_AIRPORT_CITIES
        self.transfer_time_config = TRANSFER_TIME_CONFIG
        self.regional_strategies = REGIONAL_STRATEGIES
        self.international_hubs = INTERNATIONAL_HUBS
        self.route_strategies = ROUTE_TRANSFER_STRATEGY

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

    def get_hubs_for_route(
        self,
        from_city: str,
        to_city: str,
        max_count: int = 15,
        transport_type: str = "all",
        use_international_hubs: bool = True
    ) -> Tuple[List[str], RouteType, str]:
        """
        根据路线智能选择中转枢纽城市

        这是核心方法，根据出发地和目的地自动判断路线类型，
        并返回最合适的中转枢纽城市列表。

        Args:
            from_city: 出发城市
            to_city: 目的城市
            max_count: 最大返回数量
            transport_type: 交通类型 ("all", "flight", "train")
            use_international_hubs: 是否使用国际枢纽（国内→国外路线时有效）

        Returns:
            Tuple[List[str], RouteType, str]:
                - 推荐的中转城市列表
                - 检测到的路线类型
                - 提示信息（用于UI显示）
        """
        # 1. 检测路线类型
        route_type = detect_route_type(from_city, to_city)
        strategy = self.route_strategies.get(route_type, {})

        hubs = []
        tip_message = ""

        # 2. 根据路线类型选择枢纽
        if route_type == RouteType.DOMESTIC:
            # 国内航线：使用原有的44个国内枢纽
            if transport_type == "flight":
                hubs = self.get_recommended_transfer_cities("flight", max_count)
            elif transport_type == "train":
                hubs = self.get_recommended_transfer_cities("train", max_count)
            else:
                hubs = self.get_recommended_transfer_cities("all", max_count)
            tip_message = f"国内航线，使用 {len(hubs)} 个国内枢纽"

        elif route_type == RouteType.DOMESTIC_TO_SOUTHEAST_ASIA:
            # 国内→东南亚：华南门户 + 东南亚枢纽
            domestic_hubs = strategy.get("recommended_domestic", [])

            # 【修改】根据use_international_hubs决定是否使用国际枢纽
            if use_international_hubs:
                intl_hubs = []
                for group in strategy.get("hub_groups", []):
                    intl_hubs.extend(self.international_hubs.get(group, []))
                # 去重并合并
                hubs = domestic_hubs + [h for h in intl_hubs if h not in domestic_hubs]
                hubs = hubs[:max_count]
                tip_message = f"国内→东南亚，使用 {len(domestic_hubs)} 个国内门户 + {len(intl_hubs)} 个东南亚枢纽"
            else:
                # 仅使用国内枢纽
                hubs = domestic_hubs[:max_count]
                tip_message = f"国内→东南亚（仅国内中转），使用 {len(hubs)} 个国内门户"

        elif route_type == RouteType.DOMESTIC_TO_EAST_ASIA:
            # 国内→东亚：华东/华北门户 + 亚洲枢纽
            domestic_hubs = strategy.get("recommended_domestic", [])

            # 【修改】根据use_international_hubs决定是否使用国际枢纽
            if use_international_hubs:
                intl_hubs = []
                for group in strategy.get("hub_groups", []):
                    intl_hubs.extend(self.international_hubs.get(group, []))
                hubs = domestic_hubs + [h for h in intl_hubs if h not in domestic_hubs]
                hubs = hubs[:max_count]
                tip_message = f"国内→东亚，使用 {len(domestic_hubs)} 个国内门户 + {len(intl_hubs)} 个亚洲枢纽"
            else:
                # 仅使用国内枢纽
                hubs = domestic_hubs[:max_count]
                tip_message = f"国内→东亚（仅国内中转），使用 {len(hubs)} 个国内门户"

        elif route_type == RouteType.DOMESTIC_TO_LONG_HAUL:
            # 国内→远程国际（欧美等）：使用全球主要枢纽
            # 【修改】根据use_international_hubs决定是否使用国际枢纽
            if use_international_hubs:
                # 优先从所有 hub_groups 收集（已扩展到73个枢纽）
                intl_hubs = []
                for group in strategy.get("hub_groups", []):
                    intl_hubs.extend(self.international_hubs.get(group, []))
                # 去重保序
                hubs = list(dict.fromkeys(intl_hubs))[:max_count]
                total_available = len(list(dict.fromkeys(intl_hubs)))
                tip_message = f"国内→远程国际，共有 {total_available} 个全球枢纽可用，已选择 {len(hubs)} 个"
            else:
                # 仅使用国内枢纽
                domestic_hubs = strategy.get("recommended_domestic", [])
                hubs = domestic_hubs[:max_count]
                tip_message = f"国内→远程国际（仅国内中转），使用 {len(hubs)} 个国内门户"

        elif route_type == RouteType.SOUTHEAST_ASIA_TO_DOMESTIC:
            # 东南亚→国内：东南亚枢纽 + 亚洲门户 + 国内门户
            domestic_hubs = strategy.get("recommended_domestic", [])

            # 【修改】根据use_international_hubs决定是否使用国际枢纽
            if use_international_hubs:
                intl_hubs = []
                for group in strategy.get("hub_groups", []):
                    intl_hubs.extend(self.international_hubs.get(group, []))
                all_hubs = intl_hubs + [h for h in domestic_hubs if h not in intl_hubs]
                hubs = list(dict.fromkeys(all_hubs))[:max_count]
                total_available = len(list(dict.fromkeys(all_hubs)))
                tip_message = f"东南亚→国内，共有 {total_available} 个枢纽可用（东南亚+亚洲+国内门户），已选择 {len(hubs)} 个"
            else:
                # 仅使用国内枢纽
                hubs = domestic_hubs[:max_count]
                tip_message = f"东南亚→国内（仅国内中转），使用 {len(hubs)} 个国内门户"

        elif route_type == RouteType.EAST_ASIA_TO_DOMESTIC:
            # 东亚→国内：亚洲门户 + 国内门户
            domestic_hubs = strategy.get("recommended_domestic", [])

            # 【修改】根据use_international_hubs决定是否使用国际枢纽
            if use_international_hubs:
                intl_hubs = []
                for group in strategy.get("hub_groups", []):
                    intl_hubs.extend(self.international_hubs.get(group, []))
                all_hubs = intl_hubs + [h for h in domestic_hubs if h not in intl_hubs]
                hubs = list(dict.fromkeys(all_hubs))[:max_count]
                total_available = len(list(dict.fromkeys(all_hubs)))
                tip_message = f"东亚→国内，共有 {total_available} 个枢纽可用（亚洲+国内门户），已选择 {len(hubs)} 个"
            else:
                # 仅使用国内枢纽
                hubs = domestic_hubs[:max_count]
                tip_message = f"东亚→国内（仅国内中转），使用 {len(hubs)} 个国内门户"

        elif route_type == RouteType.INTERNATIONAL_TO_DOMESTIC:
            # 远程国际→国内：全球枢纽 + 国内大门户
            domestic_hubs = strategy.get("recommended_domestic", [])

            # 【修改】根据use_international_hubs决定是否使用国际枢纽
            if use_international_hubs:
                intl_hubs = []
                for group in strategy.get("hub_groups", []):
                    intl_hubs.extend(self.international_hubs.get(group, []))
                # 合并国际枢纽和国内门户
                all_hubs = intl_hubs + [h for h in domestic_hubs if h not in intl_hubs]
                hubs = list(dict.fromkeys(all_hubs))[:max_count]
                total_available = len(list(dict.fromkeys(all_hubs)))
                tip_message = f"远程国际→国内，共有 {total_available} 个枢纽可用（全球枢纽+国内门户），已选择 {len(hubs)} 个"
            else:
                # 仅使用国内枢纽
                hubs = domestic_hubs[:max_count]
                tip_message = f"远程国际→国内（仅国内中转），使用 {len(hubs)} 个国内门户"

        elif route_type == RouteType.INTERNATIONAL:
            # 国际→国际：使用全球所有主要枢纽
            intl_hubs = []
            for group in strategy.get("hub_groups", []):
                intl_hubs.extend(self.international_hubs.get(group, []))
            hubs = list(dict.fromkeys(intl_hubs))[:max_count]
            total_available = len(list(dict.fromkeys(intl_hubs)))
            tip_message = f"国际航线，共有 {total_available} 个全球枢纽可用，已选择 {len(hubs)} 个"

        # 3. 排除出发地和目的地
        hubs = [h for h in hubs if h != from_city and h != to_city]

        return hubs, route_type, tip_message

    def get_route_info(self, from_city: str, to_city: str) -> Dict[str, any]:
        """
        获取路线信息（用于UI显示）

        Args:
            from_city: 出发城市
            to_city: 目的城市

        Returns:
            包含路线信息的字典
        """
        route_type = detect_route_type(from_city, to_city)
        hubs, _, tip = self.get_hubs_for_route(from_city, to_city)

        return {
            "route_type": route_type,
            "route_type_name": get_route_type_description(route_type),
            "is_international": route_type != RouteType.DOMESTIC,
            "recommended_hubs": hubs,
            "hub_count": len(hubs),
            "tip_message": tip,
            "from_region": get_city_region(from_city),
            "to_region": get_city_region(to_city),
        }


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

    print("=" * 60)
    print("中转枢纽管理器测试")
    print("=" * 60)

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

    print("\n" + "=" * 60)
    print("智能路线枢纽选择测试")
    print("=" * 60)

    # 测试不同类型的路线
    test_routes = [
        ("北京", "上海"),       # 国内 → 国内
        ("北京", "曼谷"),       # 国内 → 东南亚
        ("上海", "东京"),       # 国内 → 东亚
        ("北京", "旧金山"),     # 国内 → 远程国际
        ("纽约", "成都"),       # 国际 → 国内
        ("伦敦", "东京"),       # 国际 → 国际
    ]

    for from_city, to_city in test_routes:
        hubs, route_type, tip = manager.get_hubs_for_route(from_city, to_city)
        print(f"\n{from_city} → {to_city}")
        print(f"  路线类型: {get_route_type_description(route_type)}")
        print(f"  提示: {tip}")
        print(f"  推荐枢纽: {', '.join(hubs[:8])}{'...' if len(hubs) > 8 else ''}")

    print("\n" + "=" * 60)
    print("系统提示词补充（飞机+火车）:")
    print("=" * 60)
    print(get_transfer_hub_prompt("all", True))
