import re
from pathlib import Path

import pytest
from click.testing import CliRunner

from .conftest import csv_rows, list_dir

from civic_scraper import cli


@pytest.mark.vcr()
@pytest.mark.usefixtures("set_default_env", "create_scraper_dir")
def test_cli_scrape_simple(civic_scraper_dir):
    "Scrape should write assets metadata by default"
    runner = CliRunner()
    runner.invoke(
        cli.cli,
        [
            "scrape",
            "--start-date",
            "2020-05-05",
            "--end-date",
            "2020-05-05",
            "--url",
            "http://nc-nashcounty.civicplus.com/AgendaCenter",
        ],
    )
    meta_files = [
        f.name for f in Path(civic_scraper_dir).joinpath("metadata").glob("*")
    ]
    # Check metadata written by default
    assert len(meta_files) == 1
    fname = meta_files[0]
    pattern = r"civic_scraper_assets_meta_20201225T\d{4}z.csv"
    assert re.match(pattern, fname)
    full_path = str(Path(civic_scraper_dir, "metadata", fname))
    data = csv_rows(full_path)
    assert len(data) == 2
    # Check assets and artifacts *not* saved by default
    artifacts_dir = Path(civic_scraper_dir).joinpath("artifacts")
    assets_dir = Path(civic_scraper_dir).joinpath("assets")
    assert not artifacts_dir.exists()
    assert not assets_dir.exists()


@pytest.mark.vcr()
@pytest.mark.usefixtures("set_default_env", "create_scraper_dir")
def test_cli_store_assets_and_artifacts(civic_scraper_dir):
    "Scrape should write assets metadata by default"
    runner = CliRunner()
    runner.invoke(
        cli.cli,
        [
            "scrape",
            "--start-date",
            "2020-05-05",
            "--end-date",
            "2020-05-05",
            "--cache",
            "--download",
            "--url",
            "http://nc-nashcounty.civicplus.com/AgendaCenter",
        ],
    )
    artifacts_dir = Path(civic_scraper_dir).joinpath("artifacts")
    assets_dir = Path(civic_scraper_dir).joinpath("assets")
    meta_dir = Path(civic_scraper_dir).joinpath("metadata")
    # Check assets, artifacts, and metadata have been saved by default
    assert meta_dir.exists()
    assert len(list_dir(meta_dir)) == 1
    assert artifacts_dir.exists()
    assert len(list_dir(artifacts_dir)) == 1
    assert assets_dir.exists()
    assert len(list_dir(assets_dir)) == 2
