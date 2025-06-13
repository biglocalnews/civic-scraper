from bs4 import BeautifulSoup
import re
import html # For unescaping HTML entities in URLs
import logging
from datetime import datetime # For default year context if needed
from .base import GranicusBaseScraper # Assuming base.py is in the same directory

logger = logging.getLogger(__name__)

class GranicusType4Scraper(GranicusBaseScraper):
    """
    Scraper for Granicus Type 4 URLs.
    - Year selector TabbedPanel is OUTSIDE (usually above) the div with class CollapsiblePanelTab.
    - Multiple CollapsiblePanelTabs for committees.
    - Under the selected panel's content (within a specific year's tab content),
      there is an ordered list (<ol> or <ul>) often with class "responsive-table" or similar,
      where each <li> represents a meeting row.
    Example: "https://coralsprings.granicus.com/ViewPublisher.php?view_id=3" with CollapsiblePanelTab = "Coral Springs City Commission"
    """
    def _extract_meeting_details_internal(self, soup: BeautifulSoup, panel_name: str | None) -> list[dict]:
        if not panel_name:
            logger.warning(f"{self.__class__.__name__}: This scraper type requires a panel_name to identify the correct committee section.")
            return []

        meetings = []
        
        # Step 1: Find the main TabbedPanelsContentGroup which contains all year panels' content.
        main_tabbed_panels_content_group = soup.find('div', class_='TabbedPanelsContentGroup')

        if not main_tabbed_panels_content_group:
            logger.info(f"{self.__class__.__name__}: No 'TabbedPanelsContentGroup' (for years) found. This might not be a Type 4 structure or it's a simpler page.")
            # Fallback: Try to parse current view if no year tabs found.
            logger.info(f"{self.__class__.__name__}: Attempting to parse current page view for panel '{panel_name}'.")
            return self._extract_from_single_view_or_panel(soup, panel_name, "DefaultYear")

        # Get all year content divs from the main TabbedPanelsContentGroup
        year_content_divs = main_tabbed_panels_content_group.find_all('div', class_='TabbedPanelsContent', recursive=False)
        
        if not year_content_divs:
            logger.warning(f"{self.__class__.__name__}: 'TabbedPanelsContentGroup' found, but no 'TabbedPanelsContent' (year content) divs within it for panel '{panel_name}'.")
            return []

        # Try to get year names from corresponding tabs for context
        year_tabs_ul = soup.find('ul', class_='TabbedPanelsTabGroup') # Assuming it's a sibling or related to ContentGroup
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
            # Type 4 structure: Year Tab -> Collapsible Panel (Committee) -> Responsive List (Meetings)
            meetings_from_year_panel = self._extract_from_single_view_or_panel(year_content_div, panel_name, year_context)
            if meetings_from_year_panel: # If it returns a list (even empty), it means the panel was processed.
                panel_ever_found = True # Assume if it processed, it implies the panel logic was engaged.

                meetings.extend(meetings_from_year_panel)
            # If _extract_from_single_view_or_panel returns None, it means panel_name was not found in that year_content_div
            elif meetings_from_year_panel is None: # Explicitly check for None if it signifies panel not found
                 logger.debug(f"{self.__class__.__name__}: Panel '{panel_name}' not found or no relevant content in year '{year_context}'.")


        if not panel_ever_found and year_content_divs: # Only log if we actually processed year tabs
            logger.warning(f"{self.__class__.__name__}: Panel '{panel_name}' was not found in any year's content after checking all year tabs.")
            # Log available panels if main structure was found but not the specific panel
            available_panels_overall = set()
            for yc_div in year_content_divs: # Check within each year's parsed content
                collapsible_panels_in_year = yc_div.find_all('div', class_='CollapsiblePanel')
                for cp_p in collapsible_panels_in_year:
                    h_div = cp_p.find(['div','h2','h3'], class_=['CollapsiblePanelTab', 'CollapsiblePanelTabNotSelected'])
                    if h_div:
                        txt_cont = h_div.find(['a', 'h3', 'span', 'div'])
                        available_panels_overall.add(txt_cont.get_text(strip=True) if txt_cont else h_div.get_text(strip=True))
            if available_panels_overall:
                logger.info(f"{self.__class__.__name__}: Available panels found across years: {list(available_panels_overall)}")

        logger.info(f"{self.__class__.__name__}: Extracted a total of {len(meetings)} meetings for panel '{panel_name}' across all available years.")
        return meetings

    def _extract_from_single_view_or_panel(self, soup_section: BeautifulSoup, panel_name: str, year_context: str) -> list[dict] | None:
        """
        Extracts meetings for a specific panel_name from a given soup_section (can be whole page or a year's content div).
        Returns list of meetings if panel and its list are found, otherwise None if panel_name not found.
        """
        meetings = []
        
        # Find all CollapsiblePanels in the current section
        collapsible_panels = soup_section.find_all('div', class_='CollapsiblePanel')
        if not collapsible_panels:
            logger.debug(f"{self.__class__.__name__}: No 'CollapsiblePanel' divs found in the current section for panel '{panel_name}' (Year: {year_context}).")
            # If no collapsible panels at all, this section doesn't match Type 4's committee structure.
            return None # Indicate panel structure not found here

        target_panel_content_div = None
        panel_found_in_section = False

        for cp_panel in collapsible_panels:
            header_div = cp_panel.find(['div','h2','h3'], class_=['CollapsiblePanelTab', 'CollapsiblePanelTabNotSelected'])
            if not header_div:
                continue
            
            text_container = header_div.find(['a', 'h3', 'span', 'div'])
            current_panel_name_text = text_container.get_text(strip=True) if text_container else header_div.get_text(strip=True)

            if current_panel_name_text == panel_name:
                panel_found_in_section = True
                target_panel_content_div = cp_panel.find('div', class_='CollapsiblePanelContent')
                if not target_panel_content_div:
                    logger.warning(f"{self.__class__.__name__}: Panel '{panel_name}' (Year: {year_context}) header found, but 'CollapsiblePanelContent' is missing.")
                break 
        
        if not panel_found_in_section:
            logger.debug(f"{self.__class__.__name__}: Panel '{panel_name}' not found in this specific section (Year: {year_context}).")
            # Log available panels in this specific soup_section
            available_panels_in_section = []
            for cp_p_debug in collapsible_panels: # Iterate again just for logging
                 h_div_debug = cp_p_debug.find(['div','h2','h3'], class_=['CollapsiblePanelTab', 'CollapsiblePanelTabNotSelected'])
                 if h_div_debug:
                    txt_c_debug = h_div_debug.find(['a', 'h3', 'span', 'div'])
                    available_panels_in_section.append(txt_c_debug.get_text(strip=True) if txt_c_debug else h_div_debug.get_text(strip=True))
            if available_panels_in_section:
                logger.info(f"{self.__class__.__name__}: Available panels in section (Year: {year_context}): {available_panels_in_section}")
            return None # Panel specifically not found

        if not target_panel_content_div:
            return [] # Panel found, but no content div, so no meetings.

        # Type 4: Inside the panel's content, look for an <ol> or <ul> with class "responsive-table"
        # Some sites might use a div wrapper with class "responsive-table" containing the list.
        meeting_list_container = target_panel_content_div.find(['ol', 'ul'], class_='responsive-table')
        if not meeting_list_container:
            responsive_div_wrapper = target_panel_content_div.find('div', class_='responsive-table')
            if responsive_div_wrapper:
                meeting_list_container = responsive_div_wrapper.find(['ol', 'ul'])
        
        if not meeting_list_container:
            logger.warning(f"{self.__class__.__name__}: Panel '{panel_name}' (Year: {year_context}) content found, but no 'responsive-table' <ol> or <ul> list inside.")
            return [] # Structure for meetings not found

        # If found the list, extract meetings from its items
        meetings.extend(self._extract_meetings_from_list_items(meeting_list_container, year_context))
        return meetings

    def _extract_meetings_from_list_items(self, meeting_list_element: BeautifulSoup, year_context: str) -> list[dict]:
        """
        Extracts meeting details from <li> items within a "responsive-table" <ol> or <ul>.
        """
        meetings = []
        
        # Meeting rows are usually <li> elements with class "table-row"
        meeting_list_items = meeting_list_element.find_all('li', class_='table-row')
        if not meeting_list_items: # Fallback if no "table-row", try direct <li> children
            meeting_list_items = meeting_list_element.find_all('li', recursive=False)

        for item_idx, list_item in enumerate(meeting_list_items):
            # Skip header row if it's an <li> and has a specific class like "table-row--head"
            if 'table-row--head' in list_item.get('class', []):
                continue
            
            meeting_data = {'year_context': year_context} # For debugging or context
            
            # Extract data based on common div classes within the <li>
            # Name
            name_div = list_item.find('div', class_='archive-name') # Common class for name/title
            if name_div:
                meeting_data['name'] = name_div.get_text(strip=True).replace('\xa0', '')
            else: # Fallback if no specific class, try to find a prominent text
                name_text_candidate = list_item.find(['span','div'], recursive=False) # First direct span/div
                if name_text_candidate: meeting_data['name'] = name_text_candidate.get_text(strip=True).replace('\xa0', '')


            # Date
            date_div = list_item.find('div', class_='archive-date') # Common class for date
            if date_div:
                meeting_data['date'] = date_div.get_text(strip=True)
            
            # If name or date is missing after trying specific classes, skip (or try more general selectors)
            if not meeting_data.get('name') or not meeting_data.get('date'):
                # Attempt to find divs by data-label attribute as seen in some responsive tables
                if not meeting_data.get('name'):
                    name_labelled_div = list_item.find('div', attrs={'data-label': re.compile(r'Name|Event', re.I)})
                    if name_labelled_div: meeting_data['name'] = name_labelled_div.get_text(strip=True).replace('\xa0', '')
                if not meeting_data.get('date'):
                    date_labelled_div = list_item.find('div', attrs={'data-label': 'Date'})
                    if date_labelled_div: meeting_data['date'] = date_labelled_div.get_text(strip=True)
                
                if not meeting_data.get('name') or not meeting_data.get('date'):
                    logger.debug(f"Skipping list item {item_idx+1} due to missing name or date: {list_item.get_text(strip=True)[:100]}")
                    continue


            # Links: Agenda, Packet, Minutes, Video
            # These are often in divs like 'archive-agenda', 'archive-packet', etc., containing an <a> tag.
            link_sections = {
                'agenda_url': 'archive-agenda',
                'packet_url': 'archive-packet', # Or 'archive-agenda-packet'
                'minutes_url': 'archive-minutes',
                'video_url': 'archive-video' # Or 'archive-media'
            }

            all_links_in_item = list_item.find_all('a', href=True)

            for key, div_class in link_sections.items():
                section_div = list_item.find('div', class_=div_class)
                if section_div:
                    link_tag = section_div.find('a', href=True)
                    if link_tag:
                        meeting_data[key] = link_tag['href']
                        # Try to get meeting_id_source from one of the links
                        if not meeting_data.get('meeting_id_source'):
                             id_match = re.search(r'[?&](?:clip_id|event_id|meeting_id)=(\d+)', link_tag['href'], re.IGNORECASE)
                             if id_match: meeting_data['meeting_id_source'] = id_match.group(1)

            # Fallback: If specific divs not found, iterate all links and identify by text
            if not meeting_data.get('agenda_url'):
                for a_tag in all_links_in_item:
                    if re.search(r'Agenda', a_tag.get_text(strip=True), re.I) and 'packet' not in a_tag.get_text(strip=True).lower():
                        meeting_data['agenda_url'] = a_tag['href']; break
            if not meeting_data.get('packet_url'):
                 for a_tag in all_links_in_item:
                    if re.search(r'Packet|Agenda Packet', a_tag.get_text(strip=True), re.I):
                        meeting_data['packet_url'] = a_tag['href']; break
            if not meeting_data.get('minutes_url'):
                 for a_tag in all_links_in_item:
                    if re.search(r'Minutes', a_tag.get_text(strip=True), re.I):
                        meeting_data['minutes_url'] = a_tag['href']; break
            if not meeting_data.get('video_url'):
                 for a_tag in all_links_in_item:
                    if re.search(r'Video|Watch|Media', a_tag.get_text(strip=True), re.I) or \
                       'ViewEvent.php' in a_tag['href'] or 'MediaPlayer.php' in a_tag['href']:
                        meeting_data['video_url'] = a_tag['href']; break
            
            # Time (attempt extraction, base class _parse_date_time also tries this)
            if not meeting_data.get('time') and meeting_data.get('date'):
                time_match_item = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)', meeting_data['date'])
                if time_match_item:
                    meeting_data['time'] = time_match_item.group(1)
            
            if meeting_data.get('name') and meeting_data.get('date'):
                meetings.append(meeting_data)
            else:
                logger.debug(f"Final check failed for list item {item_idx+1}, missing name or date after all attempts.")
                
        return meetings
