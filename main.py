import os
import sys
import time
import shutil
import logging
import requests
from typing import Dict
from pathlib import Path
import pyinputplus as pyip
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException

# Download a file with a delay of 3 seconds to no go over
# the omnivox rate limit, because if we download the files too
# fast omnivox will cut the connection
def download(_session, folder, url, _i):
    time.sleep(3)

    response = _session.get(url, headers=HEADERS)
    try:
        filename = response.headers["content-disposition"].split('"')[1]
    except:
        print("DOWNLOAD OF THIS FILE FAILED")
        print(response.status_code)
        print(response.reason)
        print(response.content)
        print(response.headers)
    content = response.content
    # Save the content to a file or process it as needed
    with open(folder + "\\" + filename, "wb") as f:
        f.write(content)
    response.close()


# Go through each folder and download each file in the list and place
# them in the folder
def download_everything(_allfolders_links: dict, session):
    index_file = 0
    total_files = sum([len(array) for array in _allfolders_links.values()])
    start_time = time.time()

    for folder, links_array in _allfolders_links.items():
        for link in links_array:
            download(session, folder, link, index_file)
            index_file += 1
            delta_time = time.time() - start_time
            slope = delta_time / index_file
            time_left = (total_files - index_file) * slope
            minutes = time_left // 60
            seconds = time_left % 60
            print(
                (str(index_file) + "/" + str(total_files)).center(11),
                "   -   ",
                str(round(100 * index_file / total_files, 1)).center(6),
                "%   -   Time left: ",
                str(int(minutes)).center(4),
                "minutes and",
                str(int(seconds)).center(4),
                "seconds left",
                end="\r",
                flush=True,
            )
    print("\n")
    documents_path = Path(".\documents")
    print(
        "FINISHED DOWNLOADING THE FILES! Absolute Folder Path:",
        documents_path.absolute(),
    )


def make_valid_path(path):
    # Replace invalid characters with valid ones
    valid_chars = "-_.() %s%s" % (os.sep, os.sep)
    valid_path = "".join(c if c.isalnum() or c in valid_chars else "_" for c in path)

    # Remove leading/trailing whitespace and dots
    valid_path = valid_path.strip(". ")

    # Add a prefix or suffix if the path is empty after modifications
    if not valid_path:
        valid_path = "invalid_path"

    return valid_path


def create_folder_if_not_exist(newpath: str):
    if not os.path.exists(newpath):
        os.makedirs(newpath)

def stalenessOf(element):
  try:
    element.is_enabled()
    return False
  except:
    return True 

def click_button(button):
    driver.execute_script("arguments[0].click();", button)
    time.sleep(0.5)


def get_valid_input(nb: int):
    userChoice = 0
    while userChoice < 1 or userChoice > nb:
        try:
            userChoice = int(input(f"Please choose a number between 1 and {nb} > "))
        except ValueError:
            print("We expect you to enter a valid integer")
    return userChoice


def handle_2fa():
    message = driver.find_element(
        By.XPATH, "/html/body/div[2]/div/main/div/div/div/div[1]"
    ).text
    code_field = driver.find_element(By.ID, ":r1:")
    submit_button = driver.find_element(
        By.XPATH, "/html/body/div[2]/div/main/div/div/div/div[last()]/div/button"
    )
    another_method_button = driver.find_element(
        By.XPATH, "/html/body/div[2]/div/main/div/div/div/div[last()-2]/a"
    )
    resend_button = None

    try:
        resend_button = driver.find_element(
            By.XPATH, "/html/body/div[2]/div/main/div/div/div/div[last()-3]/button"
        )
    except:
        pass

    choices = 2
    print(message)
    print("1) Enter the code")
    print("2) Validate my identity using another method")
    if resend_button is not None:
        print("3) Resend")
        choices = 3
    print()
    user_choice = pyip.inputInt(min=1, max=choices) #get_valid_input(choices)
    if user_choice == 1:
        code = pyip.inputInt("ENTER THE RECEIVED CODE> ", min=0)
        code_field.send_keys(code)
        click_button(submit_button)
        if not stalenessOf(code_field):# code_field.get_attribute("aria-invalid"):
            print("The code you entered is INCORRECT.")
            handle_2fa()
    elif user_choice == 2:
        click_button(another_method_button)
        list_options = driver.find_elements(By.CSS_SELECTOR, "a>div>div>div>p")
        for idx,option in enumerate(list_options):
            print(f"{idx+1}) {option.text}")
        while True:
            choice = pyip.inputInt("Choose a method> ", min=1, max=len(list_options)+1)
            click_button(list_options[choice-1])
            if stalenessOf(list_options[0]):
                break
            print("It's not working, try something else...")
            click_button(driver.find_element(By.XPATH, "/html/body/div[3]/div[3]/div/div[2]/button"))
        handle_2fa()
    else:
        click_button(resend_button)
        click_button(code_field)
        handle_2fa()

# HEADERS USED TO DOWNLOAD FILES FROM OMNIVOX
HEADERS = {
    "method": "GET",
    "scheme": "https",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "fr-CA",
    "dnt": "1",
    "sec-ch-ua": '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
}
PRINT_TREE = False

# Selenium driver
driver = None
# try:
# Remove the backtrace in case python crashes
# sys.tracebacklimit = 0

print(" CTR + C TO EXIT THE SCRIPT ".center(70, "="))
print(
    " IF YOU THE STUDENT NUMBER OR THE STUDENT PASSWORD ARE INCORRECT ".center(70, "=")
)
print(
    " THE SCRIPT WILL CRASH AND YOU WILL HAVE TO START THE PROGRAM AGAIN ".center(
        70, "="
    )
)
print()

# Getting the cegep, because the login url changes
print("1) Vanier")
print("2) Rosemont")
college_choice = pyip.inputInt(min=1,max=2, prompt="Choose your college> ")
match college_choice:
    case 1:
        LOGIN_URL = "https://vaniercollege.omnivox.ca/Login/Account/Login"
    case 2:
        LOGIN_URL = "https://crosemont.omnivox.ca/Login/Account/Login"

# Getting the student number
STUDENT_NO = pyip.inputInt(min=0, prompt="STUDENT ID> ")

# Getting the student password
STUDENT_PASSWD = pyip.inputPassword(prompt="STUDENT PASSWORD> ")

base_folder_documents = ".\documents"
if os.path.exists(base_folder_documents):
    shutil.rmtree(base_folder_documents)
create_folder_if_not_exist(base_folder_documents)

# Options for chrome webdriver
options = Options()
# options.add_argument("--headless")
# options.add_argument("--log-level=3")
# options.add_argument("--disable-logging")
# options.add_argument("--disable-dev-tools")
# options.add_argument("--disable-extensions")
# options.add_argument("--disable-dev-shm-usage")
# options.add_argument("--remote-debugging-port=0")
# options.add_experimental_option("excludeSwitches", ["enable-automation"])
# options.add_experimental_option("useAutomationExtension", False)

# os.environ["WDM_LOG"] = "false"

logger = logging.getLogger("selenium.webdriver.remote.remote_connection")
logger.setLevel(logging.WARNING)

# DriverManager will download chrome driver in case it's not downloaded in the host machine
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options,
    service_log_path=os.devnull,
)
driver.implicitly_wait(2)

print()

# Storing the url for each folder created to download the files later
all_folders_links: Dict[str, list] = {}
print("Retrieving URLs to download files ...")

# Go to the login page
driver.get(LOGIN_URL)
# Find the student number field
studNum = driver.find_element(By.NAME, "NoDA")
# Find the student password field
studPass = driver.find_element(By.NAME, "PasswordEtu")
# Find the login button
loginBut = driver.find_element(
    By.XPATH, "/html/body/div[2]/div[2]/div/div/div[2]/form/div[4]/div/button"
)

# Fill in the student number
studNum.send_keys(STUDENT_NO)
# Fill in the student password
studPass.send_keys(STUDENT_PASSWD)
# Clicking on the login button
click_button(loginBut)

if "/mfa/" in driver.current_url: #works for vanier not sure for other colleges
    handle_2fa()

# Trying to find on the lea button
# If the button is not found, this means that the login page failed and
# the student number of password isn't correct
try:
    lea_button = driver.find_element(
        By.CSS_SELECTOR,
        ".raccourci.id-service_CVIE.code-groupe_lea",
    )
except NoSuchElementException as e:
    print()
    print("YOUR STUDENT NUMBER OR PASSWORD ISN'T CORRECT!")
    print("START THE PROGRAM AGAIN")
    raise ValueError()

# Clicking on the lea button
driver.execute_script("arguments[0].click();", lea_button)
# Find each course pannel on the lea page
coursesPanel = driver.find_elements(By.CSS_SELECTOR, ".card-panel.section-spacing")

# Storing the id of the current window to comeback to it later
original_window = driver.current_window_handle

# For each course the driver will go through each table and get all the urls
for coursePanel in coursesPanel:
    # Get the name of the course
    courseName = coursePanel.find_element(By.CLASS_NAME, "card-panel-title").text
    if PRINT_TREE:
        print("- " + repr(courseName))

    # Create the folder for that course
    course_base_folder_documents = "." + make_valid_path(
        base_folder_documents + "\\" + courseName
    )
    create_folder_if_not_exist(course_base_folder_documents)

    all_folders_links[course_base_folder_documents] = []

    # Finding the link for the documents page of the course
    link = coursePanel.find_element(
        By.CSS_SELECTOR, "div.card-panel-content > a:nth-child(2)"
    ).get_attribute("href")
    # Creating a new tab for the documents page of that course
    driver.switch_to.new_window("tab")
    driver.get(link)

    # Finding all the tables inside the documents page
    tables = driver.find_elements(
        By.CSS_SELECTOR, ".CategorieDocument.CategorieDocumentEtudiant"
    )
    if PRINT_TREE:
        print("TABLES:")

    # For each table in the documents page go through each row to find the links
    for table in tables:
        # Finding the name of the table
        tableName = table.find_element(By.CSS_SELECTOR, ".DisDoc_TitreCategorie").text
        if PRINT_TREE:
            print("  * " + repr(tableName))
        sub_section_folder = "." + make_valid_path(
            course_base_folder_documents + "\\" + tableName
        )
        # Creating a folder for the table
        create_folder_if_not_exist(sub_section_folder)
        all_folders_links[sub_section_folder] = []
        rows = table.find_elements(By.CSS_SELECTOR, "tr:not(:last-child)")

        # For each row in the table figure out if it's a simple document or a sub-table
        for row in rows:
            # Link element of the row
            download_element = row.find_element(
                By.CSS_SELECTOR,
                ".lblDescriptionDocumentDansListe.colVoirTelecharger > a",
            )

            # If the link element is a simple file add the file link to the list of this folder
            # if the element is downloable
            if download_element.get_attribute("target"):
                all_folders_links[sub_section_folder].append(
                    download_element.get_attribute("href")
                )
            # If the link element is a sub-table then click on it and add each link to the list
            # of this folder if the element is downloable
            elif not download_element.get_attribute("title"):
                driver.execute_script("arguments[0].click();", download_element)
                subTableName = row.find_element(
                    By.CLASS_NAME, "lblTitreDocumentDansListe"
                ).text
                if PRINT_TREE:
                    print("    * " + subTableName)
                sub_sub_section_folder = "." + make_valid_path(
                    sub_section_folder + "\\" + subTableName
                )
                create_folder_if_not_exist(sub_sub_section_folder)
                all_folders_links[sub_sub_section_folder] = []
                driver.switch_to.frame("iframePopup")
                popupTable = driver.find_element(By.ID, "TableLayoutTopPopup")
                popupRows = popupTable.find_elements(
                    By.CSS_SELECTOR,
                    "td.BoiteCVIRReguliere>table>tbody>tr:not(:first-child)",
                )
                iframe_url = driver.execute_script("return document.location.href")
                for popupRow in popupRows:
                    onclik = popupRow.get_attribute("onclick")
                    partialURL = ""
                    if onclik.split("(")[0] == "TelechargerFichier":
                        all_folders_links[sub_sub_section_folder].append(
                            iframe_url
                            + "&NomFichier="
                            + quote(onclik.split("'")[1], safe="~()*!'")
                        )
                    elif onclik.split("(")[0] == "VisualiseVideo":
                        all_folders_links[sub_sub_section_folder].append(
                            iframe_url + "&" + onclik.split("&")[-1].split("'")[0]
                        )
                driver.switch_to.default_content()
    driver.close()
    driver.switch_to.window(original_window)
# Create a requests session with all the good cookies to be able to download the files
session_requests = requests.Session()
for cookie in driver.get_cookies():
    session_requests.cookies.set(cookie["name"], cookie["value"])
print("\nDownloading the files and placing them in their respective folders ...")
# Pass the dict with all the links related to a folder, download them and place them
# in the correct folder
download_everything(all_folders_links, session_requests)
# except Exception as e:
#     print(e)
# finally:
if driver:
    driver.quit()
# Input to not exit of the program directly
input()
