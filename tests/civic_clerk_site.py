import logging

from civic_scraper.platforms import CivicClerkSite

logging.basicConfig(level="DEBUG")

civic_clerk_sites = [
    {
        "site": "https://chaffeecoco.civicclerk.com/web/home.aspx",
        "config": {"place": "chaffee_co", "state_or_province": "co"},
    },
    {
        "site": "https://mineralwellstx.civicclerk.com/web/home.aspx",
        "config": {"place": "mineral_wells", "state_or_province": "tx"},
    },
    {
        "site": "https://indianolaia.civicclerk.com/web/home.aspx",
        "config": {"place": "indianola", "state_or_province": "ia"},
    },
    {
        "site": "https://alpharettaga.civicclerk.com/web/home.aspx",
        "config": {"place": "alpharetta", "state_or_province": "ga"},
    },
    {
        "site": "https://northstpaulmn.civicclerk.com/web/home.aspx",
        "config": {"place": "north_st_paul", "state_or_province": "mn"},
    },
]


def civic_clerk_integration():
    for obj in civic_clerk_sites:
        scraper = CivicClerkSite(obj["site"], **obj["config"])
        data = scraper.scrape()
        assert len(data) > 0


if __name__ == "__main__":
    civic_clerk_integration()
