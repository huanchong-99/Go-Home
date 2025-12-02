"""
Date Tools - 日期工具类

提供日期相关的工具函数
"""

from datetime import datetime
from typing import Dict, Any
import logging

# 初始化日志器
logger = logging.getLogger(__name__)


class DateTools:
    """日期工具类"""
    
    @staticmethod
    def get_current_date() -> str:
        """
        获取当前日期
        
        Returns:
            str: 当前日期，格式为 yyyy-MM-dd
        """
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            logger.debug(f"获取当前日期: {current_date}")
            return current_date
        except Exception as e:
            logger.error(f"获取当前日期失败: {str(e)}", exc_info=True)
            raise e
    
    @staticmethod
    def get_current_datetime() -> str:
        """
        获取当前日期和时间
        
        Returns:
            str: 当前日期时间，格式为 yyyy-MM-dd HH:mm:ss
        """
        try:
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.debug(f"获取当前日期时间: {current_datetime}")
            return current_datetime
        except Exception as e:
            logger.error(f"获取当前日期时间失败: {str(e)}", exc_info=True)
            raise e


def getCurrentDate() -> Dict[str, Any]:
    """
    获取当前日期的工具函数
    
    Returns:
        Dict[str, Any]: 包含当前日期信息的字典
    """
    try:
        current_date = DateTools.get_current_date()
        current_datetime = DateTools.get_current_datetime()
        
        result = {
            "status": "success",
            "current_date": current_date,
            "current_datetime": current_datetime,
            "timestamp": datetime.now().timestamp(),
            "query_time": datetime.now().isoformat()
        }
        
        logger.info(f"获取当前日期成功: {current_date}")
        return result
        
    except Exception as e:
        logger.error(f"获取当前日期失败: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": f"获取当前日期失败: {str(e)}",
            "error_code": "GET_DATE_FAILED"
        } 