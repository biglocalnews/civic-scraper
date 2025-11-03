from bs4 import BeautifulSoup
import re
import html  # For unescaping HTML entities in URLs
import logging
from .base import GranicusBaseScraper  # Assuming base.py is in the same directory

logger = logging.getLogger(__name__)


class GranicusType3Scraper(GranicusBaseScraper):
    """
    Scraper for Granicus Type 3 URLs.
    - No CollapsiblePanelTab for committee selection within the page structure that this scraper interacts with.
    - A TabbedPanel for year selection is usually present (e.g., id='TabbedPanel1' or class='TabbedPanels').
    - If year tabs exist, it iterates through them. Otherwise, it looks for tables directly on the page.
    - The `panel_name` argument is used for the 'committee_name' field in the output metadata,
      but not typically for filtering content on the page itself by this scraper type.
    Example: "https://sacramento.granicus.com/viewpublisher.php?view_id=22"
    """

    def _extract_meeting_details_internal(
        self, soup: BeautifulSoup, panel_name: str | None
    ) -> list[dict]:
        meetings = []

        # Look for a main TabbedPanel structure for years.
        # Common IDs/classes: TabbedPanel1, TabbedPanels1, or just class TabbedPanels
        year_tab_panel_container = soup.find(
            "div", id=re.compile(r"TabbedPanels?1", re.I)
        )
        if not year_tab_panel_container:
            year_tab_panel_container = soup.find("div", class_="TabbedPanels")

        content_sections_to_parse = []
        year_context_list = []

        if year_tab_panel_container:
            logger.info(
                f"{self.__class__.__name__}: Found a TabbedPanel structure. Processing year tabs."
            )
            year_tabs_ul = year_tab_panel_container.find(
                "ul", class_="TabbedPanelsTabGroup"
            )
            year_contents_group_div = year_tab_panel_container.find(
                "div", class_="TabbedPanelsContentGroup"
            )

            if year_tabs_ul and year_contents_group_div:
                year_tabs_li_elements = year_tabs_ul.find_all(
                    "li", class_="TabbedPanelsTab", recursive=False
                )
                year_content_divs = year_contents_group_div.find_all(
                    "div", class_="TabbedPanelsContent", recursive=False
                )

                if (
                    len(year_tabs_li_elements) == len(year_content_divs)
                    and year_tabs_li_elements
                ):
                    for i in range(len(year_tabs_li_elements)):
                        year_text = year_tabs_li_elements[i].get_text(strip=True)
                        content_sections_to_parse.append(year_content_divs[i])
                        year_context_list.append(year_text)
                    logger.info(
                        f"{self.__class__.__name__}: Identified {len(content_sections_to_parse)} year content sections from tabs."
                    )
                elif (
                    year_content_divs
                ):  # If tabs don't match content divs, process content divs with unknown year
                    logger.warning(
                        f"{self.__class__.__name__}: Mismatch or missing year tabs. Processing content divs with 'UnknownYear'."
                    )
                    for content_div in year_content_divs:
                        content_sections_to_parse.append(content_div)
                        year_context_list.append("UnknownYear")
                else:  # No clear year tab structure within the TabbedPanel
                    logger.info(
                        f"{self.__class__.__name__}: TabbedPanel found, but no distinct year TabGroup/ContentGroup. Will look for tables directly within it or page."
                    )
                    content_sections_to_parse.append(
                        year_tab_panel_container
                    )  # Parse the whole container
                    year_context_list.append("DefaultYear")
            else:  # No TabGroup/ContentGroup, treat the whole TabbedPanel container as one section
                logger.info(
                    f"{self.__class__.__name__}: TabbedPanel found, but no TabGroup/ContentGroup. Parsing TabbedPanel as a single section."
                )
                content_sections_to_parse.append(year_tab_panel_container)
                year_context_list.append("DefaultYear")
        else:
            logger.info(
                f"{self.__class__.__name__}: No main TabbedPanel structure for years found. Will search for tables directly on the page."
            )
            # If no year tabs, the whole soup is the context, or look for any listingTable directly
            content_sections_to_parse.append(soup)  # Parse the entire page content
            year_context_list.append("DefaultYear")  # Default year context

        if not content_sections_to_parse:
            logger.warning(
                f"{self.__class__.__name__}: No content sections identified for parsing."
            )
            return []

        for idx, content_section in enumerate(content_sections_to_parse):
            current_year_context = year_context_list[idx]
            logger.info(
                f"{self.__class__.__name__}: Parsing section with year context: {current_year_context}"
            )

            # Find all listing tables within this section
            tables_in_section = content_section.find_all("table", class_="listingTable")
            if not tables_in_section:
                # Fallback: some sites might use slightly different table classes or structures
                tables_in_section = content_section.find_all(
                    "table", id=re.compile(r"pastEvents|upcomingEvents", re.I)
                )
                if tables_in_section:
                    logger.info(
                        f"{self.__class__.__name__}: Found tables with IDs like pastEvents/upcomingEvents."
                    )

            if not tables_in_section:
                logger.debug(
                    f"{self.__class__.__name__}: No listingTable (or common alternatives) found in content section for year '{current_year_context}'."
                )
                continue

            for table_num, table in enumerate(tables_in_section):
                logger.info(
                    f"{self.__class__.__name__}: Processing table {table_num + 1} in year '{current_year_context}'."
                )
                # Rows can have classes 'listingRow', 'listingRowAlt', or just be <tr> in <tbody>
                # Also seen 'odd' and 'even' for row classes
                rows = table.find_all(
                    "tr", class_=re.compile(r"listingRow|listingRowAlt|even|odd", re.I)
                )
                if not rows:  # If no specific classes, try all <tr> within a <tbody>
                    tbody = table.find("tbody")
                    if tbody:
                        rows = tbody.find_all("tr")
                    else:  # Or all <tr> directly under the table if no tbody
                        rows = table.find_all("tr")

                if not rows:
                    logger.debug(
                        f"{self.__class__.__name__}: No processable rows found in table {table_num + 1} for year '{current_year_context}'."
                    )
                    continue

                # Try to identify headers to map columns, if possible (more robust)
                header_row = table.find(
                    "tr", class_=re.compile(r"header|heading", re.I)
                )  # Common header row classes
                headers_text = []
                if header_row:
                    headers_text = [
                        th.get_text(strip=True).lower()
                        for th in header_row.find_all(["th", "td"])
                    ]

                for row_idx, row in enumerate(rows):
                    if row == header_row:  # Skip header row if identified
                        continue

                    cells = row.find_all("td")
                    if (
                        not cells or len(cells) < 2
                    ):  # Need at least name and date typically
                        logger.debug(
                            f"Skipping row {row_idx+1} in table {table_num+1} (year {current_year_context}): not enough cells."
                        )
                        continue

                    meeting_data = {}

                    # Try to map cells based on headers if available
                    name_col_idx, date_col_idx = 0, 1  # Default column indices

                    if headers_text:
                        try:
                            name_col_idx = (
                                headers_text.index("name")
                                if "name" in headers_text
                                else 0
                            )
                            date_col_idx = (
                                headers_text.index("date")
                                if "date" in headers_text
                                else 1
                            )
                        except ValueError:  # Header not found, stick to defaults
                            pass

                    meeting_data["name"] = (
                        cells[name_col_idx]
                        .get_text(separator=" ", strip=True)
                        .replace("\xa0", " ")
                    )
                    meeting_data["date"] = (
                        cells[date_col_idx].get_text(strip=True).replace("\xa0", " ")
                    )

                    # Meeting ID source
                    meeting_id_source = ""
                    all_links_in_row = row.find_all("a", href=True)
                    for link_tag in all_links_in_row:
                        href = link_tag["href"]
                        id_match = re.search(
                            r"[?&](?:clip_id|event_id|meeting_id|item_id)=(\d+)",
                            href,
                            re.IGNORECASE,
                        )
                        if id_match:
                            meeting_id_source = id_match.group(1)
                            break
                    meeting_data["meeting_id_source"] = meeting_id_source

                    # Links (Agenda, Minutes, Video, Packet) - search all links in the row
                    self._extract_links_from_row_links(
                        all_links_in_row, meeting_data, cells, headers_text
                    )

                    # Time (attempt extraction, base class _parse_date_time also tries this)
                    if not meeting_data.get("time"):  # Only if not already parsed
                        combined_text_for_time = (
                            meeting_data.get("name", "")
                            + " "
                            + meeting_data.get("date", "")
                        )
                        time_match_row = re.search(
                            r"(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)",
                            combined_text_for_time,
                        )
                        if time_match_row:
                            meeting_data["time"] = time_match_row.group(1)

                    if meeting_data.get("name") and meeting_data.get("date"):
                        meetings.append(meeting_data)

        logger.info(
            f"{self.__class__.__name__}: Extracted {len(meetings)} meetings for panel '{panel_name if panel_name else 'N/A'}'."
        )
        return meetings

    def _extract_links_from_row_links(
        self,
        all_links_in_row: list,
        meeting_data: dict,
        cells: list,
        headers_text: list,
    ):
        """Helper to extract various document links from all hyperlinks in a row."""
        # Initialize/clear link fields
        meeting_data["agenda_url"] = None
        meeting_data["minutes_url"] = None
        meeting_data["video_url"] = None
        meeting_data["packet_url"] = None  # Prioritize links with specific text
        for link_tag in all_links_in_row:
            href = self._normalize_url_local(link_tag.get("href", ""))
            link_text = link_tag.get_text(strip=True).lower()

            # Video - check for MediaPlayer URLs, onclick handlers, or video-related keywords
            if not meeting_data.get("video_url"):
                # Check for JavaScript onclick handlers (common in Sacramento-style sites)
                onclick_attr = link_tag.get("onclick", "")
                video_url_candidate = None

                if onclick_attr and "mediaplayer.php" in onclick_attr.lower():
                    # Extract URL from onclick="window.open('URL',...)"
                    url_match = re.search(
                        r"window\.open\s*\(\s*['\"]([^'\"]+)['\"].*?\)", onclick_attr
                    )
                    if url_match:
                        raw_onclick_url = url_match.group(1).strip()
                        unescaped_onclick_url = html.unescape(raw_onclick_url)
                        video_url_candidate = self._normalize_url_local(
                            unescaped_onclick_url
                        )
                elif (
                    "viewevent.php" in href.lower() or "mediaplayer.php" in href.lower()
                ):
                    video_url_candidate = href
                elif any(
                    keyword in link_text
                    for keyword in [
                        "video",
                        "watch",
                        "media",
                        "view event",
                        "recording",
                        "live",
                    ]
                ):
                    video_url_candidate = href

                if video_url_candidate:
                    meeting_data["video_url"] = video_url_candidate

            # Audio - check for MP3, audio files, or audio-related keywords
            if not meeting_data.get("video_url"):  # Use video_url for audio files too
                if (
                    href
                    and (
                        href.lower().endswith(".mp3")
                        or href.lower().endswith(".mp4")
                        or href.lower().endswith(".wav")
                        or "audio" in href.lower()
                    )
                ) or any(
                    keyword in link_text
                    for keyword in ["mp3", "audio", "sound", "recording"]
                ):
                    meeting_data["video_url"] = href

            # Agenda - check for AgendaViewer URLs or "agenda" text
            if not meeting_data.get("agenda_url"):
                if (
                    "agendaviewer.php" in href.lower()
                    or (link_text == "agenda" or "agenda" in link_text)
                    and not any(
                        keyword in link_text for keyword in ["packet", "minutes"]
                    )
                ):
                    meeting_data["agenda_url"] = href

            # Minutes - check for MinutesViewer URLs or "minutes" text
            if not meeting_data.get("minutes_url"):
                if "minutesviewer.php" in href.lower() or (
                    "minutes" in link_text and "agenda" not in link_text
                ):
                    meeting_data["minutes_url"] = href

            # Packet - check for packet-related keywords
            if not meeting_data.get("packet_url"):
                if any(
                    keyword in link_text
                    for keyword in ["packet", "agenda packet", "supplemental"]
                ):
                    meeting_data["packet_url"] = href

        # Fallback: If links are not clearly labeled, try to infer from column headers if available
        if headers_text and (
            not meeting_data["agenda_url"] or not meeting_data["minutes_url"]
        ):
            for i, header in enumerate(headers_text):
                if i < len(cells):
                    cell_links = cells[i].find_all("a", href=True)
                    if not cell_links:
                        continue

                    cell_href = self._normalize_url_local(
                        cell_links[0]["href"]
                    )  # Take first link in cell

                    if (
                        not meeting_data["agenda_url"]
                        and "agenda" in header
                        and "packet" not in header
                    ):
                        if cell_href not in [
                            meeting_data.get("packet_url"),
                            meeting_data.get("minutes_url"),
                            meeting_data.get("video_url"),
                        ]:
                            meeting_data["agenda_url"] = cell_href
                    elif not meeting_data["minutes_url"] and "minutes" in header:
                        if cell_href not in [
                            meeting_data.get("agenda_url"),
                            meeting_data.get("packet_url"),
                            meeting_data.get("video_url"),
                        ]:
                            meeting_data["minutes_url"] = cell_href
                    elif not meeting_data["packet_url"] and "packet" in header:
                        if cell_href not in [
                            meeting_data.get("agenda_url"),
                            meeting_data.get("minutes_url"),
                            meeting_data.get("video_url"),
                        ]:
                            meeting_data["packet_url"] = cell_href
                    elif not meeting_data["video_url"] and any(
                        keyword in header for keyword in ["video", "media", "watch"]
                    ):
                        if cell_href not in [
                            meeting_data.get("agenda_url"),
                            meeting_data.get("minutes_url"),
                            meeting_data.get("packet_url"),
                        ]:
                            meeting_data["video_url"] = cell_href

        # If agenda and minutes are still the same, clear minutes (common issue with generic links)
        if meeting_data.get("agenda_url") and meeting_data.get(
            "agenda_url"
        ) == meeting_data.get("minutes_url"):
            if (
                "minutesviewer.php" not in (meeting_data.get("minutes_url", "")).lower()
            ):  # If minutes is not specific
                meeting_data["minutes_url"] = None

    def _normalize_url_local(self, url: str) -> str | None:
        """
        Normalize URLs by ensuring they have a proper scheme, relative to the base_url.
        This is a local helper; the main _make_absolute_url is called during transformation.
        """
        if not url:
            return None
        if url.startswith("//"):
            # Assume https for scheme-relative URLs
            return f"https:{url}"
        # If it's already absolute, return as is.
        if url.startswith(("http://", "https://")):
            return url
        # Otherwise, it's relative, _make_absolute_url in base class will handle it later
        return url

    def requires_panel_name(self) -> bool:
        """
        Type 3 scraper typically does not require a panel name for parsing the page,
        as it often scrapes a single main list of meetings or iterates through year tabs
        without committee-specific collapsible panels in the same way as other types.
        The panel_name is used for metadata.
        """
        return False  # Overrides the base class default
