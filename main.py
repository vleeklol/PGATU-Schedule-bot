from io import BytesIO
from PIL import Image
from uuid import uuid4
from time import sleep, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import ClassLibrary as cl


def set_up_webdriver() -> None:
    options = Options()
    options.add_argument('--window-size=640,1280')
    options.add_experimental_option('detach', True)

    custom_driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    custom_driver.implicitly_wait(0.1)
    custom_driver.get(WEBSITE_URL)

    return custom_driver


def take_screenshot(custom_driver) -> None:
    screenshot_binary = custom_driver.find_element(by=By.ID, value='gridcontainer').screenshot_as_png
    screenshot = Image.open(BytesIO(screenshot_binary)).crop((0, 0, 574, 730))  # 594x772 is the average size of grid for 640x1280
    screenshot.save(f'Screenshots/{uuid4().hex}.png')


def click_group_select(custom_driver) -> None:
    group_select_button = custom_driver.find_element(by=By.XPATH, value='//*[@id="stream_iddiv"]/div/div[1]')
    group_select_button.click()


def click_refresh(custom_driver) -> None:
    refresh_button = custom_driver.find_element(by=By.XPATH, value='/html/body/div[3]/div/div/div[1]/div/button')
    refresh_button.click()


def get_groups_data(custom_driver) -> dict:
    groups = dict()
    dropdown_parent = custom_driver.find_element(by=By.XPATH, value='//*[@id="stream_iddiv"]/div/div[2]/div')
    dropdown_children = dropdown_parent.find_elements(By.XPATH, './/*')

    for child in dropdown_children:
        group_name = child.text
        group_name = group_name[:group_name.find('(')]
        group_id = child.get_attribute('data-value')
        groups[group_name] = cl.Group(group_name, int(group_id))
        if group_name == NEEDED_GROUP and GET_ONLY_NEEDED:
            break

    return groups


def change_group_value(custom_driver, group: cl.Group) -> None:
    try:
        change_to_value = custom_driver.find_element(by=By.XPATH, value='//*[@id="stream_id"]/option')
        custom_driver.execute_script(f"arguments[0].setAttribute('value', {group.id})", change_to_value)
    except KeyError:
        custom_driver.quit()
        raise NameError(f"{group.name} wasn't found correctly.")


def get_week_table(custom_driver) -> cl.Week:
    lecture_elements = custom_driver.find_elements(by=By.CSS_SELECTOR, value='td.lesson-lec, td.lesson-lab, td.lesson-prac')
    grid_elements = custom_driver.find_elements(by=By.CSS_SELECTOR, value='tr.noselect')

    week = cl.Week(1)

    for element in lecture_elements:
        lecture_data = element.text.split('\n')
        split_index = lecture_data[0].find(' ')
        lecture_data.insert(0, lecture_data[0][:split_index])
        lecture_data[1] = lecture_data[1][split_index+1:]

        element_index = grid_elements.index(element.find_element(by=By.XPATH, value='./..'))

        time = cl.Day.TIME_TABLE[(element_index%16)//2]

        if len(lecture_data) == 5:
            lecture_data.pop(-1)

        room, lecture_name, teacher, date = lecture_data
        
        day_index = element_index//16

        week.days[day_index].add_lecture(cl.Lecture(room, lecture_name, teacher, date, time))
    
    return week
    

def update_lectures(custom_driver, groups: dict[str: cl.Group]) -> None:
    for group in groups.values():
        change_group_value(custom_driver, group)
        click_refresh(custom_driver) 
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


sleep(0.5)
check_group = input('Enter group: ')
check_day = int(input('Day: '))


group_data[check_group].weeks[0].days[check_day].print_all_lectures()


driver.quit()