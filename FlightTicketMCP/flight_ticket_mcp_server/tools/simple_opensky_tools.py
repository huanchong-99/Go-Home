"""
Simple OpenSky Tools - API航班跟踪工具

提供基础的实时航班查询功能
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import time

# 初始化日志器
logger = logging.getLogger(__name__)


class SimpleOpenSkyTracker:
    """航班跟踪器"""
    
    def __init__(self):
        """初始化OpenSky客户端"""
        self.base_url = "https://opensky-network.org/api"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FlightTicketMCP/1.0'
        })
        logger.info("SimpleOpenSky客户端初始化完成")
    
    def get_all_states(self, bbox: Optional[tuple] = None) -> Dict[str, Any]:
        """
        获取所有航班状态
        
        Args:
            bbox: 可选的边界框 (min_lat, max_lat, min_lon, max_lon)
            
        Returns:
            包含航班状态的字典
        """
        try:
            url = f"{self.base_url}/states/all"
            params = {}
            
            if bbox:
                params.update({
                    'lamin': bbox[0],
                    'lamax': bbox[1], 
                    'lomin': bbox[2],
                    'lomax': bbox[3]
                })
            
            logger.info(f"请求OpenSky API: {url}")
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_states_response(data, bbox)
            else:
                logger.warning(f"OpenSky API请求失败: {response.status_code}")
                return {
                    "status": "error",
                    "message": f"API请求失败: HTTP {response.status_code}"
                }
                
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": "请求超时，OpenSky服务器响应过慢"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenSky API请求异常: {e}")
            return {
                "status": "error",
                "message": f"网络请求失败: {str(e)}"
            }
        except Exception as e:
            logger.error(f"获取航班状态失败: {e}")
            return {
                "status": "error",
                "message": f"查询失败: {str(e)}"
            }
    
    def _parse_states_response(self, data: Dict, bbox: Optional[tuple] = None) -> Dict[str, Any]:
        """解析OpenSky API响应数据"""
        try:
            if not data or 'states' not in data or data['states'] is None:
                return {
                    "status": "success",
                    "message": "当前无航班数据",
                    "flights": [],
                    "flight_count": 0,
                    "bbox": bbox,
                    "query_time": datetime.now().isoformat()
                }
            
            flights = []
            for state_array in data['states']:
                if state_array and len(state_array) >= 17:  # 确保有足够的数据
                    flight_info = self._parse_state_vector(state_array)
                    if flight_info:
                        flights.append(flight_info)
            
            return {
                "status": "success",
                "message": f"成功获取 {len(flights)} 架航班信息",
                "flights": flights,
                "flight_count": len(flights),
                "bbox": bbox,
                "query_time": datetime.now().isoformat(),
                "data_source": "opensky_network_rest"
            }
            
        except Exception as e:
            logger.error(f"解析航班数据失败: {e}")
            return {
                "status": "error",
                "message": f"数据解析失败: {str(e)}"
            }
    
    def _parse_state_vector(self, state_array: List) -> Optional[Dict[str, Any]]:
        """
        解析单个状态向量
        
        OpenSky API状态向量格式:
        [0] icao24, [1] callsign, [2] origin_country, [3] time_position,
        [4] last_contact, [5] longitude, [6] latitude, [7] baro_altitude,
        [8] on_ground, [9] velocity, [10] true_track, [11] vertical_rate,
        [12] sensors, [13] geo_altitude, [14] squawk, [15] spi, [16] position_source
        """
        try:
            if len(state_array) < 17:
                return None
                
            icao24 = state_array[0]
            callsign = state_array[1].strip() if state_array[1] else None
            origin_country = state_array[2]
            longitude = state_array[5]
            latitude = state_array[6]
            baro_altitude = state_array[7]  # 气压高度
            on_ground = state_array[8]
            velocity = state_array[9]  # 地面速度 m/s
            true_track = state_array[10]  # 真航迹角
            vertical_rate = state_array[11]  # 垂直速度 m/s
            geo_altitude = state_array[13]  # 几何高度
            last_contact = state_array[4]
            
            # 计算航班状态
            status = "UNKNOWN"
            if on_ground:
                status = "ON_GROUND"
            elif velocity and velocity > 100:  # 100 m/s ≈ 360 km/h
                status = "AIRBORNE"
            elif velocity and velocity > 10:
                status = "TAXI"
            else:
                status = "STATIONARY"
            
            # 选择更可靠的高度数据
            altitude = baro_altitude if baro_altitude else geo_altitude
            
            return {
                "icao24": icao24,
                "callsign": callsign,
                "origin_country": origin_country,
                "position": {
                    "longitude": longitude,
                    "latitude": latitude,
                    "altitude_meters": altitude,
                    "altitude_feet": round(altitude * 3.28084) if altitude else None
                },
                "velocity": {
                    "ground_speed_ms": velocity,
                    "ground_speed_kmh": round(velocity * 3.6) if velocity else None,
                    "vertical_rate_ms": vertical_rate
                },
                "true_track": true_track,
                "on_ground": on_ground,
                "status": status,
                "last_contact": datetime.fromtimestamp(last_contact).isoformat() if last_contact else None,
                "last_contact_seconds_ago": int(time.time() - last_contact) if last_contact else None
            }
            
        except Exception as e:
            logger.warning(f"解析状态向量失败: {e}")
            return None
    
    def search_flights_by_callsign(self, callsign_pattern: str) -> Dict[str, Any]:
        """根据呼号模式搜索航班"""
        all_states = self.get_all_states()
        
        if all_states.get("status") != "success":
            return all_states
        
        matching_flights = []
        for flight in all_states.get("flights", []):
            if flight.get("callsign"):
                if callsign_pattern.upper() in flight["callsign"].upper():
                    matching_flights.append(flight)
        
        return {
            "status": "success",
            "message": f"找到 {len(matching_flights)} 架匹配航班",
            "search_pattern": callsign_pattern,
            "flights": matching_flights,
            "flight_count": len(matching_flights),
            "query_time": datetime.now().isoformat(),
            "data_source": "opensky_network_rest"
        }
    
    def get_airport_area_flights(self, airport_code: str) -> Dict[str, Any]:
        """获取机场区域的航班"""
        # 中国主要机场坐标（数据来源：中国开放数据平台等）
        airport_coords = {

            "PEK": (40.0801, 116.5844),  # 北京首都国际机场
            "PKX": (39.5098, 116.4107),  # 北京大兴国际机场
            "PVG": (31.1434, 121.8052),  # 上海浦东国际机场
            "SHA": (31.1979, 121.3364),  # 上海虹桥国际机场
            "CAN": (23.3925, 113.2989),  # 广州白云国际机场
            "SZX": (22.6393, 113.8107),  # 深圳宝安国际机场
            "CKG": (29.7194, 106.6419),  # 重庆江北国际机场
            "TSN": (39.1244, 117.3469),  # 天津滨海国际机场
            

            "CTU": (30.5786, 103.9472),  # 成都双流国际机场
            "TFU": (30.3114, 104.4419),  # 成都天府国际机场
            "KMG": (25.1019, 102.9292),  # 昆明长水国际机场
            "XIY": (34.4471, 108.7519),  # 西安咸阳国际机场
            "HGH": (30.2295, 120.4344),  # 杭州萧山国际机场
            "NKG": (31.7420, 118.8620),  # 南京禄口国际机场
            "WUH": (30.7838, 114.2081),  # 武汉天河国际机场
            "CSX": (28.1892, 113.2196),  # 长沙黄花国际机场
            "TAO": (36.2661, 120.3744),  # 青岛流亭国际机场
            "XMN": (24.5440, 118.1277),  # 厦门高崎国际机场
            "FOC": (25.9351, 119.6633),  # 福州长乐国际机场
            "NNG": (22.6083, 108.1722),  # 南宁吴圩国际机场
            "KWE": (26.5385, 106.8007),  # 贵阳龙洞堡国际机场
            "SJW": (38.2806, 114.6963),  # 石家庄正定国际机场
            "TYN": (37.7469, 112.6286),  # 太原武宿国际机场
            "HET": (40.8514, 111.8244),  # 呼和浩特白塔国际机场
            "SHE": (41.6398, 123.4836),  # 沈阳桃仙国际机场
            "CGQ": (43.9961, 125.6850),  # 长春龙嘉国际机场
            "HRB": (45.6234, 126.2507),  # 哈尔滨太平国际机场
            "NKQ": (25.6675, 100.2769),  # 南昌昌北国际机场（新增）
            "LHW": (34.7414, 113.8406),  # 兰州中川国际机场
            "INC": (38.8531, 106.0094),  # 银川河东国际机场
            "XNN": (36.5275, 102.0430),  # 西宁曹家堡机场
            "URC": (43.9071, 87.4744),   # 乌鲁木齐地窝堡国际机场
            

            "SYX": (18.3027, 109.4122),  # 三亚凤凰国际机场
            "HAK": (19.9349, 110.4590),  # 海口美兰国际机场
            "DLC": (38.9656, 121.5386),  # 大连周水子国际机场
            "YNT": (37.4017, 121.3717),  # 烟台蓬莱国际机场
            "WEH": (37.1871, 122.2286),  # 威海大水泊国际机场
            "JZH": (35.0286, 118.6414),  # 济南遥墙国际机场
            "LYG": (34.5714, 119.1286),  # 连云港白塔埠机场
            "YTY": (32.5631, 119.7197),  # 扬州泰州国际机场
            "WUX": (31.4944, 120.4292),  # 无锡硕放国际机场
            "NTG": (32.0708, 120.9764),  # 南通兴东国际机场
            "HFE": (31.7800, 117.2981),  # 合肥新桥国际机场
            "WNZ": (27.9122, 120.8522),  # 温州龙湾国际机场
            "NGB": (29.8267, 121.4619),  # 宁波栎社国际机场
            "YIW": (29.3447, 120.0322),  # 义乌机场
            

            "BHY": (49.2050, 119.8250),  # 北海福成机场
            "LZH": (24.2075, 109.3917),  # 柳州白莲机场
            "GXG": (24.7953, 110.0381),  # 桂林两江国际机场
            "ZUH": (22.0064, 113.3758),  # 珠海金湾机场
            "MXZ": (24.2783, 116.1222),  # 梅县机场
            "SWA": (23.5619, 116.5086),  # 汕头外砂机场
            "JYG": (24.1436, 116.6664),  # 揭阳潮汕机场
            "ZHA": (21.2144, 110.3583),  # 湛江机场
            "BAV": (23.7208, 106.9592),  # 百色巴马机场
        }
        
        if airport_code.upper() not in airport_coords:
            return {
                "status": "error",
                "message": f"不支持的机场代码: {airport_code}",
                "supported_airports": list(airport_coords.keys())
            }
        
        lat, lon = airport_coords[airport_code.upper()]
        
        # 创建机场周边边界框（约30公里范围）
        delta = 0.25  # 约30公里
        bbox = (lat - delta, lat + delta, lon - delta, lon + delta)
        
        result = self.get_all_states(bbox)
        
        if result.get("status") == "success":
            result["airport_code"] = airport_code.upper()
            result["airport_coordinates"] = {"latitude": lat, "longitude": lon}
            result["search_radius_km"] = 30
            result["message"] = f"{airport_code}机场周边找到 {result.get('flight_count', 0)} 架航班"
        
        return result


# 全局实例
simple_tracker = SimpleOpenSkyTracker()


def getFlightStatus(flight_number: str, date: str = None) -> Dict[str, Any]:
    """
    查询航班实时状态（使用OpenSky Network REST API）
    
    Args:
        flight_number: 航班号/呼号 (如: "CCA1234", "CSN5678")
        date: 日期参数（OpenSky仅支持实时数据，此参数被忽略）
        
    Returns:
        包含航班状态信息的字典
    """
    if date:
        logger.info("OpenSky仅支持实时数据，忽略date参数")
    
    return simple_tracker.search_flights_by_callsign(flight_number)


def getAirportFlights(airport_code: str, flight_type: str = "departure") -> Dict[str, Any]:
    """
    查询机场周边的航班信息
    
    Args:
        airport_code: 机场代码 (如: "PEK", "PVG", "CAN")
        flight_type: 航班类型（此参数仅为兼容性，OpenSky返回所有航班）
        
    Returns:
        包含机场周边航班列表的字典
    """
    return simple_tracker.get_airport_area_flights(airport_code)


def getFlightsInArea(min_lat: float, max_lat: float, min_lon: float, max_lon: float) -> Dict[str, Any]:
    """
    查询指定地理区域内的所有航班
    
    Args:
        min_lat: 最小纬度
        max_lat: 最大纬度
        min_lon: 最小经度 
        max_lon: 最大经度
        
    Returns:
        包含区域内航班列表的字典
    """
    bbox = (min_lat, max_lat, min_lon, max_lon)
    return simple_tracker.get_all_states(bbox)


def trackMultipleFlights(flight_numbers: List[str], date: str = None) -> Dict[str, Any]:
    """
    批量跟踪多个航班状态
    
    Args:
        flight_numbers: 航班号列表
        date: 日期参数（OpenSky仅支持实时数据）
        
    Returns:
        包含所有航班状态的字典
    """
    if date:
        logger.info("OpenSky仅支持实时数据，忽略date参数")
    
    logger.info(f"批量查询航班状态: {flight_numbers}")
    
    results = []
    for flight_number in flight_numbers:
        result = getFlightStatus(flight_number)
        results.append(result)
        time.sleep(1)  # 避免API频率限制
    
    successful_count = sum(1 for r in results if r.get("status") == "success" and r.get("flight_count", 0) > 0)
    
    return {
        "status": "success",
        "message": f"批量查询完成，共查询{len(flight_numbers)}个航班，找到{successful_count}个",
        "flight_count": len(flight_numbers),
        "found_count": successful_count,
        "results": results,
        "query_time": datetime.now().isoformat(),
        "data_source": "opensky_network_rest",
        "note": "OpenSky仅提供实时数据，无法查询历史航班信息"
    }
