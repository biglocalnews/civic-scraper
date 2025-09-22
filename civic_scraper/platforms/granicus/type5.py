import logging
import re
from bs4 import BeautifulSoup
from .base import GranicusBaseScraper

logger = logging.getLogger(__name__)

class GranicusType5Scraper(GranicusBaseScraper):
    """
    Scraper for Granicus 'Type 5' (proposed) single-committee/year pages:
    Characteristics observed (e.g., Sarasota County Commission page):
      - No CollapsiblePanelTab or TabbedPanels structure.
      - One or more plain tables with classes "listingtable", "listingtable2" (lowercase) and sometimes an archived section.
      - Tables contain <th id="name"> and <th id="date"> or similar headers.
      - Multiple year links are rendered as plain <a href=...view_id=XX>YYYY</a> inline (not JavaScript tabs).
      - Page represents *one* committee; committee name appears in header text (e.g., "County Commissioners meetings").
    This scraper processes all qualifying tables present on the page.
    """

    def requires_panel_name(self) -> bool:
        # Committee name provided by site configuration or can be inferred; we accept provided committee for labeling, but don't require for extraction.
        return False

    # Use base class extract_and_process_meetings for transformation; only supply raw dicts via _extract_meeting_details_internal

    # --- Internal helpers ---
    def _extract_meeting_details_internal(self, soup: BeautifulSoup, panel_name: str | None):
        # Collect candidate tables (case-insensitive) for classes that often appear.
        candidate_class_patterns = [
            re.compile(r'listingtable2?', re.I),  # listingtable or listingtable2 (any case)
            re.compile(r'rsslistingtable', re.I),
        ]
        seen = set()
        tables = []
        for pattern in candidate_class_patterns:
            for tbl in soup.find_all('table', class_=pattern):
                # Deduplicate by object id to avoid repeats from overlapping patterns
                if id(tbl) not in seen:
                    seen.add(id(tbl))
                    tables.append(tbl)
        if not tables:
            logger.info(
                f"{self.__class__.__name__}: No listing tables found for Type5 structure (searched patterns: listingtable*, rsslistingtable). "
                "Will return empty so caller can optionally fallback to Type3."
            )
            return []
        logger.info(
            f"{self.__class__.__name__}: Found {len(tables)} candidate tables for Type5 parsing (case-insensitive match)."
        )
        meetings = []
        for idx, table in enumerate(tables):
            header_cells = table.find_all('th')
            headers_text_lower = [h.get_text(strip=True).lower() for h in header_cells]
            # Identify likely name/date columns
            name_index = 0
            date_index = 1 if len(header_cells) > 1 else None
            for i, txt in enumerate(headers_text_lower):
                if 'date' in txt:
                    date_index = i
                if any(k in txt for k in ['meeting', 'name', 'commissioners']) and name_index == 0:
                    name_index = i
            body_rows = table.find_all('tr')
            processed_rows = 0
            for row in body_rows:
                # Skip header-like rows
                if row.find('th'):
                    continue
                tds = row.find_all('td')
                if len(tds) < 2:
                    continue
                processed_rows += 1
                name_text = tds[name_index].get_text(separator=' ', strip=True).replace('\xa0', ' ')
                date_text = tds[date_index].get_text(separator=' ', strip=True).replace('\xa0', ' ') if date_index is not None else ''
                # Skip empty or decorative rows
                if not name_text or not date_text:
                    continue
                meeting_dict = {
                    'name': name_text,
                    'date': date_text,
                }
                # Collect all links for this row
                links = row.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    text_l = link.get_text(strip=True).lower()
                    if 'agenda' in text_l and 'packet' not in text_l:
                        meeting_dict.setdefault('agenda_url', href)
                    elif 'packet' in text_l:
                        meeting_dict.setdefault('packet_url', href)
                    elif 'minutes' in text_l:
                        meeting_dict.setdefault('minutes_url', href)
                    elif any(k in text_l for k in ['video','watch']) or 'mediaplayer.php' in href.lower():
                        meeting_dict.setdefault('video_url', href)
                    # meeting id source
                    id_match = re.search(r'[?&](?:clip_id|event_id|meeting_id|item_id)=(\d+)', href, re.I)
                    if id_match:
                        meeting_dict.setdefault('meeting_id_source', id_match.group(1))
                # Attempt coarse time detection (may be in the date cell)
                time_match = re.search(r'(\d{1,2}[:.]\d{2}\s*(?:AM|PM)|\d{1,2}\s*(?:AM|PM))', date_text, re.I)
                if time_match:
                    meeting_dict['time'] = time_match.group(1)
                meetings.append(meeting_dict)
            logger.info(f"{self.__class__.__name__}: Table {idx+1} processed {processed_rows} data rows -> {len(meetings)} cumulative meetings.")
        logger.info(f"{self.__class__.__name__}: Extracted total {len(meetings)} meetings.")
        return meetings

