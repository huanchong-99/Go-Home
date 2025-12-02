"""
Flights - 航班数据模型

定义航班、机场、航空公司等相关数据模型
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class Airport(BaseModel):
    """机场信息模型"""
    code: str = Field(..., description="机场代码 (如: PEK, SHA)")
    name: str = Field(..., description="机场名称")
    city: str = Field(..., description="所在城市")
    country: str = Field(..., description="所在国家")
    terminals: List[str] = Field(default=[], description="航站楼列表")
    timezone: str = Field(..., description="时区")


class Airline(BaseModel):
    """航空公司信息模型"""
    code: str = Field(..., description="航空公司代码 (如: CA, MU)")
    name: str = Field(..., description="航空公司名称")
    logo_url: Optional[str] = Field(None, description="logo图片链接")


class FlightSchedule(BaseModel):
    """航班时刻表模型"""
    departure_time: str = Field(..., description="出发时间")
    arrival_time: str = Field(..., description="到达时间")
    duration: str = Field(..., description="飞行时长")
    timezone: str = Field(default="UTC+8", description="时区")


class SeatConfiguration(BaseModel):
    """座位配置模型"""
    economy: Dict[str, Any] = Field(default={}, description="经济舱配置")
    business: Dict[str, Any] = Field(default={}, description="商务舱配置")
    first: Dict[str, Any] = Field(default={}, description="头等舱配置")


class FlightPrice(BaseModel):
    """航班价格模型"""
    economy: float = Field(..., description="经济舱价格")
    business: float = Field(..., description="商务舱价格")
    first: float = Field(..., description="头等舱价格")
    currency: str = Field(default="CNY", description="货币单位")


class Flight(BaseModel):
    """航班信息模型"""
    flight_id: str = Field(..., description="航班ID")
    flight_number: str = Field(..., description="航班号")
    airline: str = Field(..., description="航空公司")
    aircraft: str = Field(..., description="机型")
    origin: str = Field(..., description="出发地机场代码")
    destination: str = Field(..., description="目的地机场代码")
    schedule: FlightSchedule = Field(..., description="时刻表")
    price: FlightPrice = Field(..., description="价格信息")
    seat_config: SeatConfiguration = Field(..., description="座位配置")
    services: Dict[str, Any] = Field(default={}, description="服务信息")
    status: str = Field(default="scheduled", description="航班状态")

class FlightTransfer(BaseModel):
    '''航班中转信息模型'''
    transfer_id: str = Field(..., description="中转ID")
    first_flight: Flight = Field(..., description="航班信息")
    second_flight: Flight = Field(..., description="中转航班信息")
    departure_date:str=Field(..., description="出发日期")
    transfer_time: float = Field(..., description="中转时间（小时）")
    

class FlightSearchCriteria(BaseModel):
    """航班搜索条件模型"""
    origin: str = Field(..., description="出发地")
    destination: str = Field(..., description="目的地")
    departure_date: str = Field(..., description="出发日期")
    return_date: Optional[str] = Field(None, description="返程日期")
    passengers: int = Field(default=1, description="乘客数量")
    class_type: str = Field(default="economy", description="舱位等级")
    max_price: Optional[float] = Field(None, description="最高价格")
    preferred_time: Optional[str] = Field(None, description="偏好时间段")


# 模拟航班数据
MOCK_AIRPORTS = {
    "PEK": Airport(
        code="PEK",
        name="北京首都国际机场",
        city="北京",
        country="中国",
        terminals=["T1", "T2", "T3"],
        timezone="UTC+8"
    ),
    "SHA": Airport(
        code="SHA",
        name="上海虹桥国际机场",
        city="上海",
        country="中国",
        terminals=["T1", "T2"],
        timezone="UTC+8"
    ),
    "CAN": Airport(
        code="CAN",
        name="广州白云国际机场",
        city="广州",
        country="中国",
        terminals=["T1", "T2"],
        timezone="UTC+8"
    )
}

MOCK_AIRLINES = {
    "CA": Airline(code="CA", name="中国国际航空"),
    "MU": Airline(code="MU", name="中国东方航空"),
    "CZ": Airline(code="CZ", name="中国南方航空")
} 