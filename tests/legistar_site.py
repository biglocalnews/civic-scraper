import logging
import sys
import urllib3
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
sys.path.append(PROJECT_ROOT)

from civic_scraper.platforms import LegistarSite

logging.basicConfig(level="DEBUG")

legistar_sites = [
    {
        "start_date": "2022-05-17",
        "end_date": "2022-05-17",
        "site": "https://kpb.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Alaska",
        },
    },
    {
        "start_date": "2022-01-04",
        "end_date": "2022-01-04",
        "site": "https://matanuska.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Alaska",
        },
    },
    {
        "start_date": "2021-04-19",
        "end_date": "2021-04-19",
        "site": "https://petersburg.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Alaska",
        },
    },
    {
        "start_date": "2022-04-19",
        "end_date": "2022-04-19",
        "site": "https://sitka.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Alaska",
        },
    },
    {
        "start_date": "2022-04-19",
        "end_date": "2022-04-19",
        "site": "https://valdez.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Alaska",
        },
    },
    {
        "start_date": "2022-04-14",
        "end_date": "2022-04-14",
        "site": "https://baldwincountyal.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Central",
        },
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://cityoffoley.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Central",
        },
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://jonesboro.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Central",
        },
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://apachejunction.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Arizona",
        },
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://goodyear.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Arizona",
        },
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://lakehavasucity.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Arizona",
        },
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://maricopa.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Arizona",
        },
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://mesa.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Arizona",
        },
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://paradisevalleyaz.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Arizona",
        },
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://phoenix.legistar.com/Calendar.aspx",
        "config": {
            "event_info_keys": {
                "meeting_details_info": "Details",
                "meeting_date_info": "Date",
                "meeting_time_info": "Time",
                "meeting_location_info": "Location",
            },
            "timezone": "US/Arizona",
        },
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "asset_list": ["Agenda", "Summaries"],
        "site": "https://pima.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Arizona",
        },
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://alameda.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://actransit.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://burlingameca.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://carson.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://cityofcommerce.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://corona.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://cupertino.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://eldorado.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://emeryville.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://cityfortbragg.legistar.com/Calendar.aspx",
        "config": {"timezone": "US/Pacific"},
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://fresnocounty.legistar.com/Calendar.aspx",
        "config": {"timezone": "US/Pacific"},
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://fresno.legistar.com/Calendar.aspx",
        "config": {"timezone": "US/Pacific"},
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://fullerton.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
    {
        "start_date": "2022-01-01",
        "end_date": "2022-03-31",
        "site": "https://goleta.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
]


def legistar_integration():
    for obj in legistar_sites:
        print(f"{obj['site']}")
        scraper = LegistarSite(obj["site"], **obj["config"])
        try:
            kwargs = {"start_date": obj["start_date"], "end_date": obj["end_date"]}
            try:
                kwargs["asset_list"] = obj["asset_list"]
            except KeyError:
                pass
            data = scraper.scrape(**kwargs)
            assert len(data) > 0
        except Exception as e:
            print(f"Error: {obj['site']}")
            if e.__class__ == AssertionError:
                continue
            else:
                raise


if __name__ == "__main__":
    legistar_integration()
