"""
Flight Info Tools - 航班信息查询工具

提供根据航班号查询具体航班信息的功能
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import random
import logging
import re

# 初始化日志器
logger = logging.getLogger(__name__)

# 模拟航班数据 - 主要国内外航空公司
MOCK_FLIGHT_DATA = {
    # 中国国际航空
    "CA1234": {
        "airline": "中国国际航空",
        "airline_code": "CA",
        "aircraft_type": "Boeing 737-800",
        "departure_airport": "北京首都国际机场",
        "departure_code": "PEK",
        "arrival_airport": "上海浦东国际机场", 
        "arrival_code": "PVG",
        "scheduled_departure": "08:30",
        "scheduled_arrival": "11:00",
        "terminal": {"departure": "T3", "arrival": "T2"},
        "gate": {"departure": "A12", "arrival": "B08"},
        "seat_map": {"economy": 150, "business": 20, "first": 8},
        "route_type": "domestic"
    },
    "CA8901": {
        "airline": "中国国际航空",
        "airline_code": "CA", 
        "aircraft_type": "Airbus A350-900",
        "departure_airport": "北京首都国际机场",
        "departure_code": "PEK",
        "arrival_airport": "纽约肯尼迪国际机场",
        "arrival_code": "JFK",
        "scheduled_departure": "13:45",
        "scheduled_arrival": "16:30+1",
        "terminal": {"departure": "T3", "arrival": "T1"},
        "gate": {"departure": "E15", "arrival": "4A"},
        "seat_map": {"economy": 280, "business": 36, "first": 12},
        "route_type": "international"
    },
    
    # 中国东方航空
    "MU5678": {
        "airline": "中国东方航空",
        "airline_code": "MU",
        "aircraft_type": "Boeing 777-300ER",
        "departure_airport": "上海浦东国际机场",
        "departure_code": "PVG",
        "arrival_airport": "洛杉矶国际机场",
        "arrival_code": "LAX",
        "scheduled_departure": "11:20",
        "scheduled_arrival": "07:45",
        "terminal": {"departure": "T1", "arrival": "TBIT"},
        "gate": {"departure": "D06", "arrival": "159"},
        "seat_map": {"economy": 296, "business": 42, "first": 8},
        "route_type": "international"
    },
    "MU2468": {
        "airline": "中国东方航空",
        "airline_code": "MU",
        "aircraft_type": "Airbus A320",
        "departure_airport": "上海虹桥国际机场",
        "departure_code": "SHA",
        "arrival_airport": "深圳宝安国际机场",
        "arrival_code": "SZX",
        "scheduled_departure": "14:15",
        "scheduled_arrival": "17:30",
        "terminal": {"departure": "T2", "arrival": "T3"},
        "gate": {"departure": "B15", "arrival": "A21"},
        "seat_map": {"economy": 174, "business": 8, "first": 0},
        "route_type": "domestic"
    },
    
    # 中国南方航空
    "CZ3691": {
        "airline": "中国南方航空",
        "airline_code": "CZ",
        "aircraft_type": "Airbus A330-300",
        "departure_airport": "广州白云国际机场",
        "departure_code": "CAN",
        "arrival_airport": "悉尼金斯福德·史密斯机场",
        "arrival_code": "SYD",
        "scheduled_departure": "09:15",
        "scheduled_arrival": "22:40",
        "terminal": {"departure": "T2", "arrival": "T1"},
        "gate": {"departure": "A28", "arrival": "38"},
        "seat_map": {"economy": 269, "business": 28, "first": 0},
        "route_type": "international"
    },
    "CZ1357": {
        "airline": "中国南方航空",
        "airline_code": "CZ",
        "aircraft_type": "Boeing 737-800",
        "departure_airport": "广州白云国际机场",
        "departure_code": "CAN",
        "arrival_airport": "武汉天河国际机场",
        "arrival_code": "WUH",
        "scheduled_departure": "16:45",
        "scheduled_arrival": "18:25",
        "terminal": {"departure": "T2", "arrival": "T3"},
        "gate": {"departure": "B05", "arrival": "C12"},
        "seat_map": {"economy": 162, "business": 12, "first": 0},
        "route_type": "domestic"
    },
    
    # 海南航空
    "HU7890": {
        "airline": "海南航空",
        "airline_code": "HU",
        "aircraft_type": "Boeing 787-9",
        "departure_airport": "海口美兰国际机场",
        "departure_code": "HAK",
        "arrival_airport": "芝加哥奥黑尔国际机场",
        "arrival_code": "ORD",
        "scheduled_departure": "02:30",
        "scheduled_arrival": "05:15",
        "terminal": {"departure": "T2", "arrival": "T5"},
        "gate": {"departure": "A08", "arrival": "M18"},
        "seat_map": {"economy": 259, "business": 36, "first": 6},
        "route_type": "international"
    },
    
    # 厦门航空
    "MF8123": {
        "airline": "厦门航空",
        "airline_code": "MF",
        "aircraft_type": "Boeing 737-800",
        "departure_airport": "厦门高崎国际机场",
        "departure_code": "XMN",
        "arrival_airport": "北京首都国际机场",
        "arrival_code": "PEK",
        "scheduled_departure": "07:20",
        "scheduled_arrival": "10:35",
        "terminal": {"departure": "T4", "arrival": "T2"},
        "gate": {"departure": "D18", "arrival": "C26"},
        "seat_map": {"economy": 162, "business": 12, "first": 0},
        "route_type": "domestic"
    },
    
    # 春秋航空
    "9C8765": {
        "airline": "春秋航空",
        "airline_code": "9C",
        "aircraft_type": "Airbus A320",
        "departure_airport": "上海浦东国际机场",
        "departure_code": "PVG",
        "arrival_airport": "大阪关西国际机场",
        "arrival_code": "KIX",
        "scheduled_departure": "12:40",
        "scheduled_arrival": "16:15",
        "terminal": {"departure": "T2", "arrival": "T1"},
        "gate": {"departure": "S02", "arrival": "12"},
        "seat_map": {"economy": 180, "business": 0, "first": 0},
        "route_type": "international"
    },
    
    # 吉祥航空
    "HO1288": {
        "airline": "吉祥航空",
        "airline_code": "HO",
        "aircraft_type": "Airbus A321",
        "departure_airport": "上海虹桥国际机场",
        "departure_code": "SHA",
        "arrival_airport": "成都双流国际机场",
        "arrival_code": "CTU",
        "scheduled_departure": "19:30",
        "scheduled_arrival": "22:45",
        "terminal": {"departure": "T1", "arrival": "T2"},
        "gate": {"departure": "A06", "arrival": "B18"},
        "seat_map": {"economy": 195, "business": 8, "first": 0},
        "route_type": "domestic"
    },
    
    # 国外航空公司示例
    "UA858": {
        "airline": "美国联合航空",
        "airline_code": "UA",
        "aircraft_type": "Boeing 777-300ER",
        "departure_airport": "旧金山国际机场",
        "departure_code": "SFO",
        "arrival_airport": "上海浦东国际机场",
        "arrival_code": "PVG",
        "scheduled_departure": "14:25",
        "scheduled_arrival": "18:50+1",
        "terminal": {"departure": "I", "arrival": "T2"},
        "gate": {"departure": "A1", "arrival": "E05"},
        "seat_map": {"economy": 276, "business": 52, "first": 8},
        "route_type": "international"
    },
    
    "NH955": {
        "airline": "全日本空输",
        "airline_code": "NH",
        "aircraft_type": "Boeing 787-8",
        "departure_airport": "东京羽田机场",
        "departure_code": "HND",
        "arrival_airport": "北京首都国际机场",
        "arrival_code": "PEK",
        "scheduled_departure": "09:55",
        "scheduled_arrival": "12:35",
        "terminal": {"departure": "T3", "arrival": "T3"},
        "gate": {"departure": "112", "arrival": "E09"},
        "seat_map": {"economy": 206, "business": 32, "first": 0},
        "route_type": "international"
    }
}

def generate_dynamic_status():
    """生成动态航班状态"""
    statuses = [
        {"status": "scheduled", "message": "准时"},
        {"status": "delayed", "message": "延误15分钟", "delay_minutes": 15},
        {"status": "delayed", "message": "延误30分钟", "delay_minutes": 30},
        {"status": "boarding", "message": "正在登机"},
        {"status": "departed", "message": "已起飞"},
        {"status": "in_flight", "message": "飞行中"},
        {"status": "arrived", "message": "已到达"},
        {"status": "cancelled", "message": "航班取消"}
    ]
    return random.choice(statuses)

def generate_price_info():
    """生成价格信息"""
    base_prices = {
        "economy": random.randint(800, 3500),
        "business": random.randint(3500, 12000),
        "first": random.randint(12000, 25000)
    }
    
    return {
        "economy": {
            "price": base_prices["economy"],
            "currency": "CNY",
            "availability": random.choice(["available", "limited", "sold_out"])
        },
        "business": {
            "price": base_prices["business"],
            "currency": "CNY",
            "availability": random.choice(["available", "limited", "sold_out"])
        },
        "first": {
            "price": base_prices["first"],
            "currency": "CNY",
            "availability": random.choice(["available", "limited"])
        }
    }

def generate_weather_info():
    """生成天气信息"""
    conditions = ["晴", "多云", "阴", "小雨", "中雨", "雾", "雪"]
    return {
        "departure": {
            "condition": random.choice(conditions),
            "temperature": random.randint(-10, 35),
            "visibility": random.choice(["良好", "一般", "较差"]),
            "wind": f"{random.choice(['北风', '南风', '东风', '西风'])}{random.randint(2, 8)}级"
        },
        "arrival": {
            "condition": random.choice(conditions),
            "temperature": random.randint(-10, 35),
            "visibility": random.choice(["良好", "一般", "较差"]),
            "wind": f"{random.choice(['北风', '南风', '东风', '西风'])}{random.randint(2, 8)}级"
        }
    }

def getFlightInfo(flight_number: str) -> Dict[str, Any]:
    """
    根据航班号查询航班详细信息
    
    Args:
        flight_number: 航班号 (如: CA1234, MU5678)
        
    Returns:
        包含航班详细信息的字典
    """
    logger.info(f"开始查询航班信息: {flight_number}")
    
    try:
        # 验证输入参数
        if not flight_number:
            logger.warning("航班号为空")
            return {
                "status": "error",
                "message": "航班号不能为空",
                "error_code": "EMPTY_FLIGHT_NUMBER"
            }
        
        # 格式化航班号 (转换为大写，移除空格)
        flight_number = flight_number.strip().upper()
        
        # 验证航班号格式
        if not re.match(r'^[A-Z0-9]{2,3}\d{3,4}$', flight_number):
            logger.warning(f"航班号格式不正确: {flight_number}")
            return {
                "status": "error", 
                "message": f"航班号格式不正确: {flight_number}。正确格式示例: CA1234, MU5678",
                "error_code": "INVALID_FLIGHT_NUMBER_FORMAT"
            }
        
        # 查询航班基础信息
        base_info = MOCK_FLIGHT_DATA.get(flight_number)
        
        if not base_info:
            logger.warning(f"未找到航班: {flight_number}")
            return {
                "status": "error",
                "message": f"未找到航班号 {flight_number} 的信息",
                "error_code": "FLIGHT_NOT_FOUND",
                "suggestion": "请检查航班号是否正确，或该航班可能已取消"
            }
        
        # 生成动态信息
        current_status = generate_dynamic_status()
        price_info = generate_price_info()
        weather_info = generate_weather_info()
        
        # 生成当前日期的航班时间
        today = datetime.now()
        
        # 构建完整的航班信息
        flight_info = {
            "status": "success",
            "flight_number": flight_number,
            "query_time": datetime.now().isoformat(),
            "basic_info": {
                "airline": base_info["airline"],
                "airline_code": base_info["airline_code"],
                "aircraft_type": base_info["aircraft_type"],
                "route_type": base_info["route_type"]
            },
            "route_info": {
                "departure": {
                    "airport": base_info["departure_airport"],
                    "code": base_info["departure_code"],
                    "terminal": base_info["terminal"]["departure"],
                    "gate": base_info["gate"]["departure"],
                    "scheduled_time": base_info["scheduled_departure"],
                    "actual_time": _calculate_actual_time(base_info["scheduled_departure"], current_status)
                },
                "arrival": {
                    "airport": base_info["arrival_airport"],
                    "code": base_info["arrival_code"],
                    "terminal": base_info["terminal"]["arrival"],
                    "gate": base_info["gate"]["arrival"],
                    "scheduled_time": base_info["scheduled_arrival"],
                    "actual_time": _calculate_actual_time(base_info["scheduled_arrival"], current_status)
                }
            },
            "current_status": current_status,
            "seat_map": base_info["seat_map"],
            "price_info": price_info,
            "weather_info": weather_info,
            "additional_info": {
                "check_in_counter": f"{base_info['airline_code']}{random.randint(1, 50):02d}",
                "baggage_allowance": {
                    "carry_on": "7kg",
                    "checked": "23kg" if base_info["route_type"] == "domestic" else "30kg"
                },
                "meal_service": "有" if base_info["route_type"] == "international" else "无",
                "wifi_available": random.choice([True, False]),
                "entertainment_system": random.choice([True, False])
            },
            "formatted_output": ""
        }
        
        # 生成格式化输出
        flight_info["formatted_output"] = _format_flight_info(flight_info)
        
        logger.info(f"航班信息查询成功: {flight_number}")
        return flight_info
        
    except Exception as e:
        logger.error(f"查询航班信息失败: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": f"查询航班信息失败: {str(e)}",
            "error_code": "QUERY_FAILED"
        }

def _calculate_actual_time(scheduled_time: str, status_info: Dict) -> str:
    """计算实际时间"""
    if status_info["status"] == "delayed" and "delay_minutes" in status_info:
        # 这里简化处理，实际应该解析时间并添加延误时间
        return f"{scheduled_time} (延误{status_info['delay_minutes']}分钟)"
    elif status_info["status"] == "cancelled":
        return "已取消"
    else:
        return scheduled_time

def _format_flight_info(flight_info: Dict[str, Any]) -> str:
    """
    格式化航班信息为易读的字符串
    
    Args:
        flight_info: 航班信息字典
        
    Returns:
        格式化后的字符串
    """
    basic = flight_info["basic_info"]
    route = flight_info["route_info"]
    status = flight_info["current_status"]
    prices = flight_info["price_info"]
    weather = flight_info["weather_info"]
    additional = flight_info["additional_info"]
    
    output = []
    
    # 基本信息
    output.append(f"✈️ 航班信息查询结果")
    output.append(f"🔖 航班号: {flight_info['flight_number']}")
    output.append(f"🏢 航空公司: {basic['airline']} ({basic['airline_code']})")
    output.append(f"✈️ 机型: {basic['aircraft_type']}")
    output.append(f"🌐 航线类型: {'国际航班' if basic['route_type'] == 'international' else '国内航班'}")
    output.append("")
    
    # 航线信息
    output.append(f"📍 航线信息")
    output.append(f"🛫 出发: {route['departure']['airport']} ({route['departure']['code']})")
    output.append(f"   航站楼: {route['departure']['terminal']}  登机口: {route['departure']['gate']}")
    output.append(f"   计划时间: {route['departure']['scheduled_time']}")
    output.append(f"   实际时间: {route['departure']['actual_time']}")
    output.append(f"🛬 到达: {route['arrival']['airport']} ({route['arrival']['code']})")
    output.append(f"   航站楼: {route['arrival']['terminal']}  出口: {route['arrival']['gate']}")
    output.append(f"   计划时间: {route['arrival']['scheduled_time']}")
    output.append(f"   实际时间: {route['arrival']['actual_time']}")
    output.append("")
    
    # 当前状态
    status_emoji = {
        "scheduled": "🕐",
        "delayed": "⏰", 
        "boarding": "🚪",
        "departed": "🛫",
        "in_flight": "✈️",
        "arrived": "🛬",
        "cancelled": "❌"
    }
    emoji = status_emoji.get(status["status"], "ℹ️")
    output.append(f"📊 当前状态: {emoji} {status['message']}")
    output.append("")
    
    # 座位和价格信息
    output.append(f"💺 座位配置:")
    seat_map = flight_info["seat_map"]
    if seat_map["economy"] > 0:
        econ_price = prices["economy"]
        output.append(f"   经济舱: {seat_map['economy']}座 - ¥{econ_price['price']} ({econ_price['availability']})")
    if seat_map["business"] > 0:
        bus_price = prices["business"]
        output.append(f"   商务舱: {seat_map['business']}座 - ¥{bus_price['price']} ({bus_price['availability']})")
    if seat_map["first"] > 0:
        first_price = prices["first"]
        output.append(f"   头等舱: {seat_map['first']}座 - ¥{first_price['price']} ({first_price['availability']})")
    output.append("")
    
    # 天气信息
    output.append(f"🌤️ 天气信息:")
    dep_weather = weather["departure"]
    arr_weather = weather["arrival"]
    output.append(f"   出发地: {dep_weather['condition']} {dep_weather['temperature']}°C {dep_weather['wind']} (能见度: {dep_weather['visibility']})")
    output.append(f"   目的地: {arr_weather['condition']} {arr_weather['temperature']}°C {arr_weather['wind']} (能见度: {arr_weather['visibility']})")
    output.append("")
    
    # 附加服务信息
    output.append(f"🛎️ 服务信息:")
    output.append(f"   值机柜台: {additional['check_in_counter']}")
    output.append(f"   行李额度: 手提 {additional['baggage_allowance']['carry_on']} / 托运 {additional['baggage_allowance']['checked']}")
    output.append(f"   机上餐食: {additional['meal_service']}")
    output.append(f"   WiFi: {'有' if additional['wifi_available'] else '无'}")
    output.append(f"   娱乐系统: {'有' if additional['entertainment_system'] else '无'}")
    output.append("")
    
    output.append(f"🕐 查询时间: {flight_info['query_time']}")
    
    return "\n".join(output)

# 便于测试的函数
def get_available_flights() -> List[str]:
    """获取所有可用的航班号列表"""
    return list(MOCK_FLIGHT_DATA.keys())

def get_airline_flights(airline_code: str) -> List[str]:
    """根据航空公司代码获取航班列表"""
    return [
        flight_num for flight_num, info in MOCK_FLIGHT_DATA.items()
        if info["airline_code"] == airline_code.upper()
    ]
