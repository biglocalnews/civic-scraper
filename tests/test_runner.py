from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from civic_scraper.runner import Runner


@pytest.mark.usefixtures("set_default_env")
def test_runner_site_scrape(civic_scraper_dir, one_site_url):
    site_class = MagicMock(name="CivicPlusSite")
    to_patch = "civic_scraper.runner.Runner._get_site_class"
    with patch(to_patch) as mock_method:
        mock_method.return_value = site_class
        start_date = end_date = "2020-12-01"
        r = Runner(civic_scraper_dir)
        r.scrape(start_date, end_date, one_site_url)
        site_class.assert_called_once_with(
            "http://nc-nashcounty.civicplus.com/AgendaCenter"
        )
        site_instance = site_class.return_value
        site_instance.scrape.assert_called_once_with(
            "2020-12-01",
            "2020-12-01",
            cache=False,
        )


@patch("civic_scraper.runner.Runner._get_site_class")
@patch("civic_scraper.runner.Cache")
@pytest.mark.usefixtures("set_default_env")
def test_runner_site_cache(cache_mock, get_site_mock, civic_scraper_dir, one_site_url):
    "Runner should configure Site cache and call scrape with cache flag"
    # Prep mocks
    site_class = MagicMock(name="CivicPlusSite")
    cache_instance = cache_mock.return_value
    cache_instance.metadata_files_path = str(
        Path(civic_scraper_dir).joinpath("metadata")
    )
    get_site_mock.return_value = site_class
    # Run test
    start_date = end_date = "2012-12-01"
    r = Runner(civic_scraper_dir)
    r.scrape(start_date, end_date, site_urls=one_site_url, cache=True)
    # Cache class is instantiated with default civic scraper dir
    cache_mock.assert_called_once_with(civic_scraper_dir)
    # The site_class is passed a url and a Cache instance
    site_class.assert_called_once_with(one_site_url[0], cache=cache_mock.return_value)
    # The site instance is told to perform caching
    site_instance = site_class.return_value
    site_instance.scrape.assert_called_once_with(
        "2012-12-01",
        "2012-12-01",
        cache=True,
    )


@patch("civic_scraper.runner.AssetCollection")
@patch("civic_scraper.runner.Runner._get_site_class")
@pytest.mark.usefixtures("set_default_env")
def test_runner_no_download_via_site(
    get_site_mock, asset_collection, civic_scraper_dir, one_site_url
):
    "Runner should not trigger download via Site.scrape"
    # The runner is primarily intended for use by the CLI layer,
    # which may ultimately apply asynchronous, parallel,
    # or distributed downloading strategies.Therefore, we
    # should prevent runner from triggering downloads via Site.scrape
    site_class = Mock(name="CivicPlusSite")
    get_site_mock.return_value = site_class
    # Also need to configure return value for the scrape method
    site_instance = site_class.return_value
    site_instance.scrape.return_value = [Mock(name="AssetCollection")]
    start_date = end_date = "2012-12-01"
    r = Runner(civic_scraper_dir)
    r.scrape(start_date, end_date, site_urls=one_site_url, cache=True, download=True)
    # Cache class is instantiated with default civic scraper dir
    # The site instance is told to perform caching
    site_instance.scrape.assert_called_once_with(
        "2012-12-01",
        "2012-12-01",
        cache=True,
    )
    # AssetCollection is instantiated and to_csv called by default
    asset_collection.assert_called_once()
    ac_instance = asset_collection.return_value
    ac_instance.to_csv.assert_called_once()


@patch("civic_scraper.platforms.civic_plus.site.Asset")
@patch("civic_scraper.runner.AssetCollection")
@pytest.mark.vcr()
@pytest.mark.usefixtures("set_default_env")
def test_runner_downloads_assets(asset_collection, asset_mock, civic_scraper_dir):
    "Runner should trigger download on assets if requested"
    url = "http://nc-nashcounty.civicplus.com/AgendaCenter"
    start_date = end_date = "2020-05-05"
    r = Runner(civic_scraper_dir)
    r.scrape(start_date, end_date, site_urls=[url], download=True)
    # Check AssetCollection is instantiated and to_csv called by default
    asset_collection.assert_called_once()
    ac_instance = asset_collection.return_value
    ac_instance.to_csv.assert_called_once()
    # Check Asset.download is called
    assets_dir = str(Path(civic_scraper_dir).joinpath("assets"))
    asset_instance = asset_mock.return_value
    # Asset.download called twice with the assets_dir path
    asset_instance.has_calls(
        call(assets_dir),
        call(assets_dir),
    )
