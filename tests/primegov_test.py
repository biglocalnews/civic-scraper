import logging

from civic_scraper.platforms import PrimeGovSite

logging.basicConfig(level="DEBUG")

primegov_sites = [
    {
        "site": "https://lacity.primegov.com/",
        "config": {
            "place": "los angeles",
            "state_or_province": "ca",
        },
    },
    {
        "site": "https://santafe.primegov.com/",
        "config": {
            "place": "santa fe",
            "state_or_province": "nm",
        },
    },
    {
        "site": "https://sanantonio.primegov.com/",
        "config": {
            "place": "san antonio",
            "state_or_province": "tx",
        },
    },
    {
        "site": "https://ventura.primegov.com/",
        "config": {
            "place": "ventura",
            "state_or_province": "ca",
        },
    },
    {
        "site": "https://lasvegas.primegov.com/",
        "config": {
            "place": "las vegas",
            "state_or_province": "nv",
        },
    },
]


def primegov_integration():

    for obj in primegov_sites:
        scraper = PrimeGovSite(obj["site"], **obj["config"])
        data = scraper.scrape()
        assert len(data) > 0


if __name__ == "__main__":
    primegov_integration()
