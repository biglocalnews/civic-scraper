"""
TITLE: generate_civicplus_sites.py
AUTHOR: Amy DiPierro
VERSION: 2020-08-29

DESCRIPTION:

Given a csv of CivicPlus Agenda Center endpoints, check to see if each endpoint
contains assets that it would be possible to scrape. Add each endpoint with valid assets and
associated metadata to a csv.

NOTE: Avoid overwriting previous versions of the csv produced by this file, since it is
necessary to hand-key values in order to make them human-readable and to correctly categorize
each endpoint. By default, this script appends new rows if a csv with the same path exists.

USAGE: From the command line,

    python generate_civicplus_sites.py \
    "/Users/amydipierro/GitHub/biglocalnews/civic-scraper/docs/civicplus.csv" \
    "/Users/amydipierro/GitHub/test.csv"

"""

import csv
import re

import bs4
import pandas as pd

# Libraries
import requests

# Parameters
USA = [
    "AL",
    "AR",
    "AZ",
    "CA",
    "CO",
    "CT",
    "DE",
    "FL",
    "GA",
    "IA",
    "ID",
    "IL",
    "IN",
    "KS",
    "KY",
    "LA",
    "MA",
    "MD",
    "ME",
    "MI",
    "MN",
    "MO",
    "MS",
    "MT",
    "NC",
    "ND",
    "NE",
    "NH",
    "NJ",
    "NM",
    "NV",
    "NY",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "SK",
    "TN",
    "TX",
    "UT",
    "VA",
    "VT",
    "WA",
    "WI",
    "WV",
    "WY",
]

CANADA = ["AB", "BC", "SK"]

MUNICIPALITY = [
    "City",
    "Village",
    "Selectman",
    "Select Board",
    "Municipal",
    "Town",
    "Borough",
]

# Code


def generate_site_csv(file_in, file_out):

    raw_list = []
    clean_list = []

    # Read in each line of the .csv, reformat them and add them to a list

    with open(file_in) as f:
        for line in f:
            raw_url = line.strip().strip(",")
            format_url = f"http://{raw_url}/AgendaCenter"
            raw_list.append(format_url)

    # Take out the header from the list
    raw_list.pop(0)

    for url in raw_list:
        # Check to see if the endpoint is reachable
        try:
            response = requests.get(url)
        except Exception:
            continue

        # If website is reachable, extract metadata
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        years = soup.find_all(href=re.compile("changeYear"))

        name_list = re.search(r"(?<=\://\w{2}-)\w+(?=.)", url.title())
        if name_list is not None:
            name = name_list.group(0)
        else:
            name = "Name error"

        state = re.search(r"(?<=\://)\w{2}", url.upper()).group(0)

        # Categorize each endpoint by country
        if state in USA:
            country = "USA"
            whitelisted = True
        elif state in CANADA:
            country = "CANADA"
            whitelisted = True
        else:
            state = "Invalid state"
            whitelisted = False

        meeting_bodies = soup.find_all("h2")
        meeting_bodies_list = []
        for body in meeting_bodies:
            meeting_bodies_list.append(body.text[1:])

        # Categorize each endpoint by government level
        if (
            len(
                [
                    str
                    for str in meeting_bodies_list
                    if any(sub in str for sub in MUNICIPALITY)
                ]
            )
            > 0
        ):
            if len([i for i in meeting_bodies_list if "County" in i]) == 0:
                govt_level = "Municipality"
            else:
                govt_level = "Other"
        elif len([i for i in meeting_bodies_list if "County" in i]) > 0:
            govt_level = "County"
        else:
            govt_level = "Other"

        # Add endpoint to a list of dictionaries if it meets the criteria
        # to be considered valid for scraping.
        if response.status_code == 200 and len(years) != 0:
            years_list = []
            for element in years:
                link = element.attrs["href"]
                year = re.search(r"(?<=\()\d{4}(?=,)", link).group(0)
                years_list.append(year)
            num_years = len(years_list)
            years_list.sort()
            largest = years_list[num_years - 1]
            smallest = years_list[0]
            clean_dict = {
                "end_point": url,
                "begin_year": smallest,
                "end_year": largest,
                "scraper_type": "civicplus",
                "whitelisted": whitelisted,
                "root": re.sub(r"\d", "", url),
                "name": name,
                "state": state,
                "country": country,
                "govt_level": govt_level,
                "meeting_bodies": meeting_bodies_list,
            }
            print(url, "added to clean_dict")
            clean_list.append(clean_dict)

    # Remove duplicates in the list -- endpoints with the same root as the result
    # of aliases
    clean_list = pd.DataFrame(clean_list).drop_duplicates("root").to_dict("records")

    # Write out the list of dictionaries to a csv
    with open(file_out, "a", newline="") as file:
        dict_writer = csv.DictWriter(file, clean_dict.keys())
        dict_writer.writeheader()
        dict_writer.writerows(clean_list)


if __name__ == "__main__":
    """
    Call generate_site_csv from the command line.
    """

    import argparse

    # Set up parser
    parser = argparse.ArgumentParser()
    parser.add_argument("file_in", type=str)
    parser.add_argument(
        "file_out",
        type=str,
    )

    args = parser.parse_args()

    # Call function
    site_civicplus = generate_site_csv(
        file_in=args.file_in,
        file_out=args.file_out,
    )
