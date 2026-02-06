#!/usr/bin/env python3
"""
TITLE: scaffold_platform.py
DESCRIPTION:
Generate scaffolding for a new platform scraper. Creates all the boilerplate
files needed to start implementing a scraper:

  - Platform module directory
  - __init__.py with exports
  - site.py with Site class stub
  - test file with basic test stubs
  - cassettes directory

USAGE:
From the command line:

  python scripts/scaffold_platform.py \
    --platform your_jurisdiction \
    --url https://your-jurisdiction-gov.com

This creates:
  civic_scraper/platforms/your_jurisdiction/__init__.py
  civic_scraper/platforms/your_jurisdiction/site.py
  tests/test_your_jurisdiction_site.py
  tests/cassettes/test_your_jurisdiction_site/

PYTHON API:
  from scripts.scaffold_platform import scaffold_platform

  scaffold_platform(
      platform_name="your_jurisdiction",
      base_url="https://your-jurisdiction-gov.com"
  )
"""

import argparse
from pathlib import Path


# Templates for generated files

INIT_TEMPLATE = """from .site import Site as {class_name}

__all__ = ["{class_name}"]
"""

SITE_TEMPLATE = '''"""
Scraper for {platform_name}

Base URL: {base_url}
"""

import logging
from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.base.cache import Cache

logger = logging.getLogger(__name__)


class Site(base.Site):
    """Scraper for {platform_name}."""

    def __init__(self, base_url, cache=Cache()):
        """Initialize scraper.

        Args:
            base_url (str): Base URL of the jurisdiction website
            cache (Cache): Cache instance (default: new Cache())
        """
        super().__init__(base_url, cache=cache)
        self.base_url = base_url

    def scrape(self, start_date=None, end_date=None, cache=False, download=False):
        """Scrape the jurisdiction website for meeting documents.

        Args:
            start_date (str): YYYY-MM-DD format (default: today)
            end_date (str): YYYY-MM-DD format (default: today)
            cache (bool): Cache raw HTML (default: False)
            download (bool): Download PDF/doc files (default: False)

        Returns:
            AssetCollection: Collection of Asset instances
        """
        # TODO: Implement scraper logic
        # 1. Fetch data from the website
        # 2. Extract metadata (dates, URLs, types, etc.)
        # 3. Build and return AssetCollection
        raise NotImplementedError("Scraper not yet implemented")
'''

TEST_TEMPLATE = '''"""
Tests for {platform_name} scraper

Run with: pipenv run pytest -sv tests/{test_module}.py
"""

import datetime
import pytest

from civic_scraper.platforms.{platform_name} import {class_name}


@pytest.mark.vcr()
def test_scrape_defaults(civic_scraper_dir, set_default_env):
    """Test basic scraping functionality with defaults.

    On first run: VCR records HTTP interactions to cassette
    On subsequent runs: VCR replays mocked responses

    TODO: Update the expected count based on what's actually on the website.
    Inspect {base_url} to count how many documents you expect to find,
    then replace the assertion below with the exact number.
    """
    site = {class_name}("{base_url}/")
    assets = site.scrape()

    # TODO: Replace X with the number of documents you expect to find
    # (e.g., if the website shows 3 agendas on the first page, use 3)
    assert len(assets) == X, "Should find exactly X assets (update X based on what's on the website)"

    # Verify result type
    assert hasattr(assets, '__iter__'), "Assets should be iterable"

    # Verify first asset has required fields
    asset = assets[0]
    assert asset.url.startswith("https://"), "URL should be absolute"
    assert asset.asset_type in ["agenda", "minutes", "other"], "Asset type should be recognized"
    assert isinstance(asset.meeting_date, datetime.datetime), "Meeting date should be datetime"


@pytest.mark.vcr()
def test_scrape_with_date_range(civic_scraper_dir, set_default_env):
    """Test scraping with specific date range.

    TODO: Adjust dates and expected count based on your target website.
    """
    site = {class_name}("{base_url}/")
    start_date = "2024-01-01"
    end_date = "2024-01-31"

    assets = site.scrape(start_date=start_date, end_date=end_date)

    # TODO: Replace Y with the expected count for this date range
    assert len(assets) == Y, "Should find exactly Y assets in the date range"


@pytest.mark.vcr()
def test_site_initialization():
    """Test Site can be initialized."""
    site = {class_name}("{base_url}/")

    assert site.base_url == "{base_url}/"
    assert site.url == "{base_url}/"
'''


def platform_to_class_name(platform_name):
    """Convert platform_name (your_jurisdiction) to ClassName."""
    parts = platform_name.split("_")
    return "".join(word.capitalize() for word in parts) + "Site"


def scaffold_platform(platform_name, base_url, repo_root=None):
    """Generate scaffolding for a new platform scraper.

    Args:
        platform_name (str): Platform name, lowercase with underscores (e.g., 'your_jurisdiction')
        base_url (str): Base URL of the jurisdiction website
        repo_root (str): Root of the repository (default: current directory)

    Returns:
        dict: Paths of created files
    """
    if repo_root is None:
        repo_root = Path.cwd()
    else:
        repo_root = Path(repo_root)

    # Validate platform name
    if not platform_name.replace("_", "").isalnum():
        raise ValueError(
            f"Platform name must be alphanumeric with underscores: {platform_name}"
        )

    class_name = platform_to_class_name(platform_name)
    test_module = f"test_{platform_name}_site"

    # Define paths
    platform_dir = repo_root / "civic_scraper" / "platforms" / platform_name
    init_file = platform_dir / "__init__.py"
    site_file = platform_dir / "site.py"
    test_file = repo_root / "tests" / f"{test_module}.py"
    cassettes_dir = repo_root / "tests" / "cassettes" / test_module

    # Check if already exists
    if platform_dir.exists():
        raise FileExistsError(f"Platform directory already exists: {platform_dir}")

    # Create directories
    platform_dir.mkdir(parents=True, exist_ok=False)
    cassettes_dir.mkdir(parents=True, exist_ok=True)

    # Generate __init__.py
    init_content = INIT_TEMPLATE.format(class_name=class_name)
    with open(init_file, "w") as f:
        f.write(init_content)

    # Generate site.py
    site_content = SITE_TEMPLATE.format(platform_name=platform_name, base_url=base_url)
    with open(site_file, "w") as f:
        f.write(site_content)

    # Generate test file
    test_content = TEST_TEMPLATE.format(
        platform_name=platform_name,
        class_name=class_name,
        test_module=test_module,
        base_url=base_url,
    )
    with open(test_file, "w") as f:
        f.write(test_content)

    return {
        "platform_dir": str(platform_dir),
        "init_file": str(init_file),
        "site_file": str(site_file),
        "test_file": str(test_file),
        "cassettes_dir": str(cassettes_dir),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scaffold a new platform scraper with all boilerplate"
    )
    parser.add_argument(
        "--platform",
        required=True,
        help="Platform name (lowercase with underscores, e.g., your_jurisdiction)",
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Base URL of the jurisdiction website (e.g., https://your-jurisdiction-gov.com)",
    )

    args = parser.parse_args()

    try:
        files = scaffold_platform(platform_name=args.platform, base_url=args.url)

        class_name = platform_to_class_name(args.platform)
        test_module = f"test_{args.platform}_site"

        print("✓ Scaffolding created successfully!")
        print()
        print("Created files:")
        print(f"  {files['platform_dir']}/")
        print("    ├── __init__.py")
        print("    └── site.py")
        print(f"  {files['test_file']}")
        print(f"  {files['cassettes_dir']}/")
        print()
        print("Next steps:")
        print(f"  1. Run tests: pipenv run pytest -sv tests/{test_module}.py")
        print("  2. Tests will fail (NotImplementedError)")
        print("  3. Implement Site.scrape() to make tests pass")
        print("  4. First test run records HTTP cassettes")
        print("  5. Subsequent runs replay from cassettes")

    except FileExistsError as e:
        print(f"Error: {e}")
        exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        exit(1)
    except Exception as e:
        print(f"Error creating scaffold: {e}")
        exit(1)
