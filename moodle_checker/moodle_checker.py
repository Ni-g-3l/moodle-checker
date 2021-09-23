from pathlib import *
import argparse
import json
import sys

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from webdriver_manager.firefox import GeckoDriverManager


def install_browser():
    GeckoDriverManager().install()

def get_key_from_dict(data : dict, key : str) -> str:
    value = data.get(key, None)
    
    if value is None:
        print(f"ERROR : {key} key is missing into credential file")
        sys.exit(-1)
    
    return value

def parse_credential(credential_path : str):
    filepath = Path(credential_path)
    
    if not (filepath.exists() and filepath.is_file):
        print("ERROR : Credential file provided isn't exists")
        sys.exit(-1)

    with open(filepath, 'r') as file:
        data = json.load(file)
        user = get_key_from_dict(data, 'username')
        password = get_key_from_dict(data, 'password')
        return user, password

class MoodleChecker:

    def __init__(self, user, password) -> None:
        options = Options()
        options.headless = True
        self.__browser = webdriver.Firefox(executable_path=GeckoDriverManager().install(), options=options)
        self.__username = user
        self.__password = password

    def send_presence(self) -> None:
        self.__connect()
    
        if self.__access_course(): 
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

        self.__browser.find_element_by_xpath('/html/body/div/div/div/div[3]/form/div/div[1]/div[3]/input[3]').click()
        
        self.__browser.get('https://fad.u-bordeaux.fr/login/index.php')
        college_choice = self.__browser.find_element_by_xpath('//*[@id="userIdPSelection_iddtext"]')
        college_choice.send_keys('Université de Bordeaux')
        college_choice.send_keys(Keys.RETURN)

        print("INFO : Connected to 'https://cas.u-bordeaux.fr/cas/login'")

    def __access_course(self) -> bool:
        print("INFO : Check for avalaible courses")
        course = WebDriverWait(self.__browser, 20).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[3]/div/div[1]/section/div/aside/section[1]/div/div/div[1]/div[2]/div/div/div[1]/div/div/div/a")))
        course.click()
        element = WebDriverWait(self.__browser, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[5]/div[2]/div/div/div[3]/button[1]')))
        element.click()
        self.__browser.find_element_by_xpath('//*[@id="sectionlink-6"]').click()
        classes = WebDriverWait(self.__browser, 20).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[3]/div/div[1]/section/div/div/ul/li[19]/div/ul/li[8]/div/div/a")))
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


def cli():
    print("INFO : Parsing args")
    
    parser = argparse.ArgumentParser(
        description='This little script allow students of work and study program from University of Bordeaux to send their presence online.',
        epilog='If not credential file provided, --user and --password are mandatory'
    )

    parser.add_argument('--credential', help='Path to json credentials file', default=False)
    parser.add_argument('--user', help='Moodle username', default=None)
    parser.add_argument('--password', help='Moodle password', default=None)
    args = parser.parse_args(sys.argv[1:])

    if not args.credential and (args.user is None and args.password is None):
        parser.error('If credential file is not provided, --user and --password are mandatory')
        sys.exit(-1)

    user = None
    password = None

    if args.credential:
        user, password = parse_credential(args.credential)
    else:
        user, password = args.user, args.password

    checker = MoodleChecker(user, password)
    checker.send_presence()

