import click
import ujson
from typing import Dict, List

import gspread
from munch import Munch
from oauth2client.service_account import ServiceAccountCredentials
from tangerine import TangerineClient, DictionaryBasedSecretProvider


# Tangerine
tangerine_client = None

# GDrive
gdrive_scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
gdrive_client = None


# Config
config = None


def get_accounts() -> Dict[str, Dict]:
    info("Getting accounts")
    accounts = tangerine_client.list_accounts()
    mutual_fund_accounts = {}
    for account in accounts:
        if account['type'] != "MUTUAL_FUND":
            continue
        mutual_fund_accounts[account['display_name']] = tangerine_client.get_account(account['number'])

    info(f"Found {len(mutual_fund_accounts)} accounts")
    return mutual_fund_accounts


def process_data(accounts: Dict[str, Dict]):
    info(f"Getting spreadsheet {config.sheet_id}")
    spreadsheet = gdrive_client.open_by_key(config.sheet_id)
    mapping = config.mapping

    for account_id, sheet_name in mapping.items():
        account_sheet = spreadsheet.worksheet(sheet_name)
        account = accounts[account_id]

        data = Munch(account['mutual_fund']['holdings'][0])

        info(f"Processing account {account['display_name']}")

        date = data.as_of_date
        unit_price = data.unit_price
        units = data.units
        market_value = data.market_value
        book_value = data.book_value
        avg_unit_price = book_value / units
        diff = market_value - book_value

        values = [date, unit_price, units, market_value, book_value, avg_unit_price, diff]

        try:
            found_date = account_sheet.find(date)
            info(f"Row {date} already exists, replacing", color="yellow")
            account_sheet.delete_row(found_date.row)
            account_sheet.insert_row(values, index=found_date.row)
        except gspread.CellNotFound:
            info(f"Adding new row for {date}")
            account_sheet.append_row(values)


def run():
    info("Login to Tangerine")
    with tangerine_client.login():
        accounts = get_accounts()

    process_data(accounts)


def info(message: str, color: str = "blue"):
    click.secho(message, fg=color)


if __name__ == '__main__':
    info("Loading config file")
    with open("config.json", mode="r") as config_file:
        config = Munch(ujson.loads(config_file.read()))

    info("Loading credentials")
    with open("credentials.json", mode="r") as credentials_file:
        credentials = ujson.loads(credentials_file.read())

    info("Initializing Tangerine client")
    secret_provider = DictionaryBasedSecretProvider(credentials)
    tangerine_client = TangerineClient(secret_provider)

    info("Initializing Google Sheet client")
    gdrive_credentials = ServiceAccountCredentials.from_json_keyfile_name("client_secret.json", gdrive_scope)
    gdrive_client = gspread.authorize(gdrive_credentials)

    info("Starting import")
    run()
