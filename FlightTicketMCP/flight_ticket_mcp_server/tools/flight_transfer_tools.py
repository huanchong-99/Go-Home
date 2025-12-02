"""
Flight Transfer Tools - 航班中转查询工具

提供根据始发地、中转地、目的地查询飞机中转方案。
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
import time

from ..core.flights import FlightSchedule, FlightPrice, Flight, SeatConfiguration, FlightTransfer

# 初始化日志器
logger = logging.getLogger(__name__)


def getTransferFlightsByThreePlace(from_place: str, transfer_place: str, to_place: str,departure_date: str, min_transfer_time: float = 2.0,
                                max_transfer_time: float = 5.0) -> List[FlightTransfer]:
    """
   查询从出发地通过中转地到目的地的联程航班信息。

    Args:
        from_place (str): 出发地城市或机场
        transfer_place (str): 中转地城市或机场
        to_place (str): 目的地城市或机场
        min_transfer_time (float): 最小中转时间（单位：小时），默认 2 小时
        max_transfer_time (float): 最大中转时间（单位：小时），默认 5 小时

    Returns:
        List[str]: 符合条件的航班列表，每个航班用字典表示。
    """
    logger.info(f"开始查询中转航班...")
    logger.info(f"始发地: {from_place}，中转地：{transfer_place}， 目的地: {to_place}")

    try:
        # 获取所有城市的三字码
        from_code = _get_location_codev2(from_place)
        transfer_code = _get_location_codev2(transfer_place)
        to_code = _get_location_codev2(to_place)

        logger.info(f"三字码查询成功！始发地: {from_code}，中转地{transfer_code}， 目的地: {to_code}")

        # 获取两段行程列表
        first_trips = _get_direct_airline(from_code, transfer_code)
        after_trips = _get_direct_airline(transfer_code, to_code)
        logger.info(f"行程分段查询成功！ {from_place} - {transfer_place} {len(first_trips)}")
        logger.info(f"{transfer_place} - {to_place} {len(after_trips)}")

        # 计算换乘路线
        select_trips = []
        index=1
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
                    # 符合换乘时间要求，添加到结果列表
                    logger.info(f"符合换乘时间要求: {trip1.flight_number} {arrival_time} - {trip2.flight_number} {departure_time}")
                    transfer=FlightTransfer(
                        transfer_id=f"{index}",
                        first_flight=trip1,
                        second_flight=trip2,
                        departure_date=departure_date,
                        transfer_time=round((departure_time - arrival_time).total_seconds() / 3600,3)
                    )
                    index += 1
                    logger.info(f"添加中转航班: {transfer.first_flight.flight_number} -> {transfer.second_flight.flight_number}, 中转时间: {transfer.transfer_time}小时")
                    select_trips.append(transfer)

        logger.info(f"查询到 {len(select_trips)} 条中转航班信息")
        return select_trips
    except Exception as e:
        logger.warning(f"查询中转航班信息失败：{from_place}-{transfer_place}-{to_place}, 错误: {str(e)}", exc_info=True)


def _get_location_code(place: str) -> str:
    '''
    获取城市对应的机场三字码（IATA Code）。
    Args:
        place (str): 城市名称，例如 "北京"、"Shanghai"
    Returns:
        Optional[str]: 对应的机场三字码，如 "PEK" 或 "PVG"；如果找不到则返回 None。
    '''

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 无头模式，不打开浏览器窗口
    driver = webdriver.Chrome(options=options)
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

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 无头模式，不打开浏览器窗口
    driver = webdriver.Chrome(options=options)
    try:
        url = 'https://www.chahangxian.com/'  # 示例：百度汉语

        # 打开网页
        driver.get(url)
        time.sleep(2)

        # 输入一个字
        search_box = driver.find_element(By.CLASS_NAME, "search")

        # 百度汉语的输入框ID是kw
        input_box = search_box.find_element(By.NAME, "keyword")  # 百度汉语的输入框ID是kw
        input_box.clear()
        input_box.send_keys(place)
        input_box.send_keys(Keys.ENTER)
        time.sleep(2)
        return driver.current_url.split("/")[-2]
    except Exception as e:
        logger.warning(f"查询{place}城市三字码错误" + str(e))
    finally:
        driver.close()


def _get_direct_airline(from_code: str, to_code: str) -> list:
    '''
    :param from_code:
    :param to_code:
    :return:
    '''
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 无头模式，不打开浏览器窗口
    driver = webdriver.Chrome(options=options)
    try:
        url = f"https://www.chahangxian.com/{from_code.lower()}-{to_code.lower()}/"
        driver.get(url)
        time.sleep(1)

        tabs = driver.find_elements(By.CLASS_NAME, "J_link")  # 修改为你目标网站的内容类名
        if len(tabs) == 0:
            logger.warning(f"航班为空 {from_code}-{to_code}")
        else:
            result = []
            index=1
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
                logger.warning("没有直飞，建议转机")
            else:
                # print(len(result), result)
                return result
    except Exception as e:
        logger.warning(f"直飞查询失败 {from_code}-{to_code}" + str(e))
    finally:
        driver.close()


if __name__ == '__main__':
    # project_root = os.path.dirname(os.path.abspath(__file__))
    # sys.path.insert(0, project_root)
    print("开始查询中转航班")
    # 示例查询
    results = getTransferFlightsByThreePlace("北京", "迪拜", "维也纳")
    print(results)
