"""
Flight Transfer Tools - 航班中转查询工具

提供根据始发地、中转地、目的地查询飞机中转方案。
支持 Chrome 和 Edge 浏览器（自动检测）
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import os
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
import time

from ..core.flights import FlightSchedule, FlightPrice, Flight, SeatConfiguration, FlightTransfer

# 初始化日志器
logger = logging.getLogger(__name__)

# =================== 浏览器自动检测 ===================

# 常见浏览器路径
BROWSER_PATHS = {
    'chrome': [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    ],
    'edge': [
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    ],
}

def get_available_browser_for_selenium() -> tuple:
    """
    自动检测可用的浏览器（用于 Selenium）

    优先级: Chrome > Edge

    Returns:
        tuple: (浏览器类型 'chrome'/'edge', 浏览器路径) 或 (None, None)
    """
    for browser_type, paths in BROWSER_PATHS.items():
        for path in paths:
            if os.path.exists(path):
                logger.info(f"[Selenium] 检测到可用浏览器: {browser_type} -> {path}")
                return (browser_type, path)

    logger.warning("[Selenium] 未检测到 Chrome 或 Edge 浏览器")
    return (None, None)

# 在模块加载时检测
SELENIUM_BROWSER_TYPE, SELENIUM_BROWSER_PATH = get_available_browser_for_selenium()


def create_selenium_driver():
    """
    创建 Selenium WebDriver，自动选择 Chrome 或 Edge

    Returns:
        WebDriver 实例
    """
    if SELENIUM_BROWSER_TYPE == 'chrome':
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        if SELENIUM_BROWSER_PATH:
            options.binary_location = SELENIUM_BROWSER_PATH
        logger.info(f"[Selenium] 使用 Chrome 浏览器")
        return webdriver.Chrome(options=options)

    elif SELENIUM_BROWSER_TYPE == 'edge':
        options = webdriver.EdgeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        if SELENIUM_BROWSER_PATH:
            options.binary_location = SELENIUM_BROWSER_PATH
        logger.info(f"[Selenium] 使用 Edge 浏览器")
        return webdriver.Edge(options=options)

    else:
        # 回退：尝试 Chrome（可能会失败）
        logger.warning("[Selenium] 未检测到浏览器，尝试使用默认 Chrome")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        return webdriver.Chrome(options=options)


def getTransferFlightsByThreePlace(from_place: str, transfer_place: str, to_place: str,departure_date: str = None, min_transfer_time: float = 2.0,
                                max_transfer_time: float = 5.0) -> List[FlightTransfer]:
    """
   查询从出发地通过中转地到目的地的联程航班信息。

    Args:
        from_place (str): 出发地城市或机场
        transfer_place (str): 中转地城市或机场
        to_place (str): 目的地城市或机场
        departure_date (str): 出发日期（可选）
        min_transfer_time (float): 最小中转时间（单位：小时），默认 2 小时
        max_transfer_time (float): 最大中转时间（单位：小时），默认 5 小时

    Returns:
        List[str]: 符合条件的航班列表，每个航班用字典表示。
    """
    logger.info(f"开始查询中转航班: {from_place} -> {transfer_place} -> {to_place}")

    try:
        # 获取所有城市的三字码
        from_code = _get_location_codev2(from_place)
        transfer_code = _get_location_codev2(transfer_place)
        to_code = _get_location_codev2(to_place)

        logger.info(f"三字码: {from_code} -> {transfer_code} -> {to_code}")

        # 获取两段行程列表
        first_trips = _get_direct_airline(from_code, transfer_code)
        first_trips = first_trips or []
        after_trips = _get_direct_airline(transfer_code, to_code)
        after_trips = after_trips or []

        logger.info(f"第一段航班: {len(first_trips)}, 第二段航班: {len(after_trips)}")

        # 计算换乘路线
        select_trips = []
        index = 1
        for trip1 in first_trips:
            arrival_time = trip1.schedule.arrival_time
            arrival_time = datetime.strptime(arrival_time, "%H:%M").time()
            arrival_time = datetime.combine(datetime.today(), arrival_time)
            for trip2 in after_trips:
                departure_time = trip2.schedule.departure_time
                departure_time = datetime.strptime(departure_time, "%H:%M").time()
                departure_time = datetime.combine(datetime.today(), departure_time)
                if (departure_time - arrival_time > timedelta(hours=min_transfer_time)
                        and departure_time - arrival_time < timedelta(hours=max_transfer_time)):
                    transfer = FlightTransfer(
                        transfer_id=f"{index}",
                        first_flight=trip1,
                        second_flight=trip2,
                        departure_date=departure_date,
                        transfer_time=round((departure_time - arrival_time).total_seconds() / 3600, 3)
                    )
                    index += 1
                    select_trips.append(transfer)

        logger.info(f"查询到 {len(select_trips)} 条中转航班")
        return select_trips
    except Exception as e:
        logger.error(f"查询中转航班失败: {str(e)}")
        return []


def _get_location_code(place: str) -> str:
    '''
    获取城市对应的机场三字码（IATA Code）。
    Args:
        place (str): 城市名称，例如 "北京"、"Shanghai"
    Returns:
        Optional[str]: 对应的机场三字码，如 "PEK" 或 "PVG"；如果找不到则返回 None。
    '''

    driver = create_selenium_driver()
    try:
        url = 'http://szdm.00cha.net/'

        driver.get(url)
        time.sleep(1)

        input_box = driver.find_element(By.NAME, "txtname")
        input_box.clear()
        input_box.send_keys(place)

        search_button = driver.find_element(By.ID, "btnQuery")
        search_button.click()
        time.sleep(1)

        results = driver.find_elements(By.CLASS_NAME, "tabled")
      
        code = ""
        if len(results) == 0:
            logger.warning("输入城市名错误！")
        else:
            text = results[0].text
            code_array = [line.strip().split() for line in text.strip().splitlines()][1:]
            country = code_array[0][-1]
            select_array = [item for item in code_array if item[-1] == country]
            sorted_codes = sorted(select_array, key=len)
            code = sorted_codes[0][0]
            return code[:3]
    except Exception as e:
        logger.warning(f"查询{place}城市三字码错误" + str(e))
    finally:
        driver.close()


def _get_location_codev2(place: str) -> str:
    '''
    获取城市对应的机场三字码（IATA Code）。
    Args:
        place (str): 城市名称，例如 "北京"
    Returns:
        Optional[str]: 对应的机场三字码，如 "PEK" 或 "PVG"；如果找不到则返回 None。
    '''
    driver = None
    try:
        driver = create_selenium_driver()
        url = 'https://www.chahangxian.com/'
        driver.get(url)
        time.sleep(2)

        search_box = driver.find_element(By.CLASS_NAME, "search")
        input_box = search_box.find_element(By.NAME, "keyword")
        input_box.clear()
        input_box.send_keys(place)
        input_box.send_keys(Keys.ENTER)
        time.sleep(2)
        result = driver.current_url.split("/")[-2]
        return result
    except Exception as e:
        logger.warning(f"查询{place}城市三字码错误: {str(e)}")
        return None
    finally:
        if driver:
            try:
                driver.close()
            except:
                pass


def _get_direct_airline(from_code: str, to_code: str) -> list:
    '''
    查询两地之间的直飞航班
    :param from_code: 出发地机场代码
    :param to_code: 目的地机场代码
    :return: 航班列表
    '''
    driver = None
    try:
        driver = create_selenium_driver()
        url = f"https://www.chahangxian.com/{from_code.lower()}-{to_code.lower()}/"
        driver.get(url)
        time.sleep(1)

        tabs = driver.find_elements(By.CLASS_NAME, "J_link")
        if len(tabs) == 0:
            logger.warning(f"航班为空 {from_code}-{to_code}")
            return []

        result = []
        index = 1
        for tab in tabs:
            transfer = tab.find_elements(By.CLASS_NAME, "transfer")
            if len(transfer) == 0:
                box = tab.find_element(By.CLASS_NAME, "airline-box")
                img = box.find_element(By.TAG_NAME, 'img')
                airline = img.get_attribute('alt')
                message = tab.text.splitlines()
                schedule = FlightSchedule(
                    departure_time=message[3],
                    arrival_time=message[7],
                    duration="",
                    timezone=""
                )
                mPrice = message[13].split(" ")[1].split("~")
                price = FlightPrice(
                    economy=float(mPrice[0]),
                    business=float(mPrice[-1]),
                    first=0,
                )
                flight = Flight(
                    flight_id=f"{index}",
                    flight_number=message[0],
                    airline=airline,
                    aircraft=message[1],
                    origin=message[4],
                    destination=message[8],
                    schedule=schedule,
                    price=price,
                    seat_config=SeatConfiguration(),
                    services={},
                )
                index += 1
                result.append(flight)

        if len(result) == 0:
            logger.warning(f"没有直飞航班 {from_code}-{to_code}")
        return result
    except Exception as e:
        logger.warning(f"直飞查询失败 {from_code}-{to_code}: {str(e)}")
        return []
    finally:
        if driver:
            try:
                driver.close()
            except:
                pass


if __name__ == '__main__':
    # project_root = os.path.dirname(os.path.abspath(__file__))
    # sys.path.insert(0, project_root)
    print("开始查询中转航班")
    # 示例查询
    results = getTransferFlightsByThreePlace("北京", "迪拜", "维也纳")
    print(results)
