from pathlib import *
import getpass
import argparse
import json
import sys
import datetime
import requests

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from webdriver_manager.firefox import GeckoDriverManager

HOME = Path.home()
MOODLE_CHECKER_FOLDER = HOME / '.moodle_checker'
MOODLE_CHECKER_IDENTITY = MOODLE_CHECKER_FOLDER / '.credentials.json'


def save_identity(identity_dict: dict):
    with open(MOODLE_CHECKER_IDENTITY, 'w+') as file:
        json.dump(identity_dict, file)


def install_browser():
    GeckoDriverManager().install()

    if not MOODLE_CHECKER_FOLDER.exists():
        MOODLE_CHECKER_FOLDER.mkdir()

    data = dict()
    data['username'] = str(input(f'Please enter your Moodle username : '))
    data['password'] = getpass.getpass('Please enter your Moodle password : ')
    data['groups'] = str(input('Please enter the Celcat groups you belong to (ex:4TYE901S - GROUPE TD 1, 4TYE901S - '
                               'GROUPE TD 2) : '))
    save_identity(data)


def get_key_from_dict(data: dict, key: str) -> str:
    value = data.get(key, None)

    if value is None:
        print(f"ERROR : {key} key is missing into credential file")
        sys.exit(-1)

    return value


def parse_identity(identity_path: str):
    filepath = Path(identity_path)

    if not (filepath.exists() and filepath.is_file):
        print("ERROR : Credential file provided isn't exists")
        sys.exit(-1)

    with open(filepath, 'r') as file:
        data = json.load(file)
        user = get_key_from_dict(data, 'username')
        password = get_key_from_dict(data, 'password')
        groups = get_key_from_dict(data, 'groups')
        return user, password, groups


class MoodleChecker:

    def __init__(self, user, password, groups) -> None:
        options = Options()
        options.headless = True
        self.__browser = webdriver.Firefox(executable_path=GeckoDriverManager().install(), options=options)
        self.__username = user
        self.__password = password
        self.__fedIds = [fed.strip() for fed in groups.split(',')]

    def send_presence(self) -> None:
        print(datetime.datetime.now().strftime("The %d/%m/%Y At %H:%M:%S"))
        self.__connect()

        if self.__have_course() and self.__access_course():
            self.__validate()
        else:
            self.__browser.quit()

    def __connect(self) -> None:
        print("INFO : Connection to 'https://cas.u-bordeaux.fr/cas/login'")

        self.__browser.get('https://cas.u-bordeaux.fr/cas/login')
        login_input = self.__browser.find_element_by_xpath('//*[@id="username"]')
        password_input = self.__browser.find_element_by_xpath('//*[@id="password"]')

        login_input.send_keys(self.__username)
        password_input.send_keys(self.__password)
        submit_button = self.__browser.find_element_by_xpath('//input[@type="submit" and @name="submit" and '
                                                             '@value="SE CONNECTER"]')
        submit_button.click()
        self.__browser.get('https://fad.u-bordeaux.fr/login/index.php')
        college_choice = self.__browser.find_element_by_xpath('//*[@id="userIdPSelection_iddtext"]')
        college_choice.send_keys('Université de Bordeaux')
        college_choice.send_keys(Keys.RETURN)

        print("INFO : Connected to 'https://cas.u-bordeaux.fr/cas/login'")

    def __access_course(self) -> bool:
        print("INFO : Check for avalaible courses")
        course = WebDriverWait(self.__browser, 20).until(EC.element_to_be_clickable((By.XPATH,
                                                                                     "/html/body/div[2]/div[3]/div/div[1]/section/div/aside/section[1]/div/div/div[1]/div[2]/div/div/div[1]/div/div/div/a")))
        course.click()
        element = WebDriverWait(self.__browser, 20).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[5]/div[2]/div/div/div[3]/button[1]')))
        element.click()
        self.__browser.find_element_by_xpath('//*[@id="sectionlink-6"]').click()
        classes = WebDriverWait(self.__browser, 20).until(EC.element_to_be_clickable(
            (By.XPATH, "/html/body/div[2]/div[3]/div/div[1]/section/div/div/ul/li[19]/div/ul/li[8]/div/div/a")))
        classes.click()
        try:
            self.__browser.find_element_by_partial_link_text("Envoyer le statut de présence").click()
        except NoSuchElementException:
            print("ERROR : No course avalaible")
            return False
        return True

    def __validate(self) -> None:
        print("INFO : Course found")
        self.__browser.find_element_by_xpath('//*[@id="id_status_472"]').click()
        self.__browser.find_element_by_xpath('//*[@id="id_submitbutton"]').click()
        print("INFO : Course validate")

    def __have_course(self) -> bool:
        print("INFO : Check if having course today")
        t = datetime.date.today()
        today = t.strftime("%Y-%m-%d")
        url = 'https://celcat.u-bordeaux.fr/Home/GetCalendarData'
        data = {
            'colourScheme': '3',
            'start': today,
            'end': today,
            'resType': '103',
            'calView': 'agendaDay',
            'federationIds[]': self.__fedIds
        }
        response = requests.post(url, data=data)
        now = datetime.datetime.now()
        have_course = False
        if response:
            for course in response.json():
                start = datetime.datetime.strptime(course['start'], '%Y-%m-%dT%H:%M:%S')
                end = datetime.datetime.strptime(course['end'], '%Y-%m-%dT%H:%M:%S')
                if start < now < end:
                    have_course = True
                    print("INFO : You have a course now")
                    break
        else:
            print('ERROR : Please verify the groups you have selected. By default the program will assume you have '
                  'course')
            have_course = True
        return have_course


def cli():
    print("INFO : Parsing args")

    parser = argparse.ArgumentParser(
        description='This little script allow students of work and study program from University of Bordeaux to send their presence online.',
        epilog='If credential file is not provided, --user, --password and --groups are mandatory'
    )

    parser.add_argument('--credential', help='Path to json credentials file', default=False)
    parser.add_argument('--user', help='Moodle username', default=None)
    parser.add_argument('--password', help='Moodle password', default=None)
    parser.add_argument('--groups', help='Celcat groups your belong to', default=None)
    parser.add_argument('--save', help='Save credential in settings files', action='store_true')
    args = parser.parse_args(sys.argv[1:])

    if not args.credential and not MOODLE_CHECKER_IDENTITY.exists() and (args.user is None or args.password is None
                                                                         or args.groups is None):
        parser.error('If credential file is not provided, --user, --password and --groups are mandatory')
        sys.exit(-1)

    user = None
    password = None
    groups = None

    if args.credential:
        user, password, groups = parse_identity(args.credential)
    elif not args.credential and MOODLE_CHECKER_IDENTITY.exists():
        user, password, groups = parse_identity(MOODLE_CHECKER_IDENTITY)
    else:
        user, password, groups = args.user, args.password, args.groups

    checker = MoodleChecker(user, password, groups)
    checker.send_presence()

    if args.save:
        identity = {'username': user, 'password': password, 'groups': groups}
        save_identity(identity)
