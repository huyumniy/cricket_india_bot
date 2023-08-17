import sys, os
import random
from random import choice
import tempfile
import gspread
import shutil
from colorama import init, Fore
import time
from selenium.webdriver.common.by import By
import undetected_chromedriver as webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = '1fiy26TXZXDWfvHQFkPD3cqlTPHsm_xCi3ySZV3O8zAk'
init(autoreset=True)  # Initialize colorama for automatic color reset

PROXY = ('proxy.packetstream.io', 31112, 'pergfan', '6ofKZOXwL7qSTGNZ')

MATCHES_TABLE = {
'Afghanistan': 
    [
        'Dharamsala',
        'Delhi', 
        'Chennai', 
        'Lucknow',
        'Mumbai',
        'Ahmedabad'
    ],
'Australia': 
    [
        'Chennai', 
        'Bangalore',
        'Lucknow',
        'Delhi',
        'Dharamsala',
        'Ahmedabad',
        'Ahmedabad',
        'Pu'
    ],
'Bangladesh':
    [
        'Dharamsala',
        'Mumbai',
        'Chennai',
        'Kolkata',
        'Pu',
        'Delhi',
    ],
'England':
    [
        'Ahmedabad',
        'Dharamsala',
        'Delhi',
        'Mumbai',
        'Bangalore',
        'Lucknow',
        'Kolkata',
        'Pu',
    ],
'ndia': [
        'Chennai',
        'Delhi',
        'Ahmedabad',
        'Pu',
        'Dharamsala',
        'Lucknow',
        'Mumbai',
        'Kolkata',
        'Bangalore'
    ],
'Netherlands': [
    'Hyderabad',
    'Dharamsala',
    'Delhi',
    'Lucknow',
    'Kolkata',
    'Pu',
    'Bangalore'
],
'New Zealand': [
    'Hyderabad',
    'Ahmedabad',
    'Dharamsala',
    'Chennai',
    'Pu',
    'Bangalore'
],
'Pakistan': [
    'Hyderabad',
    'Ahmedabad',
    'Bangalore',
    'Chennai',
    'Kolkata'
],
'South Africa': [
    'Delhi',
    'Lucknow',
    'Dharamsala',
    'Mumbai',
    'Chennai',
    'Kolkata',
    'Pu',
    'Ahmedabad'
],
'Sri Lanka': [
    'Delhi',
    'Hyderabad',
    'Lucknow',
    'Bangalore',
    'Pu',
    'Mumbai'
]
}

class ProxyExtension:
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {"scripts": ["background.js"]},
        "minimum_chrome_version": "76.0.0"
    }
    """

    background_js = """
    var config = {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: "http",
                host: "%s",
                port: %d
            },
            bypassList: ["localhost"]
        }
    };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
        callbackFn,
        { urls: ["<all_urls>"] },
        ['blocking']
    );
    """

    def __init__(self, host, port, user, password):
        self._dir = os.path.normpath(tempfile.mkdtemp())

        manifest_file = os.path.join(self._dir, "manifest.json")
        with open(manifest_file, mode="w") as f:
            f.write(self.manifest_json)

        background_js = self.background_js % (host, port, user, password)
        background_file = os.path.join(self._dir, "background.js")
        with open(background_file, mode="w") as f:
            f.write(background_js)

    @property
    def directory(self):
        return self._dir

    def __del__(self):
        shutil.rmtree(self._dir)


def selenium_connect():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    #options.add_argument("--incognito")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-site-isolation-trials")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--lang=EN')
    #pergfan:6ofKZOXwL7qSTGNZ@proxy.packetstream.io:31112
    # with open('proxies.txt', "r") as file:
    #     lines = file.readlines()

    # random_line = choice(lines)
    # random_line = random_line.strip()
    # host, port, user, password = random_line.split(":")
    # print("Host:", host)
    # print("Port:", port)
    # print("User:", user)
    # print("Password:", password)
    # proxy = (host, int(port), user, password)
    proxy_extension = ProxyExtension(*PROXY)
    options.add_argument(f"--load-extension={proxy_extension.directory}")

    prefs = {"credentials_enable_service": False,
        "profile.password_manager_enabled": False}
    options.add_experimental_option("prefs", prefs)


    # Create the WebDriver with the configured ChromeOptions
    driver = webdriver.Chrome(
        options=options,
        enable_cdp_events=True,
        
    )

    screen_width, screen_height = driver.execute_script(
        "return [window.screen.width, window.screen.height];")
    
    desired_width = int(screen_width / 2)
    desired_height = int(screen_height / 3)
    driver.set_window_position(0, 0)
    driver.set_window_size(desired_width, screen_height)
    driver.get('chrome://settings/cookies')
    input('Configured?')
    return driver


def get_data_from_google_sheets():
    try:
        # Authenticate with Google Sheets API using the credentials file
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)

            with open("token.json", "w") as token:
                token.write(creds.to_json())

        # Connect to Google Sheets API
        service = build("sheets", "v4", credentials=creds)

        # Define the range to fetch (assuming the data is in the first worksheet and starts from cell A2)
        range_name = "main!A2:B"

        # Fetch the data using batchGet
        request = service.spreadsheets().values().batchGet(spreadsheetId=SPREADSHEET_ID, ranges=[range_name])
        response = request.execute()

        # Extract the values from the response
        values = response['valueRanges'][0]['values']

        return values

    except HttpError as error:
        print(f"An HTTP error occurred: {error}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def write_error_to_file(error_message):
    with open('error_log.txt', 'a') as file:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        file.write(f'{timestamp}: {error_message}\n')


def update_processed_status(cell):
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet("main")  # Use the appropriate sheet index or title

    sheet.update(cell, 'Done')


def check_for_captcha(driver):
    while True:
        try:
            driver.find_element(By.XPATH, "//iframe[contains(@title, 'recaptcha challenge ')]")
            print_colored('WAIT', Fore.MAGENTA,  'Found captcha, waiting for 60 sec.')
            time.sleep(60)
            return True
        except: return False 


def print_colored(text, color, rest):
    print(f"{color}[{text}] {Fore.YELLOW}{rest}")


def scroll_and_click(driver, by, value, click=False):
    try:
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((by, value))
        )

        if click:
            element.click()
        return element
    except TimeoutException:
        print_colored('ERROR', Fore.RED, "Element not clickable within timeout.")
        return False
    except Exception as e:
        print_colored('ERROR', Fore.RED, "An unexpected error occured.")
        return False


def process_email(email, driver):
    global MATCHES_TABLE
    
    while True:
        try:
            while True:
                try:
                    time.sleep(1)
                    driver.get('https://www.cricketworldcup.com/register')
                    driver.find_element(By.CSS_SELECTOR, 'div[class="cookie-notice__button btn js-cookie-btn"]').click()
                    break
                except: continue
            iframe = WebDriverWait(driver, timeout=10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'iframe[class="_lpSurveyEmbed"]'))
            )
            driver.switch_to.frame(iframe)
            name = driver.find_element(By.CSS_SELECTOR,'input[class="ng-pristine ng-untouched ng-empty ng-invalid ng-invalid-required"]')
            name.send_keys('John')
            email_input = driver.find_element(By.CSS_SELECTOR, 'input[class="ng-pristine ng-untouched ng-empty ng-valid-email ng-invalid ng-invalid-required"]')
            email_input.click()
            email_input.send_keys(email)
            mm = driver.find_element(By.CSS_SELECTOR, 'input[ng-model="datetime.month"]')
            mm.click()
            mm.send_keys('01')
            dd = driver.find_element(By.CSS_SELECTOR, 'input[ng-model="datetime.day"]')
            dd.click()
            dd.send_keys('01')
            yyyy = driver.find_element(By.CSS_SELECTOR, 'input[ng-model="datetime.year"]')
            yyyy.click()
            yyyy.send_keys('1999')
            select_element = driver.find_element(By.CSS_SELECTOR, '#dropdown-8')
            dropdown = Select(select_element)
            random_index = random.randint(1, 248)
            dropdown.select_by_index(random_index)
            random_team = random.choice(list(MATCHES_TABLE.keys()))
            for city in MATCHES_TABLE[random_team]:
                driver.find_element(By.XPATH, f"//font[contains(text(), '{city}')]").click()
            driver.find_element(By.XPATH, f"//font[contains(text(), '{random_team}')]").click()

            driver.find_element(By.CSS_SELECTOR, '#consent-15').click()
            driver.find_element(By.CSS_SELECTOR, '#consent-18').click()
            driver.find_element(By.CSS_SELECTOR, '#consent-16').click()
            driver.find_element(By.CSS_SELECTOR, 'input[type="submit"][class="paging-button-submit"]').click()
            if check_for_captcha(driver): continue
            if WebDriverWait(driver, timeout=10).until(EC.url_changes(driver.current_url)): break
            else: continue
        except Exception as e:
            print_colored('ERROR', Fore.RED, 'An unexpeted error occured.')
            write_error_to_file(e)


if __name__ == "__main__":
    data = get_data_from_google_sheets()
    driver = selenium_connect()
    for row in data:
        status = row[0]
        if "done" not in status.lower():
            email = row[1]
            process_email(email, driver)
            # update_processed_status(status)
            print_colored('DONE', Fore.BLUE, email)
    print('SUCCESS', Fore.BLUE, 'All emails were processed')
