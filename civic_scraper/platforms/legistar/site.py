from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection

from pathlib import Path

# Scrape today's agendas and minutes from a Legistar site
class LegistarSite(base.Site):
    # do not overwrite init method
    # base.Site's init has what we need for now
    def create_asset(self):
        return Asset(url="https://google.com",
                     place="Canton, GA",
                     content_type="txt")

    def scrape(self, download=True):
        a = self.create_asset()
        ac = AssetCollection()
        ac.append(a)
        if download:
            asset_dir = Path(self.cache.path, 'assets')
            asset_dir.mkdir(parents=True, exist_ok=True)
            for asset in ac:
                # if self._skippable(asset, file_size, asset_list):
                    # continue
                s = str(asset_dir)
                # breakpoint()
                asset.download(s)
        return ac

if __name__ == "__main__":
    url = "https://canton.legistar.com/Calendar.aspx"
    site = LegistarSite(url)
    assets = site.scrape(download=True)
    assets.to_csv(site.cache.metadata_files_path)