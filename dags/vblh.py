from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time
import pendulum
import os
from pathlib import Path
import zipfile
import regex as re
import pdftotext
import json

from airflow.decorators import dag, task
from airflow.hooks.base import BaseHook


# Configuration
URL = "https://www.vblh.de/banking-private/entry"
STORAGE_BASE_PATH = Path("/storage")
TMP_PATH = Path(STORAGE_BASE_PATH, "tmp", "vblh")
ARCHIVE_PATH = Path(STORAGE_BASE_PATH, "archive", "vblh", "kontoauszuege")
CHROME_DRIVER_PATH = "/usr/local/bin/chromedriver"
CONN_ID = "vblh"

local_tz = pendulum.timezone("Europe/Berlin")
default_args = {
    "owner": "airflow",
}


@dag(
    default_args=default_args,
    schedule_interval=None,
    start_date=pendulum.datetime(2021, 1, 1, tz=local_tz),
    tags=["vblh"],
)
def vblh_kontoauszuege():
    @task()
    def download_data():
        conn = BaseHook.get_connection(CONN_ID)
        TMP_PATH.mkdir(parents=True, exist_ok=True)

        # Set up
        chrome_options = webdriver.ChromeOptions()
        prefs = {"download.default_directory": TMP_PATH.as_posix()}
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(CHROME_DRIVER_PATH, options=chrome_options)
        file_name = None

        try:
            # Open webpage
            print(f"Opening '{URL}'...")
            driver.get(URL)

            # Log in
            print("Logging in...")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "txtBenutzerkennung"))
            )
            userInput = driver.find_element_by_id("txtBenutzerkennung")
            userInput.send_keys(conn.login)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "pwdPin"))
            )
            passwordInput = driver.find_element_by_id("pwdPin")
            passwordInput.send_keys(conn.password)

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
                for fname in os.listdir(TMP_PATH):
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

        return Path(TMP_PATH, file_name).as_posix()

    @task()
    def extract_files(file_name):
        extracted_files = [
            file_name,
        ]
        if Path(file_name).suffix == ".zip":
            with zipfile.ZipFile(file_name, "r") as zip_ref:
                ARCHIVE_PATH.mkdir(parents=True, exist_ok=True)
                zip_ref.extractall(ARCHIVE_PATH)
                extracted_files = list(
                    [Path(ARCHIVE_PATH, f).as_posix() for f in zip_ref.namelist()]
                )
        else:
            f = Path(file_name)
            extracted_files = [
                f.rename(ARCHIVE_PATH / f.name).as_posix(),
            ]
        return extracted_files

    @task()
    def convert_to_json(extracted_files):
        for file in extracted_files:
            transactions = []
            year = int(re.match(r"\d+_(\d{4})_.*", Path(file).name)[1])

            with open(file, "rb") as f:
                pdf = pdftotext.PDF(f)

            pdfs = "".join(pdf)
            pdfs = re.sub(r"\n.*Übertrag auf[\s\S]*?Übertrag von.*\n", "", pdfs)
            pdfs = re.sub(r"[\s\S]*?alter Kontostand vom.*\n", "", pdfs)
            pdfs = re.sub(
                r"\n.*neuer Kontostand vom[\s\S]*", "            00.00. 00.00.", pdfs
            )

            matches = re.findall(
                r"\n\s+(\d{2}\.\d{2}\. \d{2}\.\d{2}\.[\s\S]*?)\n\s+\d{2}\.\d{2}\. \d{2}\.\d{2}\.",
                pdfs,
                overlapped=True,
            )

            for match in matches:
                tr_matches = re.match(
                    r"(\d{2})\.(\d{2})\. (\d{2})\.(\d{2})\.\s*(.*?)\s*(\d*\.*\d+),(\d+) ([HS]).*(\n(.*)\n?([\s\S]*))?",
                    match,
                )

                source = tr_matches[10]
                if not tr_matches[10]:
                    source = ""
                purpose = tr_matches[11]
                if not tr_matches[11]:
                    purpose = ""
                transaction = {
                    "booking_date": f"{year}-{tr_matches[2]}-{tr_matches[1]}",
                    "settlement_date": f"{year}-{tr_matches[4]}-{tr_matches[3]}",
                    "amount": float(f"{tr_matches[6].replace('.', '')}.{tr_matches[7]}")
                    * (-1.0 if tr_matches[8] == "S" else 1.0),
                    "source": source.strip(),
                    "type": tr_matches[5].strip(),
                    "purpose": re.sub(r"\s*\n\s*", " ", purpose).strip(),
                }
                transactions.append(transaction)

            transactions = sorted(transactions, key=lambda k: k["booking_date"])
            with open(file + ".json", "w") as f:
                json.dump(transactions, f, ensure_ascii=False, indent=4)

    file_name = download_data()
    extracted_files = extract_files(file_name)
    convert_to_json(extracted_files)
    # load_files(extracted_files)


vblh_kontoauszuege = vblh_kontoauszuege()
