import csv
import logging
import os

import click
from click_option_group import RequiredMutuallyExclusiveOptionGroup, optgroup

from civic_scraper.runner import Runner
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
@optgroup.group(
    "Site sources",
    cls=RequiredMutuallyExclusiveOptionGroup,
    help="Site URLs must be supplied on the command line or via CSV file.",
)
@optgroup.option("--url", help="Base URL for a single site to scraper.")
@optgroup.option(
    "--urls-file",
    type=click.File("r"),
    help="CSV containing a 'url' field for target sites.",
)
def scrape(start_date, end_date, download, cache, url, urls_file):
    """Scrape one or more government sites."""
    cache_path = os.environ.get("CIVIC_SCRAPER_DIR", DEFAULT_USER_HOME)
    runner = Runner(cache_path=cache_path)
    kwargs = {
        "start_date": start_date,
        "end_date": end_date,
        "cache": cache,
        "download": download,
    }
    if url:
        kwargs["site_urls"] = [url]
    else:
        reader = csv.DictReader(urls_file.readlines())
        kwargs["site_urls"] = [row["url"] for row in reader]
    runner.scrape(**kwargs)
