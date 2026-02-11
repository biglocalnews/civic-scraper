# Developer Guide: Writing Your First Scraper

This guide will orient you to the repository and walk you through writing a scraper for any jurisdiction or a platform
used by multiple jurisdictions. It is meant to serve as a good place to start to onboard to the code base and repository.

## Document status: Needs more eyes

This document has been used by the original author to write a scraper. It has not been used for a second developer to
write a second scraper, which would serve as a more thorough review opportunity.

This document was written with the help of GitHub Copilot.

## Introduction: Test-Driven Development (TDD)

This guide uses **Test-Driven Development** principles. The workflow is:

1. **Write Tests First** - Define what your scraper should do
2. **See Tests Fail** - Run them; they should fail (you haven't implemented yet)
3. **Implement Code** - Write code to pass the tests
4. **See Tests Pass** - Verify all tests pass
5. **Iterate & Refine** - Add more tests for edge cases

**Why TDD?**
- Tests serve as executable specifications of how your scraper should work
- You know when you're done (all tests pass)
- Reduces bugs and makes debugging easier
- Makes refactoring safer
- Creates documentation through tests

In civic-scraper, tests use **vcrpy** to record HTTP interactions on first run, then replay them. This means:
- ✅ Tests run fast (no network requests after first run)
- ✅ Tests are reproducible (same cassette every time)
- ✅ You can run tests without internet
- ✅ Tests don't hammer the government website on every run

## Quick Repository Orientation

### What is civic-scraper?

civic-scraper is a **plugin-based scraper framework** for government websites. It supports multiple government platforms (Civic Plus, Legistar, Granicus, etc.) through platform-specific implementations, all inheriting from a common base class.

### Directory Structure

```
civic_scraper/
├── base/                          # Core framework code
│   ├── site.py                   # Abstract Site class (base for all scrapers)
│   ├── asset.py                  # Asset & AssetCollection (results)
│   ├── cache.py                  # File caching system
│   └── constants.py              # Shared constants
├── platforms/                     # Platform-specific scrapers
│   ├── civic_plus/               # Reference implementation
│   │   └── site.py              # Platform-specific Site class
│   ├── legistar/
│   ├── granicus/
│   ├── civic_clerk/
│   ├── primegov/
│   └── your_platform/            # ← Your new scraper goes here!
├── cli.py                         # Command-line interface
└── utils.py                       # Helper utilities
```

### tests/ Directory Structure

```
tests/
├── conftest.py                   # Fixtures and VCR configuration
├── test_civic_plus_site.py       # Example test file
├── cassettes/                    # Recorded HTTP responses for tests
│   ├── test_civic_plus_site/    # One folder per test module
│   └── test_your_site/          # ← Your cassettes go here
└── fixtures/                     # Test data files
```

---

## Core Concepts

### The Site Class (Your Scraper)

All scrapers inherit from `base.Site` and implement a `scrape()` method.

**Required:**
- Inherit from `civic_scraper.base.Site`
- Implement `scrape(start_date=None, end_date=None, cache=False, download=False)` method
- Return an `AssetCollection` instance

**What `scrape()` should do:**
1. Accept optional `start_date` and `end_date` (YYYY-MM-DD format)
2. Fetch meeting data from the government website
3. Extract metadata for each meeting document (URL, date, type, etc.)
4. Create `Asset` instances for each document found
5. Return all assets as an `AssetCollection`

**Refer to the scaffolded code** in your platform directory (`site.py`) for the actual implementation pattern. Look at existing platforms like `civic_scraper/platforms/civic_plus/site.py` for reference implementations.

### Assets & AssetCollection

Results are returned as an `AssetCollection`—a sequence of `Asset` objects representing documents:

```python
from civic_scraper.base.asset import AssetCollection, Asset

# Assets contain metadata:
asset.url              # Full URL to document
asset.asset_type       # 'agenda', 'minutes', etc.
asset.meeting_date     # datetime object
asset.committee_name   # Board/committee name
asset.content_type     # 'application/pdf', etc.
asset.content_length   # File size in bytes

# Each asset can be downloaded:
asset.download("/path/to/directory")

# Results are sequences:
assets = AssetCollection([asset1, asset2, ...])
for asset in assets:
    print(asset.url, asset.asset_type)
```

---

## Coding Conventions

### File Organization

Every platform has this structure:

```
civic_scraper/platforms/your_jurisdiction/
├── __init__.py          # Can be empty or export your Site class
└── site.py              # Main Site implementation
```

### Naming Conventions

| Item | Convention | Example |
|------|-----------|---------|
| Site class | Use name `Site` | `class Site(base.Site):` |
| Platform module | Lowercase with underscores | `your_jurisdiction/` |
| URL pattern | Extract from domain | `your-jurisdiction-gov.com` → subdomain `yourjurisdiction` |
| Asset type | Lowercase, matches `SUPPORTED_ASSET_TYPES` | `'agenda'`, `'minutes'` |
| Meeting ID | Combine platform + place + unique ID | `your_jurisdiction_yourplace_2024_01_15_agenda` |

### Import Patterns

```python
# Always import from the base package:
from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.base.cache import Cache
from civic_scraper.utils import today_local_str

# For HTTP requests:
import requests

# For HTML parsing:
import bs4

# For dates:
import datetime
from datetime import datetime as dt
```

### Supported Asset Types

Asset types are defined in `civic_scraper/base/constants.py`. Common ones:

- `agenda` - Meeting agenda
- `minutes` - Meeting minutes
- `resolution`
- `ordinance`
- `vote`

### Dates and Time Handling

```python
from civic_scraper.utils import today_local_str

# Get today's date in YYYY-MM-DD format
today = today_local_str()  # "2024-01-15"

# Convert strings to datetime objects:
meeting_date = datetime.datetime.strptime("2024-01-15", "%Y-%m-%d")

# All meeting dates should be datetime objects, not strings
```

---

## Step-by-Step: Write Your First Scraper (TDD Approach)

**TDD Philosophy:** Write tests first, then implement code to pass those tests. Tests serve as executable specifications.

### Step 1: Scaffold the Platform

Use the scaffold script to generate all boilerplate files at once:

```bash
python scripts/scaffold_platform.py \
  --platform your_jurisdiction \
  --url https://your-jurisdiction-gov.com/meetings
```

The `--url` should be the **meetings page URL** — the web page that lists agendas, minutes, and other meeting documents — not just the bare domain. It works with or without a trailing slash.

This creates:
- `civic_scraper/platforms/your_jurisdiction/__init__.py`
- `civic_scraper/platforms/your_jurisdiction/site.py` (with Site class stub)
- `tests/test_your_jurisdiction_site.py` (with test stubs)
- `tests/cassettes/test_your_jurisdiction_site/` (directory for cassettes)

Your Site class and tests are ready to run (they'll fail with `NotImplementedError`, which is expected).

### Step 2: Understand VCR test setup

**Cassettes are auto-recorded by VCR — no separate generation step needed:**

You do **not** need to run a special command to generate cassettes. VCR records them automatically the first time your *implemented* scraper makes real HTTP requests during a test. Here's the timeline:

1. **After scaffolding:** Tests exist but `scrape()` raises `NotImplementedError` — no HTTP requests happen, so **no cassettes are recorded yet**. This is expected.
2. **After implementing `scrape()`:** The first test run makes live HTTP requests to the government website. VCR captures all requests/responses and saves them as cassette files in `tests/cassettes/{test_module}/{test_name}.yaml`.
3. **Subsequent runs:** VCR replays the recorded responses (no live requests, fast tests).

If your scraper makes 2 HTTP requests (e.g., `/meetings` then `/meetings/board-1`), both get recorded in a single cassette automatically. You don't need to manually create or configure cassettes — VCR handles it.

### Step 3: Review Scaffolded Tests

The scaffold script already created `tests/test_your_jurisdiction_site.py` with basic test stubs. These tests are ready to run immediately.

Run them to see them fail (expected):

```bash
pipenv run pytest -sv tests/test_your_jurisdiction_site.py
```

**Tests will FAIL** with `NotImplementedError: Scraper not yet implemented`. This is correct! ✓

Expected output:
```
FAILED tests/test_your_jurisdiction_site.py::test_scrape_defaults - NotImplementedError: Scraper not yet implemented
```

This failure is good because it means:
- ✓ Tests are discoverable and runnable
- ✓ Site class imports correctly
- ✓ Tests define what needs to be implemented

**Note:** No cassettes are recorded at this point — your scraper hasn't made any HTTP requests yet. Cassettes will be recorded automatically later, the first time you run tests after implementing `scrape()` (see Step 4).

**You can modify or add more tests** to match your actual scraper requirements. The key is that tests fail first, then you implement code to make them pass (TDD).

### Step 4: Implement the Site Class

Now implement the Site class to make all tests pass. The first time you run your tests after implementing `scrape()`, VCR will automatically record the HTTP interactions as cassette files (this requires internet access). Subsequent test runs replay from the recorded cassettes.

### Step 5: Export Your Scraper

Update the `__init__.py`:

```python
# civic_scraper/platforms/your_jurisdiction/__init__.py
from .site import YourJurisdictionSite

__all__ = ["YourJurisdictionSite"]
```

### Step 6: Run All Tests

Now run all your tests:

```bash
pipenv run pytest -sv tests/test_your_jurisdiction_site.py
```

**All tests should PASS**. ✓

### Step 7: Iterate & Refine

Your tests define the contract. If the live website changes or you find issues:

1. Add a test that captures the bug/requirement
2. Make the test fail
3. Fix the implementation to pass the test

Example: Your extraction logic isn't finding meetings because the HTML structure is different:

```python
# Add a test that demonstrates the problem
@pytest.mark.vcr()
def test_handles_different_html_structure():
    """Test scraper works with actual website HTML."""
    site = YourJurisdictionSite("https://your-jurisdiction-gov.com/meetings")
    assets = site.scrape()
    # ... test fails
    # Fix _extract_metadata() to handle actual structure
    # ... test passes
```

---

## Understanding VCR & Test Fixtures

### The VCR Pattern: Record Once, Test Forever

Tests use **vcrpy** to:
1. **Record** HTTP requests/responses on first run (or when manually triggered)
2. **Replay** recordings in subsequent test runs (no live requests)

This makes tests **fast**, **reproducible**, and **doesn't hammer the government website**.

### Key Test Fixtures (Available in conftest.py)

```python
civic_scraper_dir      # Temp directory for cache (~/.civic-scraper)
set_default_env        # Sets CIVIC_SCRAPER_DIR env var to civic_scraper_dir
@pytest.mark.vcr()     # Records/plays HTTP interactions from cassettes/
```

Always use `civic_scraper_dir` and `set_default_env` fixtures in your tests to ensure isolation.

### Running Tests

```bash
# Run all tests
pipenv run pytest -sv

# Run only Your Jurisdiction tests
pipenv run pytest -sv tests/test_your_jurisdiction_site.py

# Run a single test
pipenv run pytest -sv tests/test_your_jurisdiction_site.py::test_scrape_defaults

# First run after implementing scrape(): Records HTTP interactions to cassettes/ (requires internet)
# Subsequent runs: Uses recorded cassettes (fast, no network required)
```

### Inspecting Cassettes

Cassettes are stored as YAML files in `tests/cassettes/test_your_jurisdiction_site/`:

```bash
# View a cassette
cat tests/cassettes/test_your_jurisdiction_site/test_scrape_defaults.yaml

# Shows structure like:
# - request:
#     method: GET
#     uri: https://your-jurisdiction-gov.com/meetings
#   response:
#     status:
#       code: 200
#       message: OK
#     body:
#       string: "<html>...</html>"
```

### Regenerating Cassettes

If the website changes and your scraper breaks:

```bash
# Delete the cassette to force re-recording
rm tests/cassettes/test_your_jurisdiction_site/test_scrape_defaults.yaml

# Re-run the test (it will record fresh HTTP interactions)
pipenv run pytest -sv tests/test_your_jurisdiction_site.py::test_scrape_defaults

# Commit the new cassette to git
git add tests/cassettes/test_your_jurisdiction_site/test_scrape_defaults.yaml
```

---

## Common Patterns & Best Practices

### 1. Handle Missing Data Gracefully

```python
# Use .get() for optional fields
committee_name = row.get("committee_name", "Unknown")

# Provide defaults
asset_type = self._get_asset_type(text) or "other"
```

### 2. Build Full URLs

```python
from urllib.parse import urljoin

# Handle relative URLs
relative_url = "/agendas/2024-01-15.pdf"
full_url = urljoin(self.base_url, relative_url)
```

### 3. Parse Dates Safely

```python
import datetime

def parse_meeting_date(date_str):
    """Try multiple date formats."""
    formats = ["%m/%d/%Y", "%Y-%m-%d", "%B %d, %Y"]
    for fmt in formats:
        try:
            return datetime.datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    # Fallback: return today
    return datetime.datetime.utcnow().date()
```

### 4. Avoid Duplicate Assets

```python
# Track already-seen URLs
seen_urls = set()

for item in metadata:
    if item["url"] not in seen_urls:
        assets.append(Asset(...))
        seen_urls.add(item["url"])
```

### 5. Add Logging (Helpful for Debugging)

```python
import logging

logger = logging.getLogger(__name__)

def scrape(self, ...):
    logger.info(f"Scraping {self.base_url}")
    response = requests.get(url)
    logger.debug(f"Response status: {response.status_code}")
    logger.info(f"Found {len(assets)} assets")
    return assets
```

---

## Making Your Platform Scraper Work with the CLI

Once you've implemented your scraper, users need to be able to invoke it via the command-line interface (CLI). The CLI automatically detects which scraper to use based on the website URL, so you need to **register your scraper** with the platform detection logic.

> Note: This developer pattern could be improved!

### Step 1: Export Your Site Class

Edit `civic_scraper/platforms/__init__.py` and add an import for your Site class:

```python
# civic_scraper/platforms/__init__.py
from .civic_plus.site import Site as CivicPlusSite
from .your_platform.site import Site as YourPlatformSite  # ← Add this line
```

Your Site class must be exported with a name matching the pattern `{Platform}Site`. For example:
- Civic Plus → `CivicPlusSite`
- Your Platform → `YourPlatformSite`

### Step 2: Register URL Pattern in Runner

The `Runner` class in `civic_scraper/runner.py` uses URL pattern matching to determine which scraper to invoke. Add a detection rule for your platform:

```python
# civic_scraper/runner.py
def _get_site_class_name(self, url):
    if re.search(r"(civicplus|AgendaCenter)", url):
        return "CivicPlusSite"
    if re.search(r"(your-platform-domain|your-platform-pattern)", url):  # ← Add this
        return "YourPlatformSite"
    # Add more platforms as needed
    raise ScraperError(f"Unknown platform for URL: {url}")
```

The key steps:
1. **Identify the URL pattern** for your platform (e.g., domain name, path structure)
2. **Add a regex check** to detect that pattern
3. **Return the class name** that matches your exported Site class (step 1)

### Step 3: Test with the CLI

Once registered, users can invoke your scraper via:

```bash
# Single URL
civic-scraper scrape --url https://your-platform-domain.com/

# Multiple URLs from CSV
civic-scraper scrape --urls-file sites.csv

# With optional flags
civic-scraper scrape --url https://your-platform-domain.com/ \
    --start-date 2024-01-01 \
    --end-date 2024-01-31 \
    --download \
    --cache
```

### Step 4: Verify Integration

Test that the CLI correctly routes to your scraper:

```bash
pipenv run python -m civic_scraper.cli scrape --url https://your-platform-domain.com/
```

You should see logging output from your scraper (if you added logging).

### Example: Registering Civic Plus

Here's how Civic Plus was registered:

**1. Export in `__init__.py`:**
```python
from .civic_plus.site import Site as CivicPlusSite
```

**2. Detect in `runner.py`:**
```python
if re.search(r"(civicplus|AgendaCenter)", url):
    return "CivicPlusSite"
```

**3. Users can now do:**
```bash
civic-scraper scrape --url https://ca-sacramento.civicplus.com/
```

### Tips for URL Pattern Matching

- **Be specific**: Use domain names or unique path patterns to avoid false positives
- **Test multiple URLs**: Ensure your regex works for all variations of your platform's URLs
- **Document the pattern**: Add a comment explaining what URLs your pattern matches
- **Consider case-insensitivity**: Use `re.search()` with lowercase or `(?i)` flag if needed

Example patterns:
```python
# Exact domain match
r"(myplatform\.com)"

# Subdomain pattern
r"([\w-]+\.myplatform\.com)"

# Path-based detection
r"(/path/to/platform)"

# Case-insensitive
r"(?i)(myplatform|MY_PLATFORM)"
```

### Handling Multiple URL Patterns

Some platforms may have different URL structures. Add all variations:

```python
if re.search(r"(pattern1|pattern2|pattern3)", url):
    return "YourPlatformSite"
```

---

## Linting & Code Style

### Run Linter

```bash
# Check code style (flake8)
pipenv run flake8 civic_scraper/platforms/your_jurisdiction/

# Auto-format code (black)
pipenv run black civic_scraper/platforms/your_jurisdiction/
```

### Code Style Rules

- Max line length: 999 (very permissive)
- Use 4 spaces for indentation
- Use meaningful variable names
- Add docstrings to classes and public methods
- Comment when logic is not obvious

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'civic_scraper'"

Make sure you're in a pipenv shell:

```bash
cd /workspaces/civic-scraper
pipenv install --dev
pipenv shell
```

### "Website returns 403 Forbidden"

Some websites block automated requests. Try:
- Adding a User-Agent header: `headers={"User-Agent": "Mozilla/5.0..."}`
- Adding a small delay between requests: `time.sleep(1)`

### Tests Fail But Live Site Works

This usually means the HTML changed. Regenerate the cassette:

```bash
rm tests/cassettes/test_your_jurisdiction_site/*.yaml
pipenv run pytest -sv tests/test_your_jurisdiction_site.py
```

### "BeautifulSoup doesn't find elements I see in browser"

The page might load JavaScript after initial load. Try:
- Checking if there's a static data source (API, JSON embedded in HTML)
- Using Playwright or Selenium for JavaScript-rendered pages
- Asking for guidance in project issues

---

## What's Next?

- **Run existing tests**: `pipenv run pytest -sv tests/test_civic_plus_site.py`
- **Review Civic Plus implementation**: Look at `civic_scraper/platforms/civic_plus/` as a full example
- **Check Asset class**: `civic_scraper/base/asset.py` for all available fields
- **See all constants**: `civic_scraper/base/constants.py` for asset types and more

## Reference Documentation

- **[Full API Reference](reference.md)** - Detailed class documentation
- **[Usage Guide](usage.md)** - Command-line usage and programmatic API
- **[Contributing](contributing.md)** - Contribution guidelines
