from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time
import os


def download_kontoauszuege(
    login, password, tmp_path, chrome_driver_path, url, headless=True
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
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "txtBenutzerkennung"))
        )
        userInput = driver.find_element_by_id("txtBenutzerkennung")
        userInput.send_keys(login)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "pwdPin"))
        )
        passwordInput = driver.find_element_by_id("pwdPin")
        passwordInput.send_keys(password)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "xview-anmelden"))
        )
        driver.find_element_by_id("xview-anmelden").click()

        # Navigate to Postfach
        print("Navigating to 'Postfach'...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Postfach"))
        )
        driver.find_element_by_link_text("Postfach").click()

        # Filter and select the messages to download
        # filterNachrichtenTypListe (div) -> input -> "Alle Kontoauszüge"
        print("Filtering messages...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "filterNachrichtenTypListe"))
        )
        msgTypes = driver.find_element_by_xpath(
            "//div[@id='filterNachrichtenTypListe']/input"
        )
        msgTypes.send_keys(Keys.CONTROL, "a")
        msgTypes.send_keys("Alle Kontoauszüge")
        msgTypes.send_keys(Keys.RETURN)

        # filterNachrichtenAnzahlListe (dv) -> input -> "Alle"
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "filterNachrichtenAnzahlListe"))
        )
        msgCount = driver.find_element_by_xpath(
            "//div[@id='filterNachrichtenAnzahlListe']/input"
        )
        msgCount.send_keys(Keys.CONTROL, "a")
        msgCount.send_keys("Alle")
        msgCount.send_keys(Keys.RETURN)

        # actionSuche -> click
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "actionSuche"))
        )
        driver.find_element_by_id("actionSuche").click()

        # tabellenFilterListe (div) -> input -> "Alle ungelesenen Dokumente"
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "tabellenFilterListe"))
        )
        msgFilter = driver.find_element_by_xpath(
            "//div[@id='tabellenFilterListe']/input"
        )
        msgFilter.send_keys(Keys.CONTROL, "a")
        # msgFilter.send_keys("Alle ungelesenen Dokumente")
        msgFilter.send_keys("Alle gelesenen Dokumente")
        msgFilter.send_keys(Keys.RETURN)

        # aktionsListe (div) -> input -> "Speichern"
        print("Saving messages...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "aktionsListe"))
        )
        msgSave = driver.find_element_by_xpath("//div[@id='aktionsListe']/input")
        loop_count = 0
        while loop_count < 10:
            if msgSave.is_enabled():
                loop_count = 10
            else:
                time.sleep(1)
                loop_count += 1
        msgSave.send_keys(Keys.CONTROL, "a")
        msgSave.send_keys("Speichern")
        msgSave.send_keys(Keys.RETURN)

        break_loop = False
        count = 0
        while not break_loop:
            time.sleep(1)
            for fname in os.listdir(tmp_path):
                if fname.startswith("Postfach"):
                    break_loop = True
                    file_name = fname
            count += 1
            if count > 120:
                break_loop = True
    finally:
        # Log out
        # actAbmelden
        print("Logging out...")
        driver.find_element_by_id("actAbmelden").click()
        driver.close()

    return file_name
