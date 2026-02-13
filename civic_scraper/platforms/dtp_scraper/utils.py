"""
Utility functions for DigitalTowPath scraper (e.g. finetownny.gov).

These functions are testable components of the scraping logic.
"""

import logging
import time
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

CATEGORIES_PATH = "/meetings/meetings/"

# Polite delay between requests (seconds)
REQUEST_DELAY = 1.0


def create_session():
    """Create a requests.Session with realistic browser headers.

    Using a session maintains cookies across requests and reuses
    TCP connections, which looks more like a real browser and is
    more polite to the server.

    Returns:
        requests.Session: Configured session
    """
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    )
    return session


def fetch_page(url, session=None, referer=None):
    """Fetch a page and return BeautifulSoup object.

    Args:
        url (str): URL to fetch
        session (requests.Session): Session to use (creates one if not provided)
        referer (str): Referer URL to send (mimics browser navigation)

    Returns:
        BeautifulSoup: Parsed HTML

    Raises:
        requests.RequestException: If request fails
    """
    if session is None:
        session = create_session()

    headers = {}
    if referer:
        headers["Referer"] = referer

    time.sleep(REQUEST_DELAY)
    response = session.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def get_categories(base_url, session=None):
    """Get list of meeting categories (committees).

    Args:
        base_url (str): Base URL (e.g., https://finetownny.gov/meetings)
        session (requests.Session): Optional session for connection reuse

    Returns:
        list: List of dicts with 'name' and 'url' keys

    Example:
        [
            {'name': 'Town Board', 'url': 'https://finetownny.gov/meetings/meetings/Town%20Board/2026'},
            {'name': 'CF Arena', 'url': 'https://finetownny.gov/meetings/meetings/CF%20Arena/2026'},
            ...
        ]
    """
    url = urljoin(base_url, CATEGORIES_PATH)
    soup = fetch_page(url, session=session)

    categories = []
    # Find all category links
    links = soup.find_all("a", class_="dtp-meeting-category-link")

    for link in links:
        name = link.get_text(strip=True)
        href = link.get("href")
        if href:
            categories.append({"name": name, "url": href})

    return categories


def get_meetings_for_category_year(url, session=None):
    """Get list of meetings for a specific category and year.

    Args:
        url (str): Category year URL (e.g., .../meetings/Town%20Board/2026)
        session (requests.Session): Optional session for connection reuse

    Returns:
        tuple: (list of meeting dicts, BeautifulSoup) — soup is returned so
            callers can extract other-year links without a second request.

    Example meetings:
        [
            {
                'title': 'February 11, 2026: February Regular Town Board Meeting',
                'url': 'https://finetownny.gov/meetings/detail/30',
                'detail_id': '30'
            },
            ...
        ]
    """
    soup = fetch_page(url, session=session)

    meetings = []
    # Find all meeting links in the current year
    links = soup.find_all("a", {"aria-label": "Link to meeting details page"})

    for link in links:
        href = link.get("href")
        if href and "/meetings/detail/" in href:
            detail_id = extract_detail_id_from_url(href)
            title = link.get_text(strip=True)
            meetings.append({"title": title, "url": href, "detail_id": detail_id})

    return meetings, soup


def get_other_years_from_soup(soup):
    """Get links to other years from an already-fetched category page.

    This avoids a second HTTP request to the same page. Pass the soup
    returned by get_meetings_for_category_year().

    Args:
        soup (BeautifulSoup): Parsed category page HTML

    Returns:
        list: List of dicts with 'year' and 'url' keys

    Example:
        [
            {'year': '2025', 'url': 'https://finetownny.gov/meetings/meetings/Town%20Board/2025'},
            {'year': '2024', 'url': 'https://finetownny.gov/meetings/meetings/Town%20Board/2024'},
            ...
        ]
    """
    years = []
    year_links = soup.find_all("a", class_="dtp-meeting-year")

    for link in year_links:
        year = link.get_text(strip=True)
        href = link.get("href")
        if href:
            years.append({"year": year, "url": href})

    return years


def get_meeting_details(detail_url, session=None):
    """Extract meeting details from a meeting detail page.

    Args:
        detail_url (str): Meeting detail page URL
        session (requests.Session): Optional session for connection reuse

    Returns:
        dict: Meeting details including metadata and documents

    Example:
        {
            'committee_name': 'Town Board',
            'meeting_title': 'February Regular Town Board Meeting',
            'meeting_date': datetime(2026, 2, 11),
            'meeting_time': '6:30 pm',
            'venue': 'Municipal Office Building',
            'address': '4078 State Highway 3',
            'zipcode': 'Star Lake, NY 13690',
            'documents': [
                {
                    'type': 'agenda',
                    'url': 'https://..../2025_DEC_AGENDA.pdf',
                    'name': '2025 DEC AGENDA.pdf'
                },
                ...
            ]
        }
    """
    soup = fetch_page(detail_url, session=session)

    # Extract committee name
    committee_elem = soup.find(class_="dtp-meeting-category")
    committee_name = committee_elem.get_text(strip=True) if committee_elem else None

    # Extract meeting title
    title_elem = soup.find(class_="dtp-meeting-title")
    meeting_title = title_elem.get_text(strip=True) if title_elem else None

    # Extract meeting date and time from <time> element
    time_elem = soup.find("time")
    meeting_date = None
    meeting_time = None
    if time_elem:
        datetime_attr = time_elem.get("datetime")
        if datetime_attr:
            try:
                meeting_date = datetime.strptime(datetime_attr, "%Y-%m-%d").date()
            except ValueError:
                logger.warning(f"Could not parse date: {datetime_attr}")

        # Extract time from text content (e.g., "February 11, 2026, 6:30 pm")
        time_text = time_elem.get_text(strip=True)
        # Extract the time portion (after the last comma)
        if "," in time_text:
            parts = time_text.split(",")
            if len(parts) >= 2:
                meeting_time = parts[-1].strip()

    # Extract venue info
    venue_elem = soup.find(class_="dtp-meeting-venue")
    venue = venue_elem.get_text(strip=True) if venue_elem else None

    address_elem = soup.find(class_="dtp-meeting-address1")
    address = address_elem.get_text(strip=True) if address_elem else None

    zipcode_elem = soup.find(class_="dtp-meeting-zipcode")
    zipcode = zipcode_elem.get_text(strip=True) if zipcode_elem else None

    # Extract documents (agendas and minutes)
    documents = _extract_documents(soup)

    return {
        "committee_name": committee_name,
        "meeting_title": meeting_title,
        "meeting_date": meeting_date,
        "meeting_time": meeting_time,
        "venue": venue,
        "address": address,
        "zipcode": zipcode,
        "documents": documents,
    }


def _extract_documents(soup):
    """Extract agenda and minutes documents from meeting detail page.

    Args:
        soup (BeautifulSoup): Parsed HTML

    Returns:
        list: List of dicts with 'type', 'url', 'name' keys
    """
    documents = []
    seen_urls = set()

    section_types = [
        ("dtp-meeting-agenda", "agenda"),
        ("dtp-meeting-minutes", "minutes"),
    ]

    for css_class, doc_type in section_types:
        header = soup.find("h3", class_=css_class)
        if not header:
            continue
        # Collect sibling elements after the header until the next h3
        for sibling in header.next_siblings:
            if sibling.name == "h3":
                break
            if sibling.name == "a":
                links = [sibling]
            elif hasattr(sibling, "find_all"):
                links = sibling.find_all("a", href=True)
            else:
                continue
            for link in links:
                href = link.get("href")
                if not href:
                    continue
                if href.lower().endswith(".pdf") or "application/pdf" in link.get("title", ""):
                    if href not in seen_urls:
                        seen_urls.add(href)
                        documents.append(
                            {
                                "type": doc_type,
                                "url": href,
                                "name": link.get_text(strip=True),
                            }
                        )

    return documents


def parse_meeting_datetime(date_str, time_str):
    """Parse meeting date and time strings into datetime object.

    Args:
        date_str (str): Date string (e.g., "2026-02-11" or date object)
        time_str (str): Time string (e.g., "6:30 pm")

    Returns:
        datetime: Combined datetime object
    """
    if isinstance(date_str, str):
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None
    else:
        date_obj = date_str

    # Parse time if available
    if time_str:
        try:
            time_obj = datetime.strptime(time_str, "%I:%M %p").time()
        except ValueError:
            # Try other formats
            try:
                time_obj = datetime.strptime(time_str, "%I:%M%p").time()
            except ValueError:
                logger.warning(f"Could not parse time: {time_str}")
                time_obj = None
    else:
        time_obj = None

    if time_obj:
        return datetime.combine(date_obj, time_obj)
    else:
        return datetime.combine(date_obj, datetime.min.time())


def extract_detail_id_from_url(url):
    """Extract detail ID from meeting detail URL.

    Args:
        url (str): URL like https://finetownny.gov/meetings/detail/30

    Returns:
        str: Detail ID (e.g., "30")
    """
    return url.split("/meetings/detail/")[-1].rstrip("/")
