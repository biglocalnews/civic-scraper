if __name__ == "__main__":
    from civic_scraper.platforms import LegistarSite
    url = "https://wellington.legistar.com/Calendar.aspx"
    site = LegistarSite(url, "wellington", "ga", timezone="EST")
    assets = site.scrape(download=True)
    assets.to_csv(site.cache.metadata_files_path)