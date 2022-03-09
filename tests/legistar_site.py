import logging

from civic_scraper.platforms import LegistarSite

logging.basicConfig(level="DEBUG")

legistar_sites = [
    {
        "site": "https://kpb.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Alaska",
        },
    },
    {
        "site": "https://matanuska.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Alaska",
        },
    },
    {
        "site": "https://petersburg.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Alaska",
        },
    },
    {
        "site": "https://sitka.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Alaska",
        },
    },
    {
        "site": "https://valdez.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Alaska",
        },
    },
    {
        "site": "https://baldwincountyal.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Central",
        },
    },
    {
        "site": "https://cityoffoley.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Central",
        },
    },
    {
        "site": "https://jonesboro.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Central",
        },
    },
    {
        "site": "https://apachejunction.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Arizona",
        },
    },
    {
        "site": "https://goodyear.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Arizona",
        },
    },
    {
        "site": "https://lakehavasucity.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Arizona",
        },
    },
    {
        "site": "https://maricopa.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Arizona",
        },
    },
    {
        "site": "https://mesa.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Arizona",
        },
    },
    {
        "site": "https://paradisevalleyaz.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Arizona",
        },
    },
    {
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
        "site": "https://pima.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Arizona",
        },
    },
    {
        "site": "https://alameda.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
    {
        "site": "https://actransit.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
    {
        "site": "https://burlingameca.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
    {
        "site": "https://carson.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
    {
        "site": "https://cityofcommerce.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
    {
        "site": "https://corona.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
    {
        "site": "https://cupertino.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
    {
        "site": "https://eldorado.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
    {
        "site": "https://emeryville.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
    {
        "site": "https://cityfortbragg.legistar.com/Calendar.aspx",
        "config": {"timezone": "US/Pacific"},
    },
    {
        "site": "https://fresnocounty.legistar.com/Calendar.aspx",
        "config": {"timezone": "US/Pacific"},
    },
    {
        "site": "https://fresno.legistar.com/Calendar.aspx",
        "config": {"timezone": "US/Pacific"},
    },
    {
        "site": "https://fullerton.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
    {
        "site": "https://goleta.legistar.com/Calendar.aspx",
        "config": {
            "timezone": "US/Pacific",
        },
    },
]


def legistar_integration():
    for obj in legistar_sites:
        scraper = LegistarSite(obj["site"], **obj["config"])
        data = scraper.scrape()
        assert len(data) > 0


if __name__ == "__main__":
    legistar_integration()
