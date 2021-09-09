import pendulum
from pathlib import Path
import zipfile
import regex as re
import pdftotext
import json

from airflow.decorators import dag, task
from airflow.hooks.base import BaseHook

from banking import norisbank


# Configuration
URL = "https://meine.norisbank.de/trxm/noris/"
STORAGE_BASE_PATH = Path("/storage")
TMP_PATH = Path(STORAGE_BASE_PATH, "tmp", "vblh")
ARCHIVE_PATH = Path(STORAGE_BASE_PATH, "archive", "norisbank", "kontoauszuege")
CHROME_DRIVER_PATH = "/usr/local/bin/chromedriver"
CONN_ID = "norisbank"

local_tz = pendulum.timezone("Europe/Berlin")
default_args = {
    "owner": "airflow",
}


@dag(
    default_args=default_args,
    schedule_interval=None,
    start_date=pendulum.datetime(2021, 1, 1, tz=local_tz),
    tags=["banking", "norisbank"],
)
def norisbank_umsaetze():
    @task()
    def download_data():
        conn = BaseHook.get_connection(CONN_ID)
        file_name = norisbank.download_kontoauszuege(
            conn.login, conn.password, TMP_PATH, CHROME_DRIVER_PATH, URL
        )
        return Path(TMP_PATH, file_name).as_posix()

    @task()
    def extract_files(file_name):
        # extracted_files = [
        #     file_name,
        # ]
        # if Path(file_name).suffix == ".zip":
        #     with zipfile.ZipFile(file_name, "r") as zip_ref:
        #         ARCHIVE_PATH.mkdir(parents=True, exist_ok=True)
        #         zip_ref.extractall(ARCHIVE_PATH)
        #         extracted_files = list(
        #             [Path(ARCHIVE_PATH, f).as_posix() for f in zip_ref.namelist()]
        #         )
        # else:
        #     f = Path(file_name)
        #     extracted_files = [
        #         f.rename(ARCHIVE_PATH / f.name).as_posix(),
        #     ]
        # return extracted_files
        return []

    @task()
    def convert_to_json(extracted_files):
        # for file in extracted_files:
        #     transactions = []
        #     year = int(re.match(r"\d+_(\d{4})_.*", Path(file).name)[1])

        #     with open(file, "rb") as f:
        #         pdf = pdftotext.PDF(f)

        #     pdfs = "".join(pdf)
        #     pdfs = re.sub(r"\n.*Übertrag auf[\s\S]*?Übertrag von.*\n", "", pdfs)
        #     pdfs = re.sub(r"[\s\S]*?alter Kontostand vom.*\n", "", pdfs)
        #     pdfs = re.sub(
        #         r"\n.*neuer Kontostand vom[\s\S]*", "            00.00. 00.00.", pdfs
        #     )

        #     matches = re.findall(
        #         r"\n\s+(\d{2}\.\d{2}\. \d{2}\.\d{2}\.[\s\S]*?)\n\s+\d{2}\.\d{2}\. \d{2}\.\d{2}\.",
        #         pdfs,
        #         overlapped=True,
        #     )

        #     for match in matches:
        #         tr_matches = re.match(
        #             r"(\d{2})\.(\d{2})\. (\d{2})\.(\d{2})\.\s*(.*?)\s*(\d*\.*\d+),(\d+) ([HS]).*(\n(.*)\n?([\s\S]*))?",
        #             match,
        #         )

        #         source = tr_matches[10]
        #         if not tr_matches[10]:
        #             source = ""
        #         purpose = tr_matches[11]
        #         if not tr_matches[11]:
        #             purpose = ""
        #         transaction = {
        #             "booking_date": f"{year}-{tr_matches[2]}-{tr_matches[1]}",
        #             "settlement_date": f"{year}-{tr_matches[4]}-{tr_matches[3]}",
        #             "amount": float(f"{tr_matches[6].replace('.', '')}.{tr_matches[7]}")
        #             * (-1.0 if tr_matches[8] == "S" else 1.0),
        #             "source": source.strip(),
        #             "type": tr_matches[5].strip(),
        #             "purpose": re.sub(r"\s*\n\s*", " ", purpose).strip(),
        #         }
        #         transactions.append(transaction)

        #     transactions = sorted(transactions, key=lambda k: k["booking_date"])
        #     with open(file + ".json", "w") as f:
        #         json.dump(transactions, f, ensure_ascii=False, indent=4)
        return None

    file_name = download_data()
    extracted_files = extract_files(file_name)
    convert_to_json(extracted_files)
    # load_files(extracted_files)


norisbank_umsaetze = norisbank_umsaetze()
