import csv
import logging
import os

import click
from click_option_group import RequiredMutuallyExclusiveOptionGroup, optgroup

from civic_scraper.runner import PLATFORMS, Runner
from civic_scraper.utils import default_user_home, today_local_str

TODAY = today_local_str()
DEFAULT_USER_HOME = default_user_home()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)-12s - %(message)s",
    datefmt="%m-%d %H:%M",
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)


@click.group()
def cli():
    pass


@cli.command(
    help="Scrape government websites for links to agendas, minutes and other files."
)
@click.option(
    "-s",
    "--start-date",
    default=TODAY,
    help=f"Scrape artifacts starting from this date. (default: {TODAY})",
)
@click.option(
    "-e",
    "--end-date",
    default=TODAY,
    help=f"Scrape artifacts up to and including this date. (default: {TODAY})",
)
@click.option(
    "-d",
    "--download/--no-download",
    default=False,
    help=(
        "Download file assets such as agendas and minutes to"
        f" {DEFAULT_USER_HOME}/assets. Location can be customized"
        " by setting the CIVIC_SCRAPER_DIR environment variable."
    ),
)
@click.option(
    "-c",
    "--cache/--no-cache",
    default=False,
    help=(
        "Save intermediate file artificats such as HTML from scraped sites."
        f" By default caches files to {DEFAULT_USER_HOME}/artifacts."
        " Location can be customized by setting the CIVIC_SCRAPER_DIR"
        " environment variable"
    ),
)
@click.option(
    "-t",
    "--timeout",
    default=None,
    type=int,
    help="Timeout in seconds for HTTP requests. By default, no timeout.",
)
@click.option(
    "--platform",
    type=click.Choice(list(PLATFORMS.keys()), case_sensitive=False),
    help="Force a specific platform instead of auto-detecting from the URL.",
)
@optgroup.group(
    "Site sources",
    cls=RequiredMutuallyExclusiveOptionGroup,
    help="Site URLs must be supplied on the command line or via CSV file.",
)
@optgroup.option("--url", help="Base URL for a single site to scrape.")
@optgroup.option(
    "--urls-file",
    type=click.File("r"),
    help="CSV containing a 'url' field for target sites. An optional 'platform' column overrides auto-detection per row.",
)
def scrape(start_date, end_date, download, cache, timeout, platform, url, urls_file):
    """Scrape one or more government sites."""
    cache_path = os.environ.get("CIVIC_SCRAPER_DIR", DEFAULT_USER_HOME)
    runner = Runner(cache_path=cache_path)
    # TODO - Do not pass download to scrapers. Runner already downloads
    # assets after scraping, so this isScrapers should just return asset
    # URLs and metadata. Refactor in a future PR.
    kwargs = {
        "start_date": start_date,
        "end_date": end_date,
        "cache": cache,
        "download": download,
        "timeout": timeout,
    }
    if platform:
        kwargs["platform"] = platform
    if url:
        kwargs["site_urls"] = [url]
    else:
        reader = csv.DictReader(urls_file.readlines())
        rows = list(reader)
        if "platform" in (reader.fieldnames or []):
            kwargs["site_urls"] = [
                {"url": row["url"].strip(), "platform": row["platform"] or None}
                for row in rows
            ]
        else:
            kwargs["site_urls"] = [row["url"] for row in rows]
    runner.scrape(**kwargs)
