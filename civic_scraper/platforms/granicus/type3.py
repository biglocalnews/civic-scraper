from bs4 import BeautifulSoup
import re
import html # For unescaping HTML entities in URLs
import logging
from .base import GranicusBaseScraper # Assuming base.py is in the same directory

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

    def _extract_meeting_details_internal(self, soup: BeautifulSoup, panel_name: str | None) -> list[dict]:
        meetings = []
        seen_keys: set[tuple] = set()  # (clip_id/date/name) to avoid duplicates

        # Helper regexes compiled once
        month_regex = r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan\.?|Feb\.?|Mar\.?|Apr\.?|May|Jun\.?|Jul\.?|Aug\.?|Sep\.?|Sept\.?|Oct\.?|Nov\.?|Dec\.?)'
        long_date_pattern = re.compile(rf'{month_regex}\s+\d{{1,2}},\s+\d{{4}}', re.I)
        slash_date_pattern = re.compile(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b')
        time_pattern = re.compile(r'\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\b')

        def extract_date_time_from_text(text: str) -> tuple[str | None, str | None]:
            text_clean = text.replace('\xa0', ' ')
            date_match = long_date_pattern.search(text_clean)
            if not date_match:
                date_match = slash_date_pattern.search(text_clean)
            date_str = date_match.group(0) if date_match else None
            time_match = time_pattern.search(text_clean)
            time_str = time_match.group(0) if time_match else None
            return date_str, time_str

        def clean_name(raw_name: str, headers_tokens: list[str], date_str: str | None) -> str:
            if not raw_name:
                return raw_name
            cleaned = raw_name.replace('\xa0', ' ').strip()
            # Remove date substring if embedded
            if date_str and date_str in cleaned:
                cleaned = cleaned.replace(date_str, ' ').strip()
            # Some rows repeat header tokens at the beginning of each cell (for accessibility)
            header_set = {h.lower() for h in headers_tokens if h}
            # Tokenize and drop leading header tokens
            tokens = cleaned.split()
            i = 0
            while i < len(tokens) and tokens[i].lower().rstrip(':') in header_set:
                i += 1
            cleaned = ' '.join(tokens[i:]).strip()
            # Collapse multiple spaces
            cleaned = re.sub(r'\s+', ' ', cleaned)
            # Trim overly long names
            if len(cleaned) > 160:
                cleaned = cleaned[:157] + '...'
            return cleaned

        def pick_meeting_name(row, cells, headers_tokens, date_str):
            # Strategy: Identify a cell likely containing the meeting title distinct from controls/links.
            # 1. If a cell contains keywords like 'commission', 'council', 'board', 'hearing', etc. treat that as name.
            keywords = ['commission', 'council', 'board', 'committee', 'hearing', 'meeting', 'workshop']
            candidate_texts = []
            for c in cells:
                txt = c.get_text(' ', strip=True)
                if not txt:
                    continue
                lower_txt = txt.lower()
                if any(kw in lower_txt for kw in keywords) and not re.search(r'\b(duration|agenda|minutes|packet|video)\b', lower_txt):
                    candidate_texts.append(txt)
            # 2. If still none, fall back to anchor texts that include clip id
            if not candidate_texts:
                for a in row.find_all('a', href=True):
                    href_lower = a['href'].lower()
                    if 'clip_id=' in href_lower:
                        txt = a.get_text(' ', strip=True)
                        if txt:
                            candidate_texts.append(txt)
            # 3. Fallback to any non-date non-header cell text
            if not candidate_texts:
                for c in cells:
                    txt = c.get_text(' ', strip=True)
                    if not txt:
                        continue
                    if date_str and date_str in txt:
                        continue
                    if re.fullmatch(long_date_pattern, txt) or slash_date_pattern.fullmatch(txt):
                        continue
                    candidate_texts.append(txt)
                    break
            chosen = candidate_texts[0] if candidate_texts else (date_str or '')
            return clean_name(chosen, headers_tokens, date_str)

        
        # Look for a main TabbedPanel structure for years.
        # Common IDs/classes: TabbedPanel1, TabbedPanels1, or just class TabbedPanels
        year_tab_panel_container = soup.find('div', id=re.compile(r'TabbedPanels?1', re.I))
        if not year_tab_panel_container:
            year_tab_panel_container = soup.find('div', class_='TabbedPanels')

        content_sections_to_parse = []
        year_context_list = []

        if year_tab_panel_container:
            logger.info(f"{self.__class__.__name__}: Found a TabbedPanel structure. Processing year tabs.")
            year_tabs_ul = year_tab_panel_container.find('ul', class_='TabbedPanelsTabGroup')
            year_contents_group_div = year_tab_panel_container.find('div', class_='TabbedPanelsContentGroup')

            if year_tabs_ul and year_contents_group_div:
                year_tabs_li_elements = year_tabs_ul.find_all('li', class_='TabbedPanelsTab', recursive=False)
                year_content_divs = year_contents_group_div.find_all('div', class_='TabbedPanelsContent', recursive=False)
                
                if len(year_tabs_li_elements) == len(year_content_divs) and year_tabs_li_elements:
                    for i in range(len(year_tabs_li_elements)):
                        year_text = year_tabs_li_elements[i].get_text(strip=True)
                        content_sections_to_parse.append(year_content_divs[i])
                        year_context_list.append(year_text)
                    logger.info(f"{self.__class__.__name__}: Identified {len(content_sections_to_parse)} year content sections from tabs.")
                elif year_content_divs: # If tabs don't match content divs, process content divs with unknown year
                    logger.warning(f"{self.__class__.__name__}: Mismatch or missing year tabs. Processing content divs with 'UnknownYear'.")
                    for content_div in year_content_divs:
                        content_sections_to_parse.append(content_div)
                        year_context_list.append("UnknownYear")
                else: # No clear year tab structure within the TabbedPanel
                    logger.info(f"{self.__class__.__name__}: TabbedPanel found, but no distinct year TabGroup/ContentGroup. Will look for tables directly within it or page.")
                    content_sections_to_parse.append(year_tab_panel_container) # Parse the whole container
                    year_context_list.append("DefaultYear")
            else: # No TabGroup/ContentGroup, treat the whole TabbedPanel container as one section
                logger.info(f"{self.__class__.__name__}: TabbedPanel found, but no TabGroup/ContentGroup. Parsing TabbedPanel as a single section.")
                content_sections_to_parse.append(year_tab_panel_container)
                year_context_list.append("DefaultYear")
        else:
            logger.info(f"{self.__class__.__name__}: No main TabbedPanel structure for years found. Will search for tables directly on the page.")
            # If no year tabs, the whole soup is the context, or look for any listingTable directly
            content_sections_to_parse.append(soup) # Parse the entire page content
            year_context_list.append("DefaultYear") # Default year context

        if not content_sections_to_parse:
            logger.warning(f"{self.__class__.__name__}: No content sections identified for parsing.")
            return []

        for idx, content_section in enumerate(content_sections_to_parse):
            current_year_context = year_context_list[idx]
            logger.info(f"{self.__class__.__name__}: Parsing section with year context: {current_year_context}")

            # DEBUG: Save first section's raw HTML snippet for manual inspection (first 1 only)
            if idx == 0:
                try:
                    snippet = str(content_section)[:20000]
                    debug_path = f"debug_detection/type3_section_{current_year_context}.html"
                    with open(debug_path, 'w', encoding='utf-8') as fh:
                        fh.write(snippet)
                    logger.info(f"{self.__class__.__name__}: Wrote debug snippet to {debug_path}")
                except Exception as e:
                    logger.debug(f"{self.__class__.__name__}: Failed to write debug snippet: {e}")

            processed_any_rows_in_section = False

            # FIRST: Handle responsive list variant (Surfside style)
            responsive_lists = content_section.find_all(['ol','ul'], class_=re.compile(r'responsive-table', re.I))
            for rlist in responsive_lists:
                list_rows = rlist.find_all('li', class_=re.compile(r'table-row', re.I))
                if not list_rows:
                    continue
                # Build headers from head row
                headers_tokens = []
                head_li = None
                for li in list_rows:
                    if 'head' in ' '.join(li.get('class', [])).lower():
                        head_li = li
                        break
                if head_li:
                    headers_tokens = [div.get_text(' ', strip=True).lower() for div in head_li.find_all('div', class_=re.compile(r'table-cell', re.I))]
                for li in list_rows:
                    if li is head_li:
                        continue
                    cell_divs = li.find_all('div', class_=re.compile(r'table-cell', re.I))
                    if len(cell_divs) < 2:
                        continue
                    raw_date = cell_divs[1].get_text(' ', strip=True)
                    date_candidate, time_candidate = extract_date_time_from_text(raw_date)
                    if not date_candidate:
                        date_candidate, time_candidate2 = extract_date_time_from_text(li.get_text(' ', strip=True))
                        if time_candidate2 and not time_candidate:
                            time_candidate = time_candidate2
                    meeting_id_source = ''
                    all_links = li.find_all('a', href=True)
                    for a in all_links:
                        href = a.get('href','')
                        m = re.search(r'[?&](?:clip_id)=(\d+)', href, re.I)
                        if m:
                            meeting_id_source = m.group(1)
                            break
                    meeting_name = pick_meeting_name(li, cell_divs, headers_tokens, date_candidate)
                    meeting_name = clean_name(meeting_name, headers_tokens, date_candidate)
                    if not (meeting_name and date_candidate):
                        continue
                    dedupe_key = (meeting_id_source or '', date_candidate, meeting_name.lower())
                    if dedupe_key in seen_keys:
                        continue
                    seen_keys.add(dedupe_key)
                    meeting_data = {
                        'name': meeting_name,
                        'date': date_candidate,
                        'time': time_candidate,
                        'meeting_id_source': meeting_id_source
                    }
                    self._extract_links_from_row_links(all_links, meeting_data, cell_divs, headers_tokens)
                    meetings.append(meeting_data)
                    processed_any_rows_in_section = True

            # SECOND: Fallback to table-based variant if no responsive list processed rows
            if not processed_any_rows_in_section:
                tables_in_section = content_section.find_all('table', class_='listingTable')
                if not tables_in_section:
                    tables_in_section = content_section.find_all('table', id=re.compile(r'pastEvents|upcomingEvents', re.I))
                    if tables_in_section:
                        logger.info(f"{self.__class__.__name__}: Found tables with IDs like pastEvents/upcomingEvents.")
                if not tables_in_section:
                    tables_in_section = content_section.find_all('table', class_=re.compile(r'listing[_-]?table\d*', re.I))
            else:
                tables_in_section = []

            if tables_in_section:
                for table_num, table in enumerate(tables_in_section):
                    logger.info(f"{self.__class__.__name__}: Processing table {table_num + 1} in year '{current_year_context}'.")
                    # Rows can have classes 'listingRow', 'listingRowAlt', or just be <tr> in <tbody>
                    # Also seen 'odd' and 'even' for row classes
                    rows = table.find_all('tr', class_=re.compile(r'listingRow|listingRowAlt|even|odd', re.I))
                    if not rows:  # If no specific classes, try all <tr> within a <tbody>
                        tbody = table.find('tbody')
                        if tbody:
                            rows = tbody.find_all('tr')
                        else:  # Or all <tr> directly under the table if no tbody
                            rows = table.find_all('tr')

                    if not rows:
                        logger.debug(f"{self.__class__.__name__}: No processable rows found in table {table_num + 1} for year '{current_year_context}'.")
                        continue

                    # Try to identify headers to map columns, if possible (more robust)
                    header_row = table.find('tr', class_=re.compile(r'header|heading', re.I))  # Common header row classes
                    # If no explicit header class, consider first row with <th>
                    if not header_row:
                        for r in rows:
                            if r.find('th'):
                                header_row = r
                                break
                    headers_text = []
                    if header_row:
                        headers_text = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]

                    for row_idx, row in enumerate(rows):
                        if row == header_row:
                            continue

                        cells = row.find_all('td')
                        if not cells:
                            continue

                        row_text_full = ' '.join([c.get_text(' ', strip=True) for c in cells])
                        date_candidate, time_candidate = extract_date_time_from_text(row_text_full)

                        meeting_id_source = ''
                        all_links_in_row = row.find_all('a', href=True)
                        for link_tag in all_links_in_row:
                            href = link_tag.get('href', '')
                            id_match = re.search(r'[?&](?:clip_id|event_id|meeting_id|item_id)=(\d+)', href, re.I)
                            if id_match:
                                meeting_id_source = id_match.group(1)
                                break

                        name_candidate = pick_meeting_name(row, cells, headers_text, date_candidate)
                        name_candidate = clean_name(name_candidate, headers_text, date_candidate)

                        if not date_candidate:
                            # Search dedicated date-like cells (often first or second cell)
                            for c in cells[:2]:
                                c_txt = c.get_text(' ', strip=True)
                                d_alt, _ = extract_date_time_from_text(c_txt)
                                if d_alt:
                                    date_candidate = d_alt
                                    break
                        if not name_candidate:
                            name_candidate = pick_meeting_name(row, cells, headers_text, date_candidate)

                        if not date_candidate or not name_candidate:
                            continue

                        dedupe_key = (meeting_id_source or '', date_candidate, name_candidate.lower())
                        if dedupe_key in seen_keys:
                            continue
                        seen_keys.add(dedupe_key)

                        meeting_data = {
                            'name': name_candidate,
                            'date': date_candidate,
                            'time': time_candidate,
                            'meeting_id_source': meeting_id_source
                        }
                        # Extract links
                        self._extract_links_from_row_links(all_links_in_row, meeting_data, cells, headers_text)

                        # Ensure at least one asset link exists to consider valid; if none, still keep to let transform filter by date
                        if any([meeting_data.get('agenda_url'), meeting_data.get('minutes_url'), meeting_data.get('video_url'), meeting_data.get('packet_url')]):
                            meetings.append(meeting_data)
                            processed_any_rows_in_section = True
                        else:
                            # Keep meeting even without links if date/name present (may fetch later)
                            meetings.append(meeting_data)
                            processed_any_rows_in_section = True

            # If we still didn't process any rows, attempt a link-based heuristic extraction.
            if not processed_any_rows_in_section:
                logger.debug(f"{self.__class__.__name__}: No table rows parsed for year '{current_year_context}'. Trying heuristic link-based extraction.")
                # Look for any anchors with typical agenda/minutes/video keywords and attempt to build records around them.
                candidate_links = content_section.find_all('a', href=True)
                # Group by nearest textual date found in ancestor or preceding text
                date_regexes = [
                    re.compile(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', re.I),
                    re.compile(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b')
                ]
                for a in candidate_links:
                    text_lower = a.get_text(strip=True).lower()
                    if not any(k in text_lower for k in ['agenda', 'minutes', 'packet', 'video', 'media', 'agendaviewer', 'minutesviewer']):
                        continue
                    # Walk up to find surrounding text block
                    container = a
                    for _ in range(4):
                        if container.parent:
                            container = container.parent
                    container_text = container.get_text(" ", strip=True)
                    found_date = None
                    for dr in date_regexes:
                        m = dr.search(container_text)
                        if m:
                            found_date = m.group(0)
                            break
                    if not found_date:
                        continue
                    meeting_data = {
                        'name': container_text[:100],  # truncate overly long descriptions
                        'date': found_date,
                        'meeting_id_source': ''
                    }
                    self._extract_links_from_row_links([a], meeting_data, [], [])
                    if meeting_data.get('agenda_url') or meeting_data.get('minutes_url') or meeting_data.get('video_url') or meeting_data.get('packet_url'):
                        meetings.append(meeting_data)
        
        logger.info(f"{self.__class__.__name__}: Extracted {len(meetings)} meetings for panel '{panel_name if panel_name else 'N/A'}'.")
        return meetings

    def _extract_links_from_row_links(self, all_links_in_row: list, meeting_data: dict, cells: list, headers_text: list):
        """Helper to extract various document links from all hyperlinks in a row."""
        # Initialize/clear link fields
        meeting_data['agenda_url'] = None
        meeting_data['minutes_url'] = None
        meeting_data['video_url'] = None
        meeting_data['packet_url'] = None        # Prioritize links with specific text
        for link_tag in all_links_in_row:
            href = self._normalize_url_local(link_tag.get('href', ''))
            link_text = link_tag.get_text(strip=True).lower()
            
            # Video - check for MediaPlayer URLs, onclick handlers, or video-related keywords
            if not meeting_data.get('video_url'):
                # Check for JavaScript onclick handlers (common in Sacramento-style sites)
                onclick_attr = link_tag.get('onclick', '')
                video_url_candidate = None
                
                if onclick_attr and 'mediaplayer.php' in onclick_attr.lower():
                    # Extract URL from onclick="window.open('URL',...)"
                    url_match = re.search(r"window\.open\s*\(\s*['\"]([^'\"]+)['\"].*?\)", onclick_attr)
                    if url_match:
                        raw_onclick_url = url_match.group(1).strip()
                        unescaped_onclick_url = html.unescape(raw_onclick_url)
                        video_url_candidate = self._normalize_url_local(unescaped_onclick_url)
                elif 'viewevent.php' in href.lower() or 'mediaplayer.php' in href.lower():
                    video_url_candidate = href
                elif any(keyword in link_text for keyword in ['video', 'watch', 'media', 'view event', 'recording', 'live']):
                    video_url_candidate = href
                
                if video_url_candidate:
                    meeting_data['video_url'] = video_url_candidate

            # Audio - check for MP3, audio files, or audio-related keywords  
            if not meeting_data.get('video_url'):  # Use video_url for audio files too
                if (href and (href.lower().endswith('.mp3') or href.lower().endswith('.mp4') or 
                              href.lower().endswith('.wav') or 'audio' in href.lower())) or \
                   any(keyword in link_text for keyword in ['mp3', 'audio', 'sound', 'recording']):
                    meeting_data['video_url'] = href

            # Agenda - check for AgendaViewer URLs or "agenda" text
            if not meeting_data.get('agenda_url'):
                if 'agendaviewer.php' in href.lower() or \
                   (link_text == 'agenda' or 'agenda' in link_text) and \
                   not any(keyword in link_text for keyword in ['packet', 'minutes']):
                    meeting_data['agenda_url'] = href

            # Minutes - check for MinutesViewer URLs or "minutes" text  
            if not meeting_data.get('minutes_url'):
                if 'minutesviewer.php' in href.lower() or \
                   ('minutes' in link_text and 'agenda' not in link_text):
                    meeting_data['minutes_url'] = href

            # Packet - check for packet-related keywords
            if not meeting_data.get('packet_url'):
                if any(keyword in link_text for keyword in ['packet', 'agenda packet', 'supplemental']):
                    meeting_data['packet_url'] = href
        
        # Fallback: If links are not clearly labeled, try to infer from column headers if available
        if headers_text and (not meeting_data['agenda_url'] or not meeting_data['minutes_url']):
            for i, header in enumerate(headers_text):
                if i < len(cells):
                    cell_links = cells[i].find_all('a', href=True)
                    if not cell_links: continue
                    
                    cell_href = self._normalize_url_local(cell_links[0]['href']) # Take first link in cell

                    if not meeting_data['agenda_url'] and 'agenda' in header and 'packet' not in header:
                        if cell_href not in [meeting_data.get('packet_url'), meeting_data.get('minutes_url'), meeting_data.get('video_url')]:
                           meeting_data['agenda_url'] = cell_href
                    elif not meeting_data['minutes_url'] and 'minutes' in header:
                        if cell_href not in [meeting_data.get('agenda_url'), meeting_data.get('packet_url'), meeting_data.get('video_url')]:
                            meeting_data['minutes_url'] = cell_href
                    elif not meeting_data['packet_url'] and 'packet' in header:
                         if cell_href not in [meeting_data.get('agenda_url'), meeting_data.get('minutes_url'), meeting_data.get('video_url')]:
                            meeting_data['packet_url'] = cell_href
                    elif not meeting_data['video_url'] and any(keyword in header for keyword in ['video', 'media', 'watch']):
                        if cell_href not in [meeting_data.get('agenda_url'), meeting_data.get('minutes_url'), meeting_data.get('packet_url')]:
                            meeting_data['video_url'] = cell_href
        
        # If agenda and minutes are still the same, clear minutes (common issue with generic links)
        if meeting_data.get('agenda_url') and meeting_data.get('agenda_url') == meeting_data.get('minutes_url'):
            if 'minutesviewer.php' not in (meeting_data.get('minutes_url','')).lower(): # If minutes is not specific
                meeting_data['minutes_url'] = None


    def _normalize_url_local(self, url: str) -> str | None:
        """
        Normalize URLs by ensuring they have a proper scheme, relative to the base_url.
        This is a local helper; the main _make_absolute_url is called during transformation.
        """
        if not url:
            return None
        if url.startswith('//'):
            # Assume https for scheme-relative URLs
            return f"https:{url}"
        # If it's already absolute, return as is.
        if url.startswith(('http://', 'https://')):
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
        return False # Overrides the base class default
