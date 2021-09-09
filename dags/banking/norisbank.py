from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select
import time
import os


def download_kontoauszuege(
    login,
    password,
    tmp_path,
    chrome_driver_path,
    url,
    headless=True,
    logout=True,
    keep_open=False,
):
    tmp_path.mkdir(parents=True, exist_ok=True)

    # Set up
    chrome_options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": tmp_path.as_posix()}
    chrome_options.add_experimental_option("prefs", prefs)
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(chrome_driver_path, options=chrome_options)
    file_name = None

    try:
        # Open webpage
        print(f"Opening '{url}'...")
        driver.get(url)

        # Log in
        print("Logging in...")
        branch = login.split("/")[0]
        account = login.split("/")[1]
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "branch"))
        )
        driver.find_element_by_id("branch").send_keys(branch)
        time.sleep(0.5)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "account"))
        )
        driver.find_element_by_id("account").send_keys(account)
        time.sleep(0.5)

        # WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "subAccount")))
        # driver.find_element_by_id("subAccount").send_keys("00")
        # time.sleep(1)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "pin")))
        driver.find_element_by_id("pin").send_keys("6hX1r")
        time.sleep(0.5)

        select = Select(
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "proxyLogins"))
            )
        )
        # select.select_by_value("setupNachrichtenbox")
        select.select_by_value("DisplayTransactions")
        time.sleep(0.5)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "action"))
        )
        driver.find_element_by_xpath("//td[@id='action']/input").click()
        time.sleep(2)

        # id=displayNachrichtenBoxForm
        # name=readAll
        # input value=Weiter
        if len(driver.find_elements_by_id("displayNachrichtenboxForm")) > 0:
            print("Found unread messages, marking as read...")
            driver.find_element_by_name("readAll").click()
            driver.find_element_by_css_selector(".button.nextStep").click()
            time.sleep(0.5)

        # id=periodStartDay
        # id=periodStartMonth
        # id=periodStartYear
        # id=periodEndDay
        # id=periodEndMonth
        # id=periodEndYear
        # value=Anzeige aktualisieren
        # ds und next_ds
        # text=Diese Seite als CSV-Datei speichern
        # Kontoumsaetze_431_437267800_20210909_164312.csv
        print("Setting transaction period...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "periodStartDay"))
        ).send_keys("01")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "periodStartMonth"))
        ).send_keys("09")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "periodStartYear"))
        ).send_keys("2021")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@value='Anzeige aktualisieren']")
            )
        ).click()
        time.sleep(1)

        print("Saving csv")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//li[@class='csv']/a"))
        ).click()

        break_loop = False
        count = 0
        while not break_loop:
            time.sleep(1)
            for fname in os.listdir(tmp_path):
                if fname.startswith("Kontoumsaetze_431_437267800"):
                    break_loop = True
                    file_name = fname
            count += 1
            if count > 120:
                break_loop = True

    finally:
        # Log out
        if logout:
            print("Logging out...")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//li[@class='logout']/a"))
            ).click()
        time.sleep(1)

        if not keep_open:
            driver.close()

    return file_name
