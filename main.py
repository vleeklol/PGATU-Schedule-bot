import os
import telebot
from time import sleep

from io import BytesIO
from PIL import Image
from uuid import uuid4
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import ClassLibrary as cl


def set_up_webdriver() -> webdriver:
    """
    Function used to setup selenium webdriver with needed options and arguments.

    Returns:
        selenum.webdriver: Driver that handles webpages.
    """
    options = Options()
    options.add_argument('--window-size=640,1280')
    options.add_experimental_option('detach', True)

    custom_driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    custom_driver.implicitly_wait(0.1)
    custom_driver.get(WEBSITE_URL)

    return custom_driver


def take_screenshot(custom_driver) -> None:
    """
    Takes a screenshot with resolution of 574x730.

    Args:
        custom_driver (selenium.webdriver): Driver that handles webpages.
    """
    screenshot_binary = custom_driver.find_element(by=By.ID, value='gridcontainer').screenshot_as_png
    screenshot = Image.open(BytesIO(screenshot_binary)).crop((0, 0, 574, 730))  # 594x772 is the average size of grid for 640x1280
    screenshot.save(f'Screenshots/{uuid4().hex}.png')


def click_group_select(custom_driver) -> None:
    """
    Finds a group select button and clicks it.

    Args:
        custom_driver (selenium.webdriver): Driver that handles webpages.
    """
    group_select_button = custom_driver.find_element(by=By.XPATH, value='//*[@id="stream_iddiv"]/div/div[1]')
    group_select_button.click()


def click_refresh(custom_driver) -> None:
    """
    Finds a refresh button and clicks it.

    Args:
        custom_driver (selenium.webdriver): Driver that handles webpages.
    """
    refresh_button = custom_driver.find_element(by=By.XPATH, value='/html/body/div[3]/div/div/div[1]/div/button')
    refresh_button.click()


def get_groups_data(custom_driver) -> dict:
    """
    Function that goes through all present groups in the website to store them in a dictionary.

    Args:
        custom_driver (selenium.webdriver): Driver that handles webpages.

    Returns:
        dict: Dictionary of groups with a format of {'name': ClassLibrary.Group}
    """
    groups = dict()
    dropdown_elements = custom_driver.find_elements(by=By.XPATH, value='//*[@id="stream_iddiv"]/div/div[2]/div/*')

    for element in dropdown_elements:
        group_name = element.text
        group_name = group_name[:group_name.find('(')]
        group_id = element.get_attribute('data-value')
        groups[group_name] = cl.Group(group_name, int(group_id))
        if group_name == NEEDED_GROUP and GET_ONLY_NEEDED:
            break

    return groups


def change_group_value(custom_driver, group: cl.Group) -> None:
    """
    Finds a value element in HTML code, then changes it to the needed ID.

    Args:
        custom_driver (selenium.webdriver): Driver that handles webpages.
        group (ClassLibrary.Group): Group that we are changing value element to.

    Raises:
        KeyError: If group wasn't found. (Usually a typo in input.)
    """
    try:
        change_to_value = custom_driver.find_element(by=By.XPATH, value='//*[@id="stream_id"]/option')
        custom_driver.execute_script(f"arguments[0].setAttribute('value', {group.id})", change_to_value)
    except KeyError:
        custom_driver.quit()
        raise NameError(f"{group.name} wasn't found correctly.")


def get_week_table(custom_driver) -> cl.Week:
    """
    This function finds all lectures in schedule for currently selected group by webdriver.
    Outputs whole week full of lectures.

    Args:
        custom_driver (selenium.webdriver): Driver that handles webpages.
    
    Returns:
        ClassLibrary.Week: Week with whole schedule.
    """

    lecture_elements = custom_driver.find_elements(by=By.CSS_SELECTOR, value='td.lesson-lec, td.lesson-lab, td.lesson-prac')

    # There are 8 possible lectures in one day. Lectures can split into odd week's and even week's lectures.
    # So there is a total of 16 grid elements for one day, 112 elements in one week.
    grid_elements = custom_driver.find_elements(by=By.CSS_SELECTOR, value='tr.noselect')

    # We can get index of a week by checking an element with value of 'Текущая неделя: 1'.
    week_index = int(custom_driver.find_element(by=By.XPATH, value='/html/body/div[3]/div/div/h4').text[-1])
    week = cl.Week(week_index)

    for element in lecture_elements:
        lecture_data = element.text.split('\n')
        split_index = lecture_data[0].find(' ')
        lecture_data.insert(0, lecture_data[0][:split_index])
        lecture_data[1] = lecture_data[1][split_index+1:]

        element_index = grid_elements.index(element.find_element(by=By.XPATH, value='./..'))

        # Each two grid places represent one time.
        # First and second place means that lecture will start at 8:30
        # Third and fourth - 10:10, and so on.
        time = cl.Day.TIME_TABLE[(element_index%16)//2]

        # If there's a fifth element, it's always 'Ещё занятия'.
        # We can get rid of that for now.
        if len(lecture_data) == 5:
            lecture_data.pop(-1)

        room, lecture_name, teacher, date = lecture_data
        
        day_index = element_index//16

        week.days[day_index].add_lecture(cl.Lecture(room, lecture_name, teacher, date, time))
    
    return week
    

def update_lectures(custom_driver, groups: dict[str: cl.Group]) -> None:
    """
    Updates a dictionary of groups so that every group has a full schedule.
    Usually takes around 3-5 minutes to complete.

    Args:
        custom_driver (selenium.webdriver): Driver that handles webpages.
        groups (dict[str: ClassLibrary.Group]): Dictionary that contains all groups.
    """
    for group in groups.values():
        change_group_value(custom_driver, group)
        click_refresh(custom_driver) 

        # There has to be atleast half a second to make sure that website has updated.
        sleep(0.5)

        week = get_week_table(custom_driver)
        group.weeks.append(week)


WEBSITE_URL = 'http://shedule.psaa.ru/'
NEEDED_GROUP = 'ПИНб-1'
NEED_SCREENSHOT = False
GET_ONLY_NEEDED = False


driver = set_up_webdriver()
click_group_select(driver)
group_data: dict = get_groups_data(driver)
update_lectures(driver, group_data)

if NEED_SCREENSHOT:
    take_screenshot(driver)

driver.quit()