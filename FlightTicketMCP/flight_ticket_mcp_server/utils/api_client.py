"""
API Client - API客户端工具

提供HTTP请求、响应处理、错误处理等功能
"""

import requests
import json
from typing import Dict, Any, Optional, Union
from datetime import datetime
import logging


class APIClient:
    """通用API客户端类"""
    
    def __init__(self, base_url: str = "", timeout: int = 30, headers: Optional[Dict[str, str]] = None):
        """
        初始化API客户端
        
        Args:
            base_url: API基础URL
            timeout: 请求超时时间（秒）
            headers: 默认请求头
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # 设置默认请求头
        default_headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'FlightTicketMCP/1.0.0'
        }
        if headers:
            default_headers.update(headers)
        self.session.headers.update(default_headers)
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
    
    def _build_url(self, endpoint: str) -> str:
        """构建完整URL"""
        endpoint = endpoint.lstrip('/')
        return f"{self.base_url}/{endpoint}" if self.base_url else endpoint
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """处理响应"""
        try:
            response.raise_for_status()
            return {
                'success': True,
                'data': response.json() if response.content else {},
                'status_code': response.status_code,
                'headers': dict(response.headers)
            }
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP错误: {e}")
            return {
                'success': False,
                'error': str(e),
                'status_code': response.status_code,
                'data': response.text
            }
        except requests.exceptions.JSONDecodeError as e:
            self.logger.error(f"JSON解析错误: {e}")
            return {
                'success': False,
                'error': f"JSON解析错误: {str(e)}",
                'status_code': response.status_code,
                'data': response.text
            }
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """发送GET请求"""
        url = self._build_url(endpoint)
        try:
            response = self.session.get(url, params=params, timeout=self.timeout, **kwargs)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            self.logger.error(f"GET请求失败: {e}")
            return {
                'success': False,
                'error': f"请求失败: {str(e)}",
                'status_code': None
            }
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """发送POST请求"""
        url = self._build_url(endpoint)
        try:
            json_data = json.dumps(data) if data else None
            response = self.session.post(url, data=json_data, timeout=self.timeout, **kwargs)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            self.logger.error(f"POST请求失败: {e}")
            return {
                'success': False,
                'error': f"请求失败: {str(e)}",
                'status_code': None
            }
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """发送PUT请求"""
        url = self._build_url(endpoint)
        try:
            json_data = json.dumps(data) if data else None
            response = self.session.put(url, data=json_data, timeout=self.timeout, **kwargs)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            self.logger.error(f"PUT请求失败: {e}")
            return {
                'success': False,
                'error': f"请求失败: {str(e)}",
                'status_code': None
            }
    
    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发送DELETE请求"""
        url = self._build_url(endpoint)
        try:
            response = self.session.delete(url, timeout=self.timeout, **kwargs)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            self.logger.error(f"DELETE请求失败: {e}")
            return {
                'success': False,
                'error': f"请求失败: {str(e)}",
                'status_code': None
            }


class FlightAPIClient(APIClient):
    """航班API客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化航班API客户端
        
        Args:
            api_key: API密钥
        """
        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        super().__init__(
            base_url="https://api.flightapi.com/v1",  # 示例API基础URL
            headers=headers
        )
    
    def search_flights(self, origin: str, destination: str, departure_date: str, 
                      return_date: Optional[str] = None, passengers: int = 1) -> Dict[str, Any]:
        """搜索航班"""
        params = {
            'origin': origin,
            'destination': destination,
            'departure_date': departure_date,
            'passengers': passengers
        }
        if return_date:
            params['return_date'] = return_date
        
        return self.get('/flights/search', params=params)
    
    def get_flight_details(self, flight_id: str) -> Dict[str, Any]:
        """获取航班详情"""
        return self.get(f'/flights/{flight_id}')
    
    def check_flight_status(self, flight_number: str, date: str) -> Dict[str, Any]:
        """检查航班状态"""
        params = {
            'flight_number': flight_number,
            'date': date
        }
        return self.get('/flights/status', params=params)


class BookingAPIClient(APIClient):
    """预订API客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化预订API客户端
        
        Args:
            api_key: API密钥
        """
        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        super().__init__(
            base_url="https://api.bookingapi.com/v1",  # 示例API基础URL
            headers=headers
        )
    
    def create_booking(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建预订"""
        return self.post('/bookings', data=booking_data)
    
    def get_booking(self, booking_id: str) -> Dict[str, Any]:
        """获取预订信息"""
        return self.get(f'/bookings/{booking_id}')
    
    def cancel_booking(self, booking_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """取消预订"""
        data = {'reason': reason} if reason else {}
        return self.delete(f'/bookings/{booking_id}', json=data)
    
    def modify_booking(self, booking_id: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        """修改预订"""
        return self.put(f'/bookings/{booking_id}', data=changes)


def create_mock_response(status: str, data: Any, message: str = "") -> Dict[str, Any]:
    """
    创建模拟响应
    
    Args:
        status: 状态 (success/error)
        data: 响应数据
        message: 消息
        
    Returns:
        Dict[str, Any]: 模拟响应字典
    """
    return {
        'status': status,
        'data': data,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }


def format_api_error(error_response: Dict[str, Any]) -> str:
    """
    格式化API错误信息
    
    Args:
        error_response: 错误响应
        
    Returns:
        str: 格式化的错误信息
    """
    if error_response.get('success', False):
        return "操作成功"
    
    error_msg = error_response.get('error', '未知错误')
    status_code = error_response.get('status_code')
    
    if status_code:
        return f"API错误 ({status_code}): {error_msg}"
    else:
        return f"请求错误: {error_msg}" 