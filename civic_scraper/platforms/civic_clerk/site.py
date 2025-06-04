import html
import re
import json
import logging
import requests
from datetime import datetime, date
from pathlib import Path
from urllib.parse import urlparse, urljoin, quote # Added quote for URL encoding

import lxml.html
from bs4 import BeautifulSoup
from requests import Session

import civic_scraper
from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.base.cache import Cache

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CivicClerkSite(base.Site):
    def __init__(self, url, place=None, state_or_province=None, cache=Cache()):
        self.initial_url = url # User-provided URL
        self.place = place
        self.state_or_province = state_or_province
        self.cache = cache

        # Set up session with browser-like headers
        self.session = Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1", # Do Not Track
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1", # Added common header
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none", # Changed from same-origin for initial request
            "Sec-Fetch-User": "?1",   # Added common header
        })
        # Don't automatically raise exception on error status for session
        self.session.hooks = {}


        # Resolve the final URL after redirects to get the correct portal domain
        try:
            # Use GET for initial resolution as HEAD might not always be allowed or reflect full redirects
            # Also, update Referer and Origin for subsequent requests based on the resolved URL
            initial_response = self.session.get(self.initial_url, allow_redirects=True, timeout=15)
            initial_response.raise_for_status()
            self.resolved_url = initial_response.url
            self.portal_domain_base = f"{urlparse(self.resolved_url).scheme}://{urlparse(self.resolved_url).netloc}"
            self.session.headers.update({ # Update session headers for future requests
                "Referer": self.resolved_url,
                "Origin": self.portal_domain_base,
                "Sec-Fetch-Site": "same-origin" # Now it's same-origin
            })
            logger.info(f"Resolved initial URL '{self.initial_url}' to '{self.resolved_url}'")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Could not resolve initial URL {self.initial_url}: {e}. Using it directly and hoping for the best.")
            self.resolved_url = self.initial_url # Fallback
            self.portal_domain_base = f"{urlparse(self.resolved_url).scheme}://{urlparse(self.resolved_url).netloc}"
            # Base URL for API calls, might be different from portal_domain_base
            # self.base_url is used for joining relative paths if needed, should be portal_domain_base
        self.url = self.resolved_url # Use resolved URL as the main URL for the site object
        self.base_url = self.portal_domain_base # For resolving relative paths from HTML

        # Extract the tenant/organization name
        parsed_resolved = urlparse(self.resolved_url)
        self.tenant_name = parsed_resolved.netloc.split('.')[0]
        self.is_portal = ".portal.civicclerk.com" in parsed_resolved.netloc

        # If tenant_name is generic, try to get it from initial_url
        if self.tenant_name.lower() in ['www', 'portal', 'unclassified'] or not self.tenant_name:
             initial_parsed_netloc = urlparse(self.initial_url).netloc
             if initial_parsed_netloc:
                potential_tenant = initial_parsed_netloc.split('.')[0]
                if potential_tenant.lower() not in ['www', 'portal', 'unclassified']:
                    self.tenant_name = potential_tenant
        logger.info(f"Detected tenant name: {self.tenant_name}, Is Portal: {self.is_portal}")

        # API configuration
        self.api_url_base_for_calls = f"https://{self.tenant_name}.api.civicclerk.com/v1" # Primary API base
        self.org_id = None
        self.api_endpoints = {} # Store discovered specific endpoints
        
        # Try to discover the API endpoints and other configuration
        # This might override self.api_url_base_for_calls if a more specific one is found
        self._discover_api_configuration()


    def _extract_js_urls_from_html(self, html_content):
        js_files = []
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            for script_tag in soup.find_all('script', src=True):
                src_val = script_tag['src']
                if src_val.endswith('.js'):
                    js_url = urljoin(self.resolved_url, src_val) # Use resolved_url as base
                    js_files.append(js_url)
                    logger.debug(f"Found JS file: {js_url}")
        except Exception as e:
            logger.error(f"Error extracting JS URLs: {e}")
        return js_files

    def _discover_api_configuration(self):
        logger.info(f"Discovering API configuration for {self.resolved_url}")
        try:
            response = self.session.get(self.resolved_url) # Use resolved_url
            if response.status_code != 200:
                logger.warning(f"Failed to fetch main page for API discovery: {response.status_code}")
                self._construct_default_api_endpoints() # Fallback to default construction
                return

            html_content = response.text
            js_files = self._extract_js_urls_from_html(html_content)
            
            window_config = self._extract_window_config(html_content)
            if window_config:
                logger.info(f"Found window configuration: {list(window_config.keys())}")
                if 'organizationId' in window_config: self.org_id = window_config['organizationId']
                if 'apiUrl' in window_config:
                    api_url_from_config = window_config['apiUrl']
                    if '[TENANT]' in api_url_from_config:
                        api_url_from_config = api_url_from_config.replace('[TENANT]', self.tenant_name)
                    if api_url_from_config.startswith('http'): # If it's a full URL
                         self.api_url_base_for_calls = api_url_from_config.rstrip('/')
                         logger.info(f"Overriding API base from window config: {self.api_url_base_for_calls}")


            for js_url in js_files:
                js_config = self._analyze_js_file(js_url)
                if js_config:
                    logger.info(f"Found configuration in JS file {js_url}: {list(js_config.keys())}")
                    if 'organizationId' in js_config and not self.org_id: self.org_id = js_config['organizationId']
                    if 'apiUrl' in js_config:
                        api_url_from_js = js_config['apiUrl']
                        if '[TENANT]' in api_url_from_js:
                            api_url_from_js = api_url_from_js.replace('[TENANT]', self.tenant_name)
                        if api_url_from_js.startswith('http'): # If it's a full URL
                            self.api_url_base_for_calls = api_url_from_js.rstrip('/')
                            logger.info(f"Overriding API base from JS config: {self.api_url_base_for_calls}")
                    
                    # Store specific discovered endpoints if any
                    if 'endpoints' in js_config and isinstance(js_config['endpoints'], dict):
                        for key, url_template in js_config['endpoints'].items():
                            full_url = url_template
                            if '[TENANT]' in full_url:
                                full_url = full_url.replace('[TENANT]', self.tenant_name)
                            if not full_url.startswith('http') and self.api_url_base_for_calls:
                                full_url = f"{self.api_url_base_for_calls}/{full_url.lstrip('/')}"
                            elif not full_url.startswith('http'): # If base is not set, cannot form full URL
                                logger.warning(f"Cannot form full URL for endpoint {key}: {url_template} as API base is unknown.")
                                continue
                            self.api_endpoints[key.lower()] = full_url
                            logger.info(f"Discovered specific endpoint: {key.lower()} -> {full_url}")


            if not self.api_endpoints.get('events') and not self.api_endpoints.get('meetings'):
                 logger.info("No specific meetings/events endpoint discovered, will use default construction.")
                 self._construct_default_api_endpoints()

        except Exception as e:
            logger.error(f"Error during API configuration discovery: {e}")
            self._construct_default_api_endpoints() # Fallback

        logger.info(f"Final API base for calls: {self.api_url_base_for_calls}")
        logger.info(f"Discovered specific API endpoints: {self.api_endpoints}")
        if self.org_id: logger.info(f"Discovered Organization ID: {self.org_id}")


    def _extract_window_config(self, html_content):
        config = {}
        patterns = [
            r'window\.__INITIAL_CONFIG__\s*=\s*({.*?});',
            r'window\.APP_CONFIG\s*=\s*({.*?});',
            r'window\.config\s*=\s*({.*?});'
        ]
        for pattern in patterns:
            match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
            if match:
                try:
                    config_str = match.group(1)
                    # Basic cleaning for JSON parsing
                    config_str = re.sub(r'(?<!")(\w+)(?=\s*:)', r'"\1"', config_str) # Add quotes to keys
                    config_str = config_str.replace("'", '"') # Replace single quotes with double
                    config_str = config_str.replace('true', 'true').replace('false', 'false').replace('null', 'null')
                    # Remove trailing commas that break JSON
                    config_str = re.sub(r',\s*([}\]])', r'\1', config_str)
                    config_data = json.loads(config_str)
                    config.update(config_data)
                    logger.debug(f"Successfully parsed window config with pattern: {pattern}")
                    return config # Return first one found
                except Exception as e:
                    logger.debug(f"Error parsing window config with pattern {pattern}: {e} - Config string snippet: {config_str[:200]}")
        return config

    def _analyze_js_file(self, js_url):
        config = {}
        try:
            response = self.session.get(js_url)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch JS file {js_url}: {response.status_code}")
                return config
            js_content = response.text
            
            # Look for API URL patterns (simplified)
            api_url_match = re.search(r'apiUrl:\s*["\']([^"\']+)["\']', js_content, re.IGNORECASE)
            if api_url_match:
                config['apiUrl'] = api_url_match.group(1)

            org_id_match = re.search(r'organizationId:\s*["\']([^"\']+)["\']', js_content, re.IGNORECASE)
            if org_id_match:
                config['organizationId'] = org_id_match.group(1)
            
            # Example for specific endpoints (highly dependent on JS structure)
            # meetings_endpoint_match = re.search(r'getMeetingsPath:\s*["\']([^"\']+)["\']', js_content)
            # if meetings_endpoint_match:
            #     if 'endpoints' not in config: config['endpoints'] = {}
            #     config['endpoints']['meetings'] = meetings_endpoint_match.group(1)

        except Exception as e:
            logger.error(f"Error analyzing JS file {js_url}: {e}")
        return config

    def _construct_default_api_endpoints(self):
        """Construct default API endpoints if discovery fails."""
        logger.info("Constructing default API endpoints.")
        # The primary API base is already set to f"https://{self.tenant_name}.api.civicclerk.com/v1"
        # We will use this self.api_url_base_for_calls for the /Events endpoint.
        # No need to populate self.api_endpoints with defaults if we directly use /Events.
        pass


    def _validate_meetings_response(self, data):
        # This was used for testing arbitrary endpoints.
        # With OData /Events, we expect a list (possibly under 'value').
        if data is None: return False
        if isinstance(data, list) and (not data or isinstance(data[0], dict)): return True # Empty list is valid, or list of dicts        if isinstance(data, dict) and "value" in data and isinstance(data["value"], list): return True
        return False

    def create_asset(self, asset_name, asset_url, asset_type, committee_name, meeting_datetime, meeting_id_str):
        # Ensure meeting_datetime is a datetime object
        if isinstance(meeting_datetime, date) and not isinstance(meeting_datetime, datetime):
            meeting_datetime_obj = datetime.combine(meeting_datetime, datetime.min.time())
        elif isinstance(meeting_datetime, datetime):
            meeting_datetime_obj = meeting_datetime
        else: # Fallback if not a recognized date/datetime type
            logger.warning(f"Invalid meeting_datetime type for asset creation: {meeting_datetime}")
            meeting_datetime_obj = datetime.now()

        e = {
            "url": asset_url,
            "asset_name": asset_name,
            "committee_name": committee_name,
            "place": self.place,
            "state_or_province": self.state_or_province,
            "asset_type": asset_type, # e.g., "agenda", "minutes"
            "meeting_date": meeting_datetime_obj.date(),
            "meeting_time": meeting_datetime_obj.time(),
            "meeting_id": meeting_id_str, # Should be the unique ID for the meeting event
            "scraped_by": f"civic-scraper_{civic_scraper.__version__}",
            "content_type": None, # Will be determined on download
            "content_length": None, # Will be determined on download
        }
        return Asset(**e)

    def _parse_meeting_datetime(self, date_str):
        """Parse meeting datetime from various formats, prioritizing ISO."""
        if not date_str: 
            return None
        date_str = str(date_str).strip()
        
        # Try ISO 8601 format first (common in APIs and data-date attributes)
        if 'T' in date_str:
            try:
                # Normalize: remove 'Z', ensure timezone offset format
                date_str_norm = date_str.replace('Z', '+00:00')
                # Handle milliseconds: remove them before parsing
                if '.' in date_str_norm:
                    parts = date_str_norm.split('.')
                    datetime_part = parts[0]
                    timezone_info = ""
                    # Check if timezone info exists after milliseconds
                    potential_tz_part = parts[1]
                    tz_match = re.search(r'([+-]\d{2}:\d{2})$', potential_tz_part)
                    if tz_match:
                        timezone_info = tz_match.group(1)
                    elif '+00:00' in potential_tz_part: # If Z was replaced
                        timezone_info = '+00:00'
                    date_str_norm = datetime_part + timezone_info
                
                return datetime.fromisoformat(date_str_norm)
            except ValueError as e_iso:
                logger.debug(f"Could not parse ISO date string: '{date_str}' (normalized: '{date_str_norm}') due to {e_iso}")
        
        # Try to parse HTML text format like "May 14, 2024 6:00 PM PST"
        # Remove timezone abbreviations
        date_str_clean = re.sub(r'\s+(PST|PDT|EST|EDT|CST|CDT|MST|MDT|UTC)\s*$', '', date_str, flags=re.IGNORECASE)
        
        # Fallback to other common formats
        formats = [
            "%B %d, %Y %I:%M %p",  # "May 14, 2024 6:00 PM"
            "%B %d, %Y at %I:%M %p",  # "May 14, 2024 at 6:00 PM"
            "%b %d, %Y %I:%M %p",  # "May 14, 2024 6:00 PM" (abbreviated month)
            "%Y-%m-%dT%H:%M:%S", 
            "%m/%d/%Y %I:%M %p", 
            "%m/%d/%Y %H:%M",
            "%Y-%m-%d %H:%M:%S", 
            "%m/%d/%Y", 
            "%B %d, %Y", 
            "%b %d, %Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str_clean, fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date '{date_str}' with any standard format.")
        return None
    def _fetch_events_via_odata_api(self, start_date_obj=None, end_date_obj=None):
        """Fetches events using the /Events OData endpoint with pagination support."""
        # Use the discovered specific 'events' endpoint if available, otherwise default
        events_api_url = self.api_endpoints.get('events', f"{self.api_url_base_for_calls}/Events")
        
        odata_params = {
            "$orderby": "startDateTime asc", # Changed from desc to asc
            "$top": 200,  # Fetch up to 200 events per page
            # "$count": "true" # Optionally get total count
        }
        
        filters = []
        if start_date_obj: # Expects datetime.date object
            filters.append(f"startDateTime ge {start_date_obj.isoformat()}T00:00:00Z")
        if end_date_obj: # Expects datetime.date object
            # Events starting on or before the end_date_obj
            filters.append(f"startDateTime le {end_date_obj.isoformat()}T23:59:59Z")
        
        if filters:
            odata_params["$filter"] = " and ".join(filters)

        api_headers = {'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}
        if self.org_id: # Add OrganizationId if discovered
            api_headers['OrganizationId'] = str(self.org_id)

        all_events = []
        current_url = events_api_url
        page_count = 0
        max_pages = 10  # Safety limit to prevent infinite loops
        
        while current_url and page_count < max_pages:
            page_count += 1
            logger.info(f"Fetching events page {page_count} from OData API: {current_url} with params: {odata_params if page_count == 1 else 'URL contains params'}")
            
            # For subsequent pages, don't pass params as they're included in the nextLink URL
            if page_count == 1:
                response = self.session.get(current_url, params=odata_params, headers=api_headers)
            else:
                response = self.session.get(current_url, headers=api_headers)

            if response and response.status_code == 200:
                try:
                    data = response.json()
                    # OData responses often have items in a "value" list
                    event_list = data.get("value", []) if isinstance(data, dict) else data if isinstance(data, list) else []
                    logger.info(f"Successfully fetched {len(event_list)} events from page {page_count}.")
                    all_events.extend(event_list)
                    
                    # Check for pagination - OData uses @odata.nextLink
                    next_link = None
                    if isinstance(data, dict):
                        next_link = data.get("@odata.nextLink") or data.get("odata.nextLink")
                    
                    if next_link:
                        current_url = next_link
                        logger.info(f"Found next page link, continuing pagination...")
                    else:
                        logger.info(f"No more pages available, pagination complete.")
                        break
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON from {current_url}: {e}. Response text: {response.text[:500]}")
                    break
            else:
                status = response.status_code if response else "No Response"
                reason = response.reason if response else "N/A"
                logger.warning(f"Failed to fetch events from OData API page {page_count}. Status: {status}, Reason: {reason}. URL: {response.url if response else current_url}")
                if response : logger.debug(f"Response content: {response.text[:500]}")
                break
        
        if page_count >= max_pages:
            logger.warning(f"Reached maximum page limit ({max_pages}) for API pagination")
        
        logger.info(f"Total events fetched across {page_count} pages: {len(all_events)}")
        return all_events
    def _fetch_meetings_from_dom(self):
        """Fallback to extract meeting information from the DOM."""
        meetings_data = [] # Store as list of dicts similar to API response
        logger.info(f"Attempting to extract meetings from DOM of {self.resolved_url}")
        try:
            response = self.session.get(self.resolved_url)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch page for DOM parsing: {response.status_code}")
                return meetings_data
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Material-UI specific selectors for CivicClerk based on sample HTML
            # Look for list items that contain meeting data
            meeting_elements = soup.select('li.cpp-MuiListItem-container')
            logger.info(f"Found {len(meeting_elements)} Material-UI list items in DOM.")

            for element in meeting_elements:
                meeting_info = {}
                
                # Extract event ID from data attributes or links
                event_id = None
                # Look for anchor tag with data-id attribute
                anchor = element.select_one('a[data-id]')
                if anchor:
                    event_id = anchor.get('data-id')
                
                # Also try href pattern like /event/3/files
                if not event_id:
                    event_link = element.select_one('a[href*="/event/"]')
                    if event_link:
                        href = event_link.get('href', '')
                        # Extract ID from URL like /event/3/files
                        id_match = re.search(r'/event/(\d+)', href)
                        if id_match:
                            event_id = id_match.group(1)
                
                meeting_info['id'] = event_id
                
                # Extract meeting title - look for h3 with specific ID pattern
                title_el = element.select_one('h3[id*="eventListRow"][id*="title"]')
                if not title_el:
                    # Fallback to any h3 element
                    title_el = element.select_one('h3')
                
                meeting_title = title_el.get_text(strip=True) if title_el else "Meeting from DOM"
                meeting_info['eventName'] = meeting_title                
                # Extract date from data-date attribute first (most reliable)
                date_str = None
                anchor = element.select_one('a[data-date]')
                if anchor:
                    date_str = anchor.get('data-date')  # Should be ISO format like "2024-05-14T18:00:00Z"
                
                # If no data-date, try to find date in text content of datetime div
                if not date_str:
                    datetime_div = element.select_one('div[id*="eventListRow"][id*="datetime"]')
                    if datetime_div:
                        # Look for date text in the format "Tuesday May 14, 2024 at 6:00 PM PST"
                        date_text = datetime_div.get_text(strip=True)
                        # Extract date part before "at"
                        if " at " in date_text:
                            date_part = date_text.split(" at ")[0]
                            time_part = date_text.split(" at ")[1]
                            # Parse the date part like "Tuesday May 14, 2024"
                            # Remove day of week and parse
                            date_clean = re.sub(r'^\w+\s+', '', date_part)  # Remove "Tuesday "
                            # Add time part
                            date_str = f"{date_clean} {time_part}"
                
                # If still no date, try data-date on container div
                if not date_str:
                    container_div = element.select_one('div[data-date]')
                    if container_div:
                        date_str = container_div.get('data-date')
                
                # Set the startDateTime
                if date_str:
                    meeting_info['startDateTime'] = date_str
                
                # Extract committee/group name from chip element
                group_name = None
                chip_element = element.select_one('.cpp-MuiChip-label')
                if chip_element:
                    group_name = chip_element.get_text(strip=True)
                
                # If no chip found, try to infer from meeting title
                if not group_name:
                    title_lower = meeting_title.lower()
                    if 'city council' in title_lower:
                        group_name = 'City Council'
                    elif 'planning commission' in title_lower:
                        group_name = 'Planning Commission'
                    elif 'committee' in title_lower:
                        group_name = 'Committee'
                    else:
                        group_name = 'General'
                
                meeting_info['groupName'] = group_name                
                # Extract attachments/documents - look for href pointing to files
                attachments = []
                
                # Look for the main anchor tag that leads to meeting files
                main_link = element.select_one('a[href*="/event/"][href*="/files"]')
                if main_link and event_id:
                    # This typically leads to a page with all meeting documents
                    files_url = urljoin(self.portal_domain_base, main_link.get('href'))
                    
                    # Create a generic meeting link asset
                    attachments.append({
                        'id': f"meeting_{event_id}",
                        'fileId': None,
                        'name': f"{meeting_title} - Meeting Documents",
                        'type': 'meeting_info',
                        'url': files_url
                    })
                
                # Look for any direct download links in the element
                download_links = element.select('a[href*="download"], a[href*="Download"], a[href*="file"], a[title*="Download"]')
                for link in download_links:
                    href = link.get('href')
                    if href:
                        file_url = urljoin(self.portal_domain_base, href)
                        link_text = link.get_text(strip=True)
                        
                        # Determine document type
                        doc_type = 'attachment'
                        if 'agenda' in link_text.lower() or 'agenda' in href.lower():
                            doc_type = 'agenda'
                        elif 'minutes' in link_text.lower() or 'minutes' in href.lower():
                            doc_type = 'minutes'
                        elif 'packet' in link_text.lower() or 'packet' in href.lower():
                            doc_type = 'packet'
                        
                        attachments.append({
                            'id': None,
                            'fileId': None,
                            'name': link_text or f"{doc_type.title()} Document",
                            'type': doc_type,
                            'url': file_url
                        })
                
                meeting_info['attachments'] = attachments
                
                # Only add meeting if we have minimum required information
                if meeting_info.get('eventName') and (meeting_info.get('startDateTime') or meeting_info.get('id')):
                    meetings_data.append(meeting_info)                    
                    logger.debug(f"Extracted meeting: {meeting_info['eventName']} on {meeting_info.get('startDateTime', 'unknown date')}")
            
            logger.info(f"Extracted {len(meetings_data)} meetings from Material-UI DOM structure.")
        except Exception as e:
            logger.error(f"Error extracting meetings from DOM: {e}")
        return meetings_data
    def events(self, start_date=None, end_date=None): # This method is expected by the base scraper structure
        """Yields batches of meeting data."""
        # Primary strategy: OData API
        api_events = self._fetch_events_via_odata_api(start_date_obj=start_date, end_date_obj=end_date)
        if api_events:
            logger.info(f"Yielding {len(api_events)} events from OData API.")
            yield api_events # Yield the whole batch
            return

        # Fallback 1: Try legacy API methods if any were discovered and are different
        # (This part can be expanded if _discover_api_configuration finds other usable meeting endpoints)
        # For now, we assume OData is the main API attempt.

        # Fallback 2: DOM parsing
        logger.warning("OData API failed or returned no events. Falling back to DOM parsing.")
        dom_events = self._fetch_meetings_from_dom()
        if dom_events:
            logger.info(f"Yielding {len(dom_events)} events from DOM parsing.")
            yield dom_events
            return
        
        logger.warning("All methods (API, DOM) failed to retrieve any events.")
        yield [] # Yield empty list if nothing found


    def scrape(self, download=True, start_date=None, end_date=None):
        """Scrape meetings and their assets from the CivicClerk site."""
        ac = AssetCollection()
        logger.info(f"Starting to scrape meetings from {self.resolved_url}")
        if start_date or end_date:
             logger.info(f"Date range: Start={start_date}, End={end_date}")        # The 'events' method yields a list (batch) of event data (dictionaries)
        for events_batch in self.events(start_date=start_date, end_date=end_date): # Pass date parameters to events() method
            if not events_batch:
                logger.info("Received an empty batch of events.")
                continue
            
            logger.info(f"Processing a batch of {len(events_batch)} events.")
            for event_data in events_batch:
                if not isinstance(event_data, dict):
                    logger.warning(f"Skipping non-dict event data: {event_data}")
                    continue
                try:
                    event_id_raw = event_data.get('id')
                    event_name = event_data.get('eventName', 'Unknown Event')
                    committee_name = event_data.get('groupName', event_data.get('departmentName', event_name)) # Use event name as fallback committee
                    meeting_datetime_str = event_data.get('startDateTime')
                    
                    meeting_datetime_obj = self._parse_meeting_datetime(meeting_datetime_str)
                    if not meeting_datetime_obj:
                        logger.warning(f"Could not parse datetime for event '{event_name}', skipping.")
                        continue
                    
                    # Filter by date if start_date or end_date provided
                    current_event_date = meeting_datetime_obj.date()
                    if start_date and current_event_date < start_date:
                        # logger.debug(f"Event {event_name} on {current_event_date} is before start_date {start_date}, skipping.")
                        continue
                    if end_date and current_event_date > end_date:
                        # logger.debug(f"Event {event_name} on {current_event_date} is after end_date {end_date}, skipping.")
                        continue


                    meeting_id_str = f"civicclerk_{self.tenant_name}_{event_id_raw}" if event_id_raw else f"civicclerk_{self.tenant_name}_{meeting_datetime_obj.strftime('%Y%m%d%H%M')}"

                    # Attachments/Files should be part of event_data if from OData /Events
                    # The key might be 'attachments', 'Files', or similar.
                    # This needs to match what _fetch_events_via_odata_api returns.
                    raw_attachments = event_data.get('attachments', event_data.get('Files', []))
                    if isinstance(raw_attachments, dict): # Handle cases where it might be a dict with 'value'
                        raw_attachments = raw_attachments.get('value', [])
                    if not isinstance(raw_attachments, list): raw_attachments = []


                    if not raw_attachments and event_id_raw:
                        logger.debug(f"No inline attachments for event {event_id_raw}. Consider a separate call to fetch documents if API structure demands it.")
                        # If documents are NOT nested in /Events, a separate call would be needed here.
                        # For now, assuming they are nested or we only process what's inline.

                    asset_count_for_meeting = 0
                    for doc_info in raw_attachments:
                        if not isinstance(doc_info, dict): continue

                        file_id = doc_info.get('id') or doc_info.get('fileId')
                        doc_name = doc_info.get('name') or doc_info.get('fileName') or "Document"
                        doc_type_api = (doc_info.get('type', '') or doc_info.get('documentType', '')).lower()

                        if not doc_type_api: # Infer type
                            if 'agenda' in doc_name.lower(): doc_type_api = 'agenda'
                            elif 'minutes' in doc_name.lower(): doc_type_api = 'minutes'
                            elif 'packet' in doc_name.lower(): doc_type_api = 'packet'
                            else: doc_type_api = 'attachment'
                        
                        asset_url = None
                        if file_id: # Prefer API download link
                            asset_url = f"{self.api_url_base_for_calls}/Meetings/GetMeetingFileStream(fileId={file_id},plainText=false)"
                        elif doc_info.get('url'): # Fallback to a direct URL if present
                            asset_url = urljoin(self.portal_domain_base, doc_info.get('url'))
                        
                        if asset_url:
                            asset = self.create_asset(doc_name, asset_url, doc_type_api, committee_name, meeting_datetime_obj, meeting_id_str)
                            ac.append(asset)
                            asset_count_for_meeting +=1
                            logger.debug(f"Added asset: {doc_name} for meeting {event_name}")
                    
                    if not asset_count_for_meeting:
                         logger.info(f"No downloadable assets found/parsed for meeting: {event_name} (ID: {event_id_raw}) on {meeting_datetime_obj.date()}")
                         # Create a placeholder asset for the meeting itself if no documents
                         placeholder_url = f"{self.portal_domain_base}/event/{event_id_raw}" if event_id_raw else self.resolved_url
                         asset = self.create_asset(event_name + " (Meeting Link)", placeholder_url, "meeting_info", committee_name, meeting_datetime_obj, meeting_id_str)
                         ac.append(asset)


                except Exception as e:
                    logger.error(f"Error processing event data: {event_data.get('eventName', event_data.get('id')) if isinstance(event_data, dict) else event_data} - {e}", exc_info=True)
                    continue
        
        logger.info(f"Scraping complete. Found {len(ac)} total assets.")
        if download and len(ac) > 0:
            asset_dir = Path(self.cache.path, "assets", self.tenant_name) # Add tenant name to path
            asset_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Downloading {len(ac)} assets to {asset_dir}")
            for asset_obj in ac: # Renamed to asset_obj to avoid conflict
                dir_str = str(asset_dir)
                try:
                    # Pass the current session for consistent headers, cookies
                    asset_obj.download(target_dir=dir_str, session=self.session)
                    if asset_obj.asset_type == "meeting_info":
                        logger.info(f"Saved meeting info to file: {asset_obj.asset_name} -> {asset_obj.filepath}")
                    else:
                        logger.info(f"Successfully downloaded: {asset_obj.asset_name} to {asset_obj.filepath}")
                except Exception as e_download:
                    logger.error(f"Failed to download {asset_obj.asset_name} from {asset_obj.url}: {e_download}")


        return ac

