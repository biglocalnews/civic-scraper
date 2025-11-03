"""
This file creates the basis for the test configuration JSON file for the tests by filtering the main_meeting_list Google Sheet.


Example test configuration JSON structure:
    "fl-sarasotacounty": {
                "state": "FL",
                "place": "Sarasota County",
                "platform": "granicus",
                "url": "https://sarasotacounty.granicus.com/ViewPublisher.php?view_id=51",
                "committees": [
                    "County Commissioners"
                ],
                "start_date": "2025-01-01"

"""

from argparse import ArgumentParser
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
import os

site_list = [
    "Unknown",
    "Granicus",
    "CivicPlus",
    "Legistar",
    "CivicClerk",
    "BoardDocs",
    "Wordpress Plugin",
    "Simbli",
    "Municode",
    "iCompass",
    "Google Docs",
    "eScribe",
    "OnBase",
    "BoardBook",
    "PrimeGov",
    "SharePoint",
    "Laserfiche",
    "towncloud.io",
    "TechShare",
    "ParentSquare",
    "OAgendas",
    "EduPortal",
    "Documents on Demand",
    "CivAssist",
    "Champ",
    "AgendaSuite",
    "AgendaQuick",
    "AgendaNet",
]


def authenticate(service_account_file) -> service_account.Credentials:
    """
    Authenticates the user and sets up the Sheets API service.
    Returns the authenticated service or None if an error occurs.

    Inputs:
        service_account_file (PosixPath): Path to the service account credentials JSON file

    Returns: service (service_account.Credentials) Google Service Account Credentials or None, if the service is not authenticated
    """
    try:
        # Load credentials from the token file and create a Sheets API service
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file
        )
        service = build("sheets", "v4", credentials=credentials)

        return service
    except Exception as e:
        # Log an error message if authentication fails
        print(f"Failed to authenticate: {e}")
        return None


def read_data_from_spreadsheet(service, spreadsheet_id, range_name) -> list:
    """
    Fetches data from a specified Google Sheet.

    Args:
        service: Authenticated Sheets API service instance.
        spreadsheet_id: The ID of the spreadsheet to fetch data from.
        range_name: The range of cells to retrieve (e.g., 'Sheet1!A1:D10').

    Returns:
        sheet_values (list): list containing the Google sheet data.
    """
    try:
        # create a Sheets API service
        sheet = service.spreadsheets()
        result = (
            sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        )
        # extract the values from the result
        sheet_values = result.get("values", [])

        # check if any data was found, print info message if not
        if not sheet_values:
            print("No data found in the specified range.")
            return None
        return sheet_values
    except Exception as e:
        print(f"Error fetching sheet data: {e}")
        return {}


def clean_and_structure_data(sheet_data: list, vendor: str) -> dict:
    """
    This function cleans and structures the raw sheet data into the config.json format

    Inputs:
        sheet_data (list): list containing the Google sheet data by sheet
        vendor (str): vendor name to filter the data by (e.g., "granicus")

    Returns:
        config (dict): dictionary containing the cleaned and structured data for the config.json file
    """
    # convert the sheet data to a pandas dataframe
    dataframe = pd.DataFrame(sheet_data[1:], columns=sheet_data[0])

    # Filter to only rows where the vendor is "vendor"
    filtered_df = dataframe[dataframe["Vendor"].str.lower() == vendor.lower()]

    # create place column based on city and county, combine if both exist else use one that exists (either city or county)
    filtered_df["Place"] = filtered_df.apply(
        lambda row: (
            f"{row['City'].strip()} County"
            if pd.notna(row["City"]) and pd.notna(row["County"])
            else (
                row["City"].strip() if pd.notna(row["City"]) else row["County"].strip()
            )
        ),
        axis=1,
    )

    # create committees list base don the government agency
    # to create the committee column remove the city, county name from government agency
    filtered_df["Committee"] = filtered_df.apply(
        lambda row: row["Government agency"]
        .replace(row["City"], "")
        .replace(row["County"], "")
        .strip(", -"),
        axis=1,
    )

    # remove the timestamp, email address, Coverage Priority, Status, Additional Commenbts columns
    filtered_df = filtered_df.drop(
        columns=[
            "Timestamp",
            "Email Address",
            "Coverage priority",
            "status",
            "Additional comments",
        ]
    )

    # configure the dictionary structure, if a state-place combination already exists append the committee to the list
    config = {"sites": {}}
    for _, row in filtered_df.iterrows():
        state = row["State"].strip()
        place = row["Place"].strip()
        site_id = f"{state.lower()}-{place.replace(' ','').lower()}"
        if site_id in config["sites"]:
            config["sites"][site_id]["committees"].append(row["Committee"].strip())
        else:
            config["sites"][site_id] = {
                "state": state,
                "place": place,
                "platform": row["Vendor"].strip().lower(),
                "url": row["URL"].strip(),
                "committees": [row["Committee"].strip()],
                "start_date": "2025-01-01",  # default start date
            }

    return config


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "--vendor", help="Input the vendor name", type=str, required=True
    )
    args = parser.parse_args()

    # check that the vendor exists and raise an exception if it doesn't
    vendor_lst = [x.lower() for x in site_list]
    if args.vendor.lower() not in vendor_lst:
        raise Exception("Invalid Vendor Name, Please rerun with valid vendor")

    # get the path to the service account credentials
    current_dir = Path(__file__).parent.parent
    credentials_path = current_dir / "env" / "GOOGLE_APPLICATION_CREDENTIALS.json"

    # define the spreadsheet ID and range to fetch
    env_path = current_dir / "env" / ".env"

    load_dotenv(dotenv_path=env_path)

    # load the SPREADSHEET_ID and SHEET_RANGE
    SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
    # SHEET_RANGE = os.environ.get("SHEET_RANGE")

    if SPREADSHEET_ID:
        # authenticate and create the Sheets API service
        service = authenticate(service_account_file=credentials_path)

        # fetch and clean the spreadsheet data
        if service:
            print("Fetching Google Sheet data...")
            sheet_data = read_data_from_spreadsheet(
                service, SPREADSHEET_ID, "form_responses!A1:L1000"
            )
            config_data = clean_and_structure_data(sheet_data, args.vendor.lower())

            # write the cleaned data to test_config.json
            with open("test_config.json", "w") as f:
                json.dump(config_data, f, indent=2)
            print("test_config.json created with filtered sites.")
    else:
        raise Exception(
            "Please define the SPREADSHEET_ID and SHEET_RANGE in an .env file"
        )


if __name__ == "__main__":
    main()
