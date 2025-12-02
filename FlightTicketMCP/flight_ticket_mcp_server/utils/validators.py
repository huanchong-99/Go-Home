"""
Validators - 数据验证工具

提供各种数据验证功能
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple


def validate_email(email: str) -> bool:
    """
    验证邮箱格式
    
    Args:
        email: 邮箱地址
        
    Returns:
        bool: 是否有效
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    验证手机号格式
    
    Args:
        phone: 手机号
        
    Returns:
        bool: 是否有效
    """
    # 简化的中国手机号验证
    pattern = r'^1[3-9]\d{9}$'
    cleaned_phone = phone.replace('-', '').replace(' ', '')
    return bool(re.match(pattern, cleaned_phone))


def validate_id_number(id_number: str) -> bool:
    """
    验证身份证号格式
    
    Args:
        id_number: 身份证号
        
    Returns:
        bool: 是否有效
    """
    # 简化的身份证号验证
    pattern = r'^\d{17}[\dX]$'
    return bool(re.match(pattern, id_number.upper()))


def validate_date_format(date_str: str, format_str: str = "%Y-%m-%d") -> bool:
    """
    验证日期格式
    
    Args:
        date_str: 日期字符串
        format_str: 日期格式
        
    Returns:
        bool: 是否有效
    """
    try:
        datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        return False


def validate_airport_code(airport_code: str) -> bool:
    """
    验证机场代码格式
    
    Args:
        airport_code: 机场代码
        
    Returns:
        bool: 是否有效
    """
    # IATA机场代码通常是3个字母
    pattern = r'^[A-Z]{3}$'
    return bool(re.match(pattern, airport_code.upper()))


def validate_flight_number(flight_number: str) -> bool:
    """
    验证航班号格式
    
    Args:
        flight_number: 航班号
        
    Returns:
        bool: 是否有效
    """
    # 航班号通常是2-3个字母加数字
    pattern = r'^[A-Z]{2,3}\d{1,4}$'
    return bool(re.match(pattern, flight_number.upper()))


def validate_passenger_info(passenger_info: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    验证乘客信息的完整性和有效性
    
    Args:
        passenger_info: 乘客信息字典
        
    Returns:
        Tuple[bool, List[str]]: (是否有效, 错误信息列表)
    """
    errors = []
    required_fields = ["name", "id_number", "phone", "email"]
    
    # 检查必需字段
    for field in required_fields:
        if field not in passenger_info or not passenger_info[field]:
            errors.append(f"缺少必需字段: {field}")
    
    # 验证字段格式
    if "email" in passenger_info and passenger_info["email"]:
        if not validate_email(passenger_info["email"]):
            errors.append("邮箱格式不正确")
    
    if "phone" in passenger_info and passenger_info["phone"]:
        if not validate_phone(passenger_info["phone"]):
            errors.append("手机号格式不正确")
    
    if "id_number" in passenger_info and passenger_info["id_number"]:
        if not validate_id_number(passenger_info["id_number"]):
            errors.append("身份证号格式不正确")
    
    return len(errors) == 0, errors


def validate_booking_request(booking_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    验证预订请求数据
    
    Args:
        booking_data: 预订数据
        
    Returns:
        Tuple[bool, List[str]]: (是否有效, 错误信息列表)
    """
    errors = []
    
    # 检查必需字段
    required_fields = ["flight_id", "passenger_info"]
    for field in required_fields:
        if field not in booking_data:
            errors.append(f"缺少必需字段: {field}")
    
    # 验证乘客信息
    if "passenger_info" in booking_data:
        is_valid, passenger_errors = validate_passenger_info(booking_data["passenger_info"])
        if not is_valid:
            errors.extend(passenger_errors)
    
    # 验证舱位类型
    if "class_type" in booking_data:
        valid_classes = ["economy", "business", "first"]
        if booking_data["class_type"] not in valid_classes:
            errors.append(f"无效的舱位类型: {booking_data['class_type']}")
    
    return len(errors) == 0, errors


def sanitize_input(input_str: str) -> str:
    """
    清理输入字符串
    
    Args:
        input_str: 输入字符串
        
    Returns:
        str: 清理后的字符串
    """
    if not isinstance(input_str, str):
        return str(input_str)
    
    # 去除首尾空格
    cleaned = input_str.strip()
    
    # 去除特殊字符（根据需要调整）
    # 这里只是一个简单示例
    cleaned = re.sub(r'[<>"\']', '', cleaned)
    
    return cleaned 