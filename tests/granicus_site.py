import logging

from civic_scraper.platforms import GranicusSite

logging.basicConfig(level="DEBUG")

granicus_sites = [
    {
        "site": "https://brookhavencityga.iqm2.com/Services/RSS.aspx?Feed=Calendar",
        "config": {
            "place": "brookhaven",
            "state_or_province": "ga",
        },
    },
    {
        "site": "https://eastpointcityga.iqm2.com/Services/RSS.aspx?Feed=Calendar",
        "config": {
            "place": "east_point",
            "state_or_province": "ga",
        },
    },
    {
        "site": "https://atlantacityga.iqm2.com/Services/RSS.aspx?Feed=Calendar",
        "config": {
            "place": "atlanta",
            "state_or_province": "ga",
        },
    },
]


def granicus_integration():
    for obj in granicus_sites:
        scraper = GranicusSite(obj["site"], **obj["config"])
        data = scraper.scrape()
        assert len(data) > 0


if __name__ == "__main__":
    granicus_integration()
