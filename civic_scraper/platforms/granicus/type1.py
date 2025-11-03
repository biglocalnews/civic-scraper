from bs4 import BeautifulSoup
import re
import html  # For unescaping HTML entities in URLs
import logging
from .base import GranicusBaseScraper  # Assuming base.py is in the same directory

logger = logging.getLogger(__name__)


class GranicusType1Scraper(GranicusBaseScraper):
    """
    Scraper for Granicus Type 1 URLs.
    - Year selector TabbedPanel is INSIDE the div with class CollapsiblePanelTab's content.
    - Multiple CollapsiblePanelTabs for different committees.
    Example: "https://cityofbradenton.granicus.com/ViewPublisher.php?view_id=1" with CollapsiblePanelTab = "City Council"
    """

    def _extract_meeting_details_internal(
        self, soup: BeautifulSoup, panel_name: str | None
    ) -> list[dict]:
        if not panel_name:
            logger.warning(
                f"{self.__class__.__name__}: This scraper type requires a panel_name to identify the correct committee section."
            )
            return []

        meetings = []
        panel_found = False
        target_panel_content_div = None
        panels_headers = soup.find_all(
            "div", class_=["CollapsiblePanelTab", "CollapsiblePanelTabNotSelected"]
        )
        if not panels_headers:
            logger.info(
                f"{self.__class__.__name__}: No 'CollapsiblePanelTab' or 'CollapsiblePanelTabNotSelected' divs found on the page for panel '{panel_name}'."
            )
            return []
        for panel_header_div in panels_headers:
            text_container = panel_header_div.find(["a", "h3", "span", "div"])
            current_panel_name_text = panel_header_div.get_text(strip=True)
            if text_container:
                current_panel_name_text = text_container.get_text(strip=True)
            if current_panel_name_text == panel_name:
                panel_found = True
                content_div = panel_header_div.find_next_sibling(
                    "div", class_="CollapsiblePanelContent"
                )
                if content_div:
                    target_panel_content_div = content_div
                else:
                    logger.warning(
                        f"{self.__class__.__name__}: Panel '{panel_name}' header found, but its 'CollapsiblePanelContent' sibling is missing."
                    )
                break
        if not panel_found:
            logger.warning(
                f"{self.__class__.__name__}: Panel '{panel_name}' not found."
            )
            available_panels = []
            for p_header in panels_headers:
                text_c = p_header.find(["a", "h3", "span", "div"])
                available_panels.append(
                    text_c.get_text(strip=True)
                    if text_c
                    else p_header.get_text(strip=True)
                )
            if available_panels:
                logger.info(
                    f"{self.__class__.__name__}: Available panels: {available_panels}"
                )
            else:
                logger.info(
                    f"{self.__class__.__name__}: No CollapsiblePanelTab elements found on the page."
                )
            return []
        if not target_panel_content_div:
            logger.warning(
                f"{self.__class__.__name__}: Panel '{panel_name}' found but its content div (CollapsiblePanelContent) is missing or could not be identified."
            )
            return []
        # STRICT: Type 1 requires year tabs (a 'TabbedPanels' div) INSIDE the panel's content div.
        tabbed_panels_container_div = target_panel_content_div.find(
            "div", class_="TabbedPanels"
        )
        if not tabbed_panels_container_div:
            logger.info(
                f"{self.__class__.__name__}: Panel '{panel_name}' content found, but the characteristic 'TabbedPanels' div (for year selection) was NOT found *within* this panel's content. This structure does not match Type 1 for this panel."
            )
            return []  # STRICT: No fallback allowed!

        # Process the TabbedPanels structure found within tabbed_panels_container_div
        year_tabs_ul = tabbed_panels_container_div.find(
            "ul", class_="TabbedPanelsTabGroup"
        )
        year_contents_group_div = tabbed_panels_container_div.find(
            "div", class_="TabbedPanelsContentGroup"
        )

        if year_tabs_ul and year_contents_group_div:
            year_tabs_li_elements = year_tabs_ul.find_all(
                "li", class_="TabbedPanelsTab", recursive=False
            )
            year_content_divs = year_contents_group_div.find_all(
                "div", class_="TabbedPanelsContent", recursive=False
            )

            if not year_tabs_li_elements or not year_content_divs:
                logger.warning(
                    f"{self.__class__.__name__}: Panel '{panel_name}' - 'TabbedPanels' structure has TabGroup/ContentGroup but they are empty or missing <li> tabs / content divs."
                )
                return []

            if len(year_tabs_li_elements) != len(year_content_divs):
                logger.warning(
                    f"{self.__class__.__name__}: Mismatch between number of year tabs ({len(year_tabs_li_elements)}) and content sections ({len(year_content_divs)}) in panel '{panel_name}'. Processing based on shorter list."
                )

            for i in range(min(len(year_tabs_li_elements), len(year_content_divs))):
                year_tab_li = year_tabs_li_elements[i]
                content_for_year_div = year_content_divs[i]
                year_text = year_tab_li.get_text(strip=True)
                logger.info(
                    f"{self.__class__.__name__}: Processing year tab '{year_text}' for panel '{panel_name}'"
                )

                table = content_for_year_div.find("table", class_="listingTable")
                if table:
                    for row in table.find_all(
                        "tr", class_=["listingRow", "listingRowAlt"]
                    ):
                        meeting = self._extract_meeting_from_row(row, year_text)
                        if meeting:
                            meetings.append(meeting)
                else:
                    logger.warning(
                        f"{self.__class__.__name__}: No listingTable found in content for year '{year_text}' in panel '{panel_name}'."
                    )
        else:
            # Case: 'TabbedPanels' div exists, but no TabGroup/ContentGroup.
            # This might mean a single listingTable directly within 'TabbedPanels'.
            table = tabbed_panels_container_div.find("table", class_="listingTable")
            if table:
                logger.info(
                    f"{self.__class__.__name__}: Panel '{panel_name}' has 'TabbedPanels' div but no distinct year groups (TabGroup/ContentGroup). Processing single listingTable found directly within 'TabbedPanels' div."
                )
                for row in table.find_all("tr", class_=["listingRow", "listingRowAlt"]):
                    meeting = self._extract_meeting_from_row(row, "DefaultYear")
                    if meeting:
                        meetings.append(meeting)
            else:
                logger.warning(
                    f"{self.__class__.__name__}: 'TabbedPanels' div found but no year groups or listingTable present for panel '{panel_name}'."
                )

        logger.info(
            f"{self.__class__.__name__}: Extracted {len(meetings)} meetings for panel '{panel_name}'."
        )
        return meetings

    def _extract_meeting_from_row(self, row_element, year_context: str) -> dict | None:
        """
        Helper to extract meeting details from a table row (<tr> element).
        'year_context' is the year from the tab, used for logging/context if needed.
        """
        cells = row_element.find_all("td")  # listItem class might not always be on td
        if not cells or len(cells) < 2:  # Need at least name and date
            logger.debug(f"Skipping row, not enough cells: {row_element.prettify()}")
            return None

        meeting_data = {}
<<<<<<< HEAD
        # Base extraction
        name_cell_text = cells[0].get_text(separator=' ', strip=True).replace('\xa0', ' ')
        date_cell_text = cells[1].get_text(strip=True).replace('\xa0', ' ')

        meeting_data['name'] = name_cell_text
        meeting_data['date'] = date_cell_text

        # Heuristic: Some tables shift so that the real date is stored in the name cell and
        # the 'date' cell starts the asset columns (showing words like 'Agenda', 'Minutes', or is blank).
        # Detect if date cell is NOT a date but looks like an asset label. If so, treat name cell as date
        # and keep meeting name as the date string (handled later by recovery logic in base).
        non_date_tokens = {"agenda", "minutes", "video", "packet", "agenda packet"}
        looks_like_date = bool(re.search(r'[0-9]{4}|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b', date_cell_text, re.I)) and any(ch.isdigit() for ch in date_cell_text)
        if not looks_like_date:
            token_lower = date_cell_text.strip().lower()
            if token_lower in non_date_tokens or token_lower == '' or token_lower == '—':
                meeting_data['suspected_column_shift'] = True
                # In these cases, the date will be parsed from 'name' via fallback. Mark date as placeholder.
                meeting_data['date'] = token_lower if token_lower else 'Agenda'  # preserve token for logging
            else:
                meeting_data['suspected_column_shift'] = False
        else:
            meeting_data['suspected_column_shift'] = False
        
=======
        # Name is usually in the first cell
        meeting_data["name"] = (
            cells[0].get_text(separator=" ", strip=True).replace("\xa0", " ")
        )
        # Date is usually in the second cell
        meeting_data["date"] = cells[1].get_text(strip=True).replace("\xa0", " ")

>>>>>>> master
        # Try to get a source for meeting_id (e.g. clip_id, event_id)
        meeting_id_source = ""
        all_links_in_row = row_element.find_all("a", href=True)
        for link_tag in all_links_in_row:
            href = link_tag["href"]
            # Common identifiers for meetings in Granicus
            clip_id_match = re.search(
                r"[?&](?:clip_id|event_id|meeting_id)=(\d+)", href, re.IGNORECASE
            )
            if clip_id_match:
                meeting_id_source = clip_id_match.group(1)
                break
        meeting_data["meeting_id_source"] = meeting_id_source

        # Link extraction: Agenda, Minutes, Video, Packet
        # This needs to be flexible as column order and link text vary.
<<<<<<< HEAD
        
        # Decide starting index for asset columns. If a shift is suspected, assets begin at cell 1.
        # Normal layout: [0]=Name, [1]=Date, [2]=Agenda, [3]=Minutes, [4]=Video, [5]=Packet
        # Shifted layout: [0]=Date (stored as name), [1]=Agenda, [2]=Minutes, etc.
        asset_start_index = 2
        if meeting_data.get('suspected_column_shift'):
            asset_start_index = 1

        # Agenda column
        if len(cells) > asset_start_index:
            agenda_cell_content = cells[asset_start_index]
            agenda_link_tag = agenda_cell_content.find('a', href=True, text=re.compile(r'Agenda', re.I))
            if not agenda_link_tag:
                agenda_link_tag = agenda_cell_content.find('a', href=True)
            if agenda_link_tag:
                meeting_data['agenda_url'] = agenda_link_tag['href']

        # Minutes column
        minutes_index = asset_start_index + 1
        if len(cells) > minutes_index:
            minutes_cell_content = cells[minutes_index]
            minutes_link_tag = minutes_cell_content.find('a', href=True, text=re.compile(r'Minutes', re.I))
            if not minutes_link_tag:
                minutes_link_tag = minutes_cell_content.find('a', href=True)
=======

        # Agenda (often in cell 2 or by text 'Agenda')
        if len(cells) > 2:  # Cell index 2
            agenda_cell_content = cells[2]
            agenda_link_tag = agenda_cell_content.find(
                "a", href=True, text=re.compile(r"Agenda", re.I)
            )
            if (
                not agenda_link_tag
            ):  # If no text match, assume link in cell 2 is agenda if it's a link
                agenda_link_tag = agenda_cell_content.find("a", href=True)
            if agenda_link_tag:
                meeting_data["agenda_url"] = agenda_link_tag["href"]

        # Minutes (often in cell 3 or by text 'Minutes')
        if len(cells) > 3:  # Cell index 3
            minutes_cell_content = cells[3]
            minutes_link_tag = minutes_cell_content.find(
                "a", href=True, text=re.compile(r"Minutes", re.I)
            )
            if (
                not minutes_link_tag
            ):  # If no text match, assume link in cell 3 is minutes if it's a link
                minutes_link_tag = minutes_cell_content.find("a", href=True)
>>>>>>> master
            if minutes_link_tag:
                meeting_data["minutes_url"] = minutes_link_tag["href"]

        # Video (search all links in row for common video patterns)
        for link_tag in all_links_in_row:
            href = link_tag["href"]
            link_text = link_tag.get_text(strip=True)
            # Common patterns for video links
            if (
                "ViewEvent.php" in href
                or "MediaPlayer.php" in href
                or re.search(r"Video|Watch|Media|View Event", link_text, re.I)
                or (
                    link_tag.find("img")
                    and link_tag.find("img").get("alt", "").lower()
                    in ["video", "play video"]
                )
            ):

                video_url_candidate = href  # Default to href
                if href and href.lower().startswith("javascript:void(0)"):
                    onclick_attr = link_tag.get("onclick")
                    if onclick_attr:
                        # Regex to capture URL from window.open('URL', ...) or window.open("URL", ...)
                        url_match = re.search(
                            r"window\.open\s*\(\s*['\"]([^'\"]+)['\"].*?\)",
                            onclick_attr,
                        )
                        if url_match:
                            raw_onclick_url = url_match.group(1).strip()
                            video_url_candidate = html.unescape(
                                raw_onclick_url
                            )  # Use unescaped onclick URL

                meeting_data["video_url"] = video_url_candidate
                break  # Take the first likely video link

        # Packet (search all links for 'Packet')
        for link_tag in all_links_in_row:
            if re.search(r"Packet|Agenda Packet", link_tag.get_text(strip=True), re.I):
                meeting_data["packet_url"] = link_tag["href"]
                break

        # Time (often embedded in name or date, or a separate column if available)
        # For now, _parse_date_time handles time extraction from date_str if not explicitly passed.
        # If a dedicated time column exists, it would be handled here.
        # Example: if len(cells) > 4 and "time_column_header" in header: meeting_data['time'] = cells[4].get_text...

        # Try to extract time from name or date cell text if not found by _parse_date_time implicitly
        # This is a fallback, _parse_date_time in base class already tries this.
        combined_text_for_time = (
            meeting_data.get("name", "") + " " + meeting_data.get("date", "")
        )
        time_match = re.search(
            r"(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)", combined_text_for_time
        )
        if time_match and not meeting_data.get(
            "time"
        ):  # Only set if not already found by _parse_date_time
            meeting_data["time"] = time_match.group(1)

        return meeting_data
