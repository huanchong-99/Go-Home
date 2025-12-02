"""
Date Utils - 日期处理工具

提供日期格式化、转换、计算等功能
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union
import pytz


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M") -> str:
    """
    格式化日期时间
    
    Args:
        dt: 日期时间对象
        format_str: 格式字符串
        
    Returns:
        str: 格式化后的日期时间字符串
    """
    return dt.strftime(format_str)


def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M") -> Optional[datetime]:
    """
    解析日期时间字符串
    
    Args:
        date_str: 日期时间字符串
        format_str: 格式字符串
        
    Returns:
        Optional[datetime]: 解析后的日期时间对象，失败返回None
    """
    try:
        return datetime.strptime(date_str, format_str)
    except ValueError:
        return None


def get_current_time(timezone_name: str = "Asia/Shanghai") -> datetime:
    """
    获取指定时区的当前时间
    
    Args:
        timezone_name: 时区名称
        
    Returns:
        datetime: 当前时间
    """
    tz = pytz.timezone(timezone_name)
    return datetime.now(tz)


def convert_timezone(dt: datetime, from_tz: str, to_tz: str) -> datetime:
    """
    转换时区
    
    Args:
        dt: 原始日期时间
        from_tz: 源时区
        to_tz: 目标时区
        
    Returns:
        datetime: 转换后的日期时间
    """
    from_timezone = pytz.timezone(from_tz)
    to_timezone = pytz.timezone(to_tz)
    
    # 如果dt是naive datetime，先本地化
    if dt.tzinfo is None:
        dt = from_timezone.localize(dt)
    
    return dt.astimezone(to_timezone)


def calculate_flight_duration(departure: str, arrival: str, date_format: str = "%H:%M") -> str:
    """
    计算航班飞行时长
    
    Args:
        departure: 出发时间
        arrival: 到达时间
        date_format: 时间格式
        
    Returns:
        str: 飞行时长（如：2小时30分钟）
    """
    try:
        dep_time = datetime.strptime(departure, date_format)
        arr_time = datetime.strptime(arrival, date_format)
        
        # 如果到达时间小于出发时间，说明跨天
        if arr_time < dep_time:
            arr_time += timedelta(days=1)
        
        duration = arr_time - dep_time
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        
        return f"{hours}小时{minutes}分钟"
    except ValueError:
        return "未知"


def is_valid_travel_date(date_str: str, min_advance_days: int = 1) -> bool:
    """
    验证出行日期是否有效
    
    Args:
        date_str: 日期字符串 (YYYY-MM-DD)
        min_advance_days: 最少提前天数
        
    Returns:
        bool: 是否有效
    """
    try:
        travel_date = datetime.strptime(date_str, "%Y-%m-%d")
        min_date = datetime.now() + timedelta(days=min_advance_days)
        return travel_date.date() >= min_date.date()
    except ValueError:
        return False


def get_check_in_window(departure_time: str, departure_date: str) -> dict:
    """
    获取值机时间窗口
    
    Args:
        departure_time: 出发时间 (HH:MM)
        departure_date: 出发日期 (YYYY-MM-DD)
        
    Returns:
        dict: 值机时间窗口信息
    """
    try:
        departure_dt = datetime.strptime(f"{departure_date} {departure_time}", "%Y-%m-%d %H:%M")
        
        # 值机开放时间：出发前24小时
        check_in_opens = departure_dt - timedelta(hours=24)
        
        # 值机关闭时间：出发前1小时
        check_in_closes = departure_dt - timedelta(hours=1)
        
        now = datetime.now()
        
        return {
            "opens_at": check_in_opens.isoformat(),
            "closes_at": check_in_closes.isoformat(),
            "is_open": check_in_opens <= now <= check_in_closes,
            "status": "open" if check_in_opens <= now <= check_in_closes else
                     "not_yet_open" if now < check_in_opens else "closed"
        }
    except ValueError:
        return {
            "opens_at": None,
            "closes_at": None,
            "is_open": False,
            "status": "error"
        }


def calculate_age_from_birth_date(birth_date: str) -> int:
    """
    根据出生日期计算年龄
    
    Args:
        birth_date: 出生日期 (YYYY-MM-DD)
        
    Returns:
        int: 年龄
    """
    try:
        birth_dt = datetime.strptime(birth_date, "%Y-%m-%d")
        today = datetime.now()
        age = today.year - birth_dt.year
        
        # 如果今年的生日还没到，年龄减1
        if today.month < birth_dt.month or (today.month == birth_dt.month and today.day < birth_dt.day):
            age -= 1
            
        return age
    except ValueError:
        return 0


def get_passenger_type_by_age(age: int) -> str:
    """
    根据年龄确定乘客类型
    
    Args:
        age: 年龄
        
    Returns:
        str: 乘客类型 (adult/child/infant)
    """
    if age < 2:
        return "infant"
    elif age < 12:
        return "child"
    else:
        return "adult"


def format_duration_minutes(minutes: int) -> str:
    """
    将分钟数格式化为时长字符串
    
    Args:
        minutes: 分钟数
        
    Returns:
        str: 格式化的时长
    """
    hours = minutes // 60
    mins = minutes % 60
    
    if hours > 0:
        return f"{hours}小时{mins}分钟"
    else:
        return f"{mins}分钟" 