from bs4 import BeautifulSoup
import re
import html # For unescaping HTML entities in URLs
import logging
from .base import GranicusBaseScraper # Assuming base.py is in the same directory

logger = logging.getLogger(__name__)

class GranicusType2Scraper(GranicusBaseScraper):
    """
    Scraper for Granicus Type 2 URLs.
    - Year selector TabbedPanel is OUTSIDE (usually above) the div with class CollapsiblePanelTab.
    - Multiple CollapsiblePanelTabs for committees.
    - Under the selected panel's content (within a specific year's tab content), there is a table with class listingTable.
    - This scraper will get meetings from all available years by examining the year tabs.
    Example: "https://marysvilleca.granicus.com/ViewPublisher.php?view_id=1" with CollapsiblePanelTab = "City Council"
    """
    def _extract_meeting_details_internal(self, soup: BeautifulSoup, panel_name: str | None) -> list[dict]:
        if not panel_name:
            logger.warning(f"{self.__class__.__name__}: This scraper type requires a panel_name to identify the correct committee section.")
            return []
        
        meetings = []
        
        # Step 1: Find the main TabbedPanel for year selection. This is usually at a higher level.
        # We look for the TabbedPanelsContentGroup that contains content for each year.
        main_tabbed_panels_content_group = soup.find('div', class_='TabbedPanelsContentGroup')

        if not main_tabbed_panels_content_group:
            logger.info(f"{self.__class__.__name__}: No 'TabbedPanelsContentGroup' (for years) found. This might not be a Type 2 structure, or the page structure is simpler.")
            # Fallback: Try to parse current view if no year tabs found.
            # This might happen if there's only one "year" of data or a different structure.
            logger.info(f"{self.__class__.__name__}: Attempting to parse current page view for panel '{panel_name}'.")
            # We need to find the specific panel_name's content without year tabs.
            all_collapsible_panels = soup.find_all('div', class_='CollapsiblePanel')
            panel_found_in_current_view = False
            for cp_panel in all_collapsible_panels:
                header_div = cp_panel.find(['div','h2','h3'], class_=['CollapsiblePanelTab', 'CollapsiblePanelTabNotSelected'])
                if header_div:
                    text_container = header_div.find(['a', 'h3', 'span', 'div'])
                    current_panel_name_text = text_container.get_text(strip=True) if text_container else header_div.get_text(strip=True)
                    if current_panel_name_text == panel_name:
                        panel_found_in_current_view = True
                        panel_content_div = cp_panel.find('div', class_='CollapsiblePanelContent')
                        if panel_content_div:
                            # Crucially, for Type 2, this panel_content_div should NOT have its own 'TabbedPanels' for years.
                            if panel_content_div.find('div', class_='TabbedPanels'):
                                logger.info(f"{self.__class__.__name__}: Panel '{panel_name}' content (in fallback) contains an inner 'TabbedPanels' div. This might be Type 1. Skipping for Type 2.")
                                return []
                            meetings.extend(self._extract_meetings_from_panel_content(panel_content_div, "DefaultYear"))
                        break
            if not panel_found_in_current_view:
                 logger.warning(f"{self.__class__.__name__}: Panel '{panel_name}' not found in current view (fallback).")
            return meetings


        # Get all year content divs from the main TabbedPanelsContentGroup
        year_content_divs = main_tabbed_panels_content_group.find_all('div', class_='TabbedPanelsContent', recursive=False)
        
        if not year_content_divs:
            logger.warning(f"{self.__class__.__name__}: 'TabbedPanelsContentGroup' found, but no 'TabbedPanelsContent' (year content) divs within it for panel '{panel_name}'.")
            return []

        # Try to get year names from corresponding tabs for context
        year_tabs_ul = soup.find('ul', class_='TabbedPanelsTabGroup') # Assuming it's a sibling or parent of ContentGroup
        year_tab_texts = ["UnknownYear"] * len(year_content_divs)
        if year_tabs_ul:
            year_tabs_li = year_tabs_ul.find_all('li', class_='TabbedPanelsTab', recursive=False)
            if len(year_tabs_li) == len(year_content_divs):
                year_tab_texts = [yt.get_text(strip=True) for yt in year_tabs_li]
            else:
                logger.warning(f"{self.__class__.__name__}: Mismatch in year tabs ({len(year_tabs_li)}) and year content divs ({len(year_content_divs)}). Using 'UnknownYear'.")

        panel_ever_found = False
        for i, year_content_div in enumerate(year_content_divs):
            year_context = year_tab_texts[i]
            logger.info(f"{self.__class__.__name__}: Processing year content for '{year_context}', looking for panel '{panel_name}'.")
            
            # Within this year's content, find the CollapsiblePanel for the target committee (panel_name)
            collapsible_panels_in_year = year_content_div.find_all('div', class_='CollapsiblePanel')
            
            found_panel_in_this_year = False
            for cp_panel in collapsible_panels_in_year:
                # Find the header of this collapsible panel
                header_div = cp_panel.find(['div','h2','h3'], class_=['CollapsiblePanelTab', 'CollapsiblePanelTabNotSelected']) # Common tags for panel headers
                if not header_div:
                    continue

                text_container = header_div.find(['a', 'h3', 'span', 'div']) # More specific text elements
                current_panel_name_text = text_container.get_text(strip=True) if text_container else header_div.get_text(strip=True)

                if current_panel_name_text == panel_name:
                    panel_ever_found = True
                    found_panel_in_this_year = True
                    panel_content_div = cp_panel.find('div', class_='CollapsiblePanelContent')
                    
                    if panel_content_div:
                        # Type 2 characteristic: The panel's content itself should NOT have another TabbedPanels (year selector).
                        # That would indicate a Type 1 structure within this year's section.
                        if panel_content_div.find('div', class_='TabbedPanels'):
                            logger.info(f"{self.__class__.__name__}: Panel '{panel_name}' (Year: {year_context}) content contains an inner 'TabbedPanels' div. This specific panel might be Type 1. Skipping for Type 2.")
                            continue # Skip this panel, might be Type 1

                        meetings.extend(self._extract_meetings_from_panel_content(panel_content_div, year_context))
                    else:
                        logger.warning(f"{self.__class__.__name__}: Panel '{panel_name}' (Year: {year_context}) found, but its 'CollapsiblePanelContent' is missing.")
                    break # Found the target panel for this year, move to next year
            
            if not found_panel_in_this_year:
                logger.info(f"{self.__class__.__name__}: Panel '{panel_name}' not found within year '{year_context}' content.")

        if not panel_ever_found:
            logger.warning(f"{self.__class__.__name__}: Panel '{panel_name}' was not found in any year's content.")
            # Log available panels if main structure was found but not the specific panel
            if year_content_divs: # Check if we actually iterated years
                available_panels_overall = set()
                for yc_div in year_content_divs:
                    for cp_p in yc_div.find_all('div', class_='CollapsiblePanel'):
                        h_div = cp_p.find(['div','h2','h3'], class_=['CollapsiblePanelTab', 'CollapsiblePanelTabNotSelected'])
                        if h_div:
                            txt_cont = h_div.find(['a', 'h3', 'span', 'div'])
                            available_panels_overall.add(txt_cont.get_text(strip=True) if txt_cont else h_div.get_text(strip=True))
                if available_panels_overall:
                    logger.info(f"{self.__class__.__name__}: Available panels found across years: {list(available_panels_overall)}")


        logger.info(f"{self.__class__.__name__}: Extracted a total of {len(meetings)} meetings for panel '{panel_name}' across all available years.")
        return meetings
    
    def _extract_meetings_from_panel_content(self, panel_content_div: BeautifulSoup, year_context: str) -> list[dict]:
        """
        Extracts meeting details from the content of a specific committee panel for a given year.
        This content is expected to contain a 'listingTable'.
        """
        meetings = []
        
        # Find the table with meeting information within this panel's content
        table = panel_content_div.find('table', class_='listingTable')
        if not table:
            logger.warning(f"{self.__class__.__name__}: listingTable not found in panel content for year '{year_context}'.")
            # Check for alternative structures if any, e.g. a list (though Type 2 is typically table-based)
            return meetings
            
        # Process each row in the table
        for row in table.find_all('tr', class_=['listingRow', 'listingRowAlt']):
            cells = row.find_all('td')
            if not cells or len(cells) < 2: # Need at least name and date
                continue

            meeting_data = {}
            meeting_data['name'] = cells[0].get_text(separator=' ', strip=True).replace('\xa0', ' ')
            meeting_data['date'] = cells[1].get_text(strip=True).replace('\xa0', ' ')
            # meeting_data['year_context'] = year_context # For debugging if needed

            meeting_id_source = ""
            all_links_in_row = row.find_all('a', href=True)
            for link_tag in all_links_in_row:
                href = link_tag['href']
                clip_id_match = re.search(r'[?&](?:clip_id|event_id|meeting_id)=(\d+)', href, re.IGNORECASE)
                if clip_id_match: 
                    meeting_id_source = clip_id_match.group(1)
                    break
            meeting_data['meeting_id_source'] = meeting_id_source

            # Extract links (agenda, minutes, video, packet)
            self._extract_links_from_cells(cells, all_links_in_row, meeting_data)
            
            # Extract time information (already attempted by base class's _parse_date_time)
            # Fallback if not picked up by _parse_date_time
            if not meeting_data.get('time'):
                combined_text_for_time = meeting_data.get('name', '') + " " + meeting_data.get('date', '')
                time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)', combined_text_for_time)
                if time_match: 
                    meeting_data['time'] = time_match.group(1)

            if meeting_data.get('name') and meeting_data.get('date'):
                meetings.append(meeting_data)
                
        return meetings

    def _extract_links_from_cells(self, cells: list, all_links_in_row: list, meeting_data: dict) -> None:
        """
        Extracts links for agenda, minutes, video, and packet from table cells and all links in a row.
        This method is specific to table-based layouts.
        """
        # Initialize/clear link fields
        meeting_data['agenda_url'] = None
        meeting_data['minutes_url'] = None
        meeting_data['video_url'] = None
        meeting_data['packet_url'] = None


        # Video (often has "Video", "Watch", "Media", or specific PHP script names)
        for link_tag in all_links_in_row:
            href = link_tag['href']
            link_text = link_tag.get_text(strip=True).lower()
            if ('viewevent.php' in href.lower() or \
               'mediaplayer.php' in href.lower() or \
               any(keyword in link_text for keyword in ['video', 'watch', 'media', 'view event', 'recording'])):
                
                video_url_candidate = href # Default to href
                if href and href.lower().startswith('javascript:void(0)'):
                    onclick_attr = link_tag.get('onclick')
                    if onclick_attr:
                        url_match = re.search(r"window\.open\s*\(\s*['\"]([^'\"]+)['\"].*?\)", onclick_attr)
                        if url_match:
                            raw_onclick_url = url_match.group(1).strip()
                            video_url_candidate = html.unescape(raw_onclick_url) # Use unescaped onclick URL
                meeting_data['video_url'] = video_url_candidate
                break 

        # Agenda Packet (usually contains "Packet")
        for link_tag in all_links_in_row:
            href = link_tag['href']
            link_text = link_tag.get_text(strip=True).lower()
            if 'packet' in link_text or 'agenda packet' in link_text:
                meeting_data['packet_url'] = href
                break

        # Agenda (usually contains "Agenda", ensure it's not also packet or minutes)
        for link_tag in all_links_in_row:
            href = link_tag['href']
            link_text = link_tag.get_text(strip=True).lower()
            if ('agenda' in link_text or 'agendaviewer.php' in href.lower()) and \
               not meeting_data.get('packet_url') == href and \
               not any(keyword in link_text for keyword in ['packet', 'minutes']): # Avoid misidentifying packet/minutes as agenda
                meeting_data['agenda_url'] = href
                break
        
        # Minutes (usually contains "Minutes")
        for link_tag in all_links_in_row:
            href = link_tag['href']
            link_text = link_tag.get_text(strip=True).lower()
            if 'minutes' in link_text or 'minutesviewer.php' in href.lower():
                meeting_data['minutes_url'] = href
                break


        # If agenda is still missing, check cell 2 (index)
        if not meeting_data.get('agenda_url') and len(cells) > 2:
            agenda_cell_link = cells[2].find('a', href=True)
            if agenda_cell_link and agenda_cell_link['href'] != meeting_data.get('packet_url') and agenda_cell_link['href'] != meeting_data.get('minutes_url'):
                meeting_data['agenda_url'] = agenda_cell_link['href']

        # If minutes is still missing, check cell 3 (index)
        if not meeting_data.get('minutes_url') and len(cells) > 3:
            minutes_cell_link = cells[3].find('a', href=True)
            if minutes_cell_link and minutes_cell_link['href'] != meeting_data.get('agenda_url') and minutes_cell_link['href'] != meeting_data.get('packet_url'):
                 meeting_data['minutes_url'] = minutes_cell_link['href']

        # Final check: if agenda and minutes URL are identical, one is likely misidentified.
        # Prefer specific viewer links if available. Often, a generic link might be agenda.
        if meeting_data.get('agenda_url') and meeting_data.get('agenda_url') == meeting_data.get('minutes_url'):
            is_minutes_specific = 'minutesviewer.php' in (meeting_data.get('minutes_url','')).lower()
            is_agenda_specific = 'agendaviewer.php' in (meeting_data.get('agenda_url','')).lower()

            if is_agenda_specific and not is_minutes_specific:
                pass # Agenda is specific, minutes might be a duplicate generic link. Keep agenda.
            elif is_minutes_specific and not is_agenda_specific:
                 meeting_data['agenda_url'] = None # Minutes is specific, agenda was likely the duplicate.
            else: # Both generic or both specific (unlikely for different types)
                 meeting_data['minutes_url'] = None # Default to clearing minutes if ambiguous and identical.
