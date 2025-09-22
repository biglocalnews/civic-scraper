import logging
import re
from typing import Optional, List # List for type hinting
from datetime import datetime # For date parsing if needed at this level

try:
    from civic_scraper.base.site import Site as BaseSite 
    from civic_scraper.base.asset import AssetCollection
    from civic_scraper.base.cache import Cache
except ImportError:
    class BaseSite:
        def __init__(self, url: str, *, 
                     place: Optional[str] = None,
                     state_or_province: Optional[str] = None,
                     cache: Optional[object] = None, 
                     parser_kls = None, 
                     committee_id: Optional[str] = None, 
                     timezone: Optional[str] = "US/Eastern",
                     **kwargs): 
            self.url = url
            self.place = place
            self.state_or_province = state_or_province
            self.cache = cache
            self.parser_kls = parser_kls
            self.committee_id = committee_id
            self.timezone = timezone
        def scrape(self, start_date=None, end_date=None, committee_name=None, **kwargs) -> 'AssetCollection':
            raise NotImplementedError
    class AssetCollection(list):
        def __init__(self, *args): 
            super().__init__(*args)
        # Removed .add() as AssetCollection is a list and uses .append()
        # def add(self, asset): self.append(asset) 
        def extend(self, assets): super().extend(assets)
    class Cache:
        def __init__(self, path=None): self.path = path
        def get(self, key): return None # Placeholder
        def set(self, key, value): pass # Placeholder

from urllib.parse import urlparse 

from .type1 import GranicusType1Scraper
from .type2 import GranicusType2Scraper
from .type3 import GranicusType3Scraper
from .type4 import GranicusType4Scraper
from .type5 import GranicusType5Scraper

logger = logging.getLogger(__name__)

class GranicusSite(BaseSite):
    """
    Scraper for government sites powered by Granicus.
    It orchestrates different Granicus HTML structure parsers (Type1, Type2, etc.),
    runs all of them, and picks the result using a prioritized logic:
    1. If committee_names is provided, prefer results from panel-specific scrapers.
    2. Otherwise, or if panel-specific scrapers yield no results, pick by most assets overall.
    """

    def __init__(self, url: str, *, 
                 place: Optional[str] = None,
                 state_or_province: Optional[str] = None,
                 cache: Optional[Cache] = None, 
                 timezone: Optional[str] = "US/Eastern", 
                 committee_names: Optional[List[str]] = None,
                 **kwargs 
                ):
        parser_kls_arg = kwargs.pop('parser_kls', None)
        committee_id_arg = kwargs.pop('committee_id', None)
        
        if 'name' in kwargs:
            name_arg_value = kwargs.pop('name')
            logger.warning(
                f"GranicusSite initialized with an unexpected 'name' keyword argument (value: '{name_arg_value}'). "
                "This argument is not used by GranicusSite and not passed to the base Site class."
            )
        
        if kwargs:
            logger.warning(
                f"GranicusSite initialized with unexpected keyword arguments: {list(kwargs.keys())}. "
                "These are not passed to the base Site class."
            )

        super().__init__(
            url, 
            place=place, 
            state_or_province=state_or_province, 
            cache=cache, 
            timezone=timezone,
            parser_kls=parser_kls_arg,    
            committee_id=committee_id_arg 
        )
        
        self.committee_names = committee_names if committee_names is not None else []
        # Order can still be relevant if multiple scrapers of the same "category" (e.g. panel-specific) tie on asset count.
        self.scraper_instances_with_info = [
            {"instance": GranicusType1Scraper(cache=self.cache), "name": "GranicusType1Scraper"},
            {"instance": GranicusType2Scraper(cache=self.cache), "name": "GranicusType2Scraper"},
            {"instance": GranicusType4Scraper(cache=self.cache), "name": "GranicusType4Scraper"},
            {"instance": GranicusType3Scraper(cache=self.cache), "name": "GranicusType3Scraper"}, # Type 3 is often general
            {"instance": GranicusType5Scraper(cache=self.cache), "name": "GranicusType5Scraper"}, # New Type 5 single-page tables
        ]

    def _detect_scraper_type(self, html_content: str) -> str:
        """
        Analyze the HTML structure to determine which scraper type should be used.
        
        Returns:
            str: The name of the detected scraper type (e.g., "GranicusType1Scraper")
        """
        from bs4 import BeautifulSoup
        import re
        import os
        from pathlib import Path
        
        soup = BeautifulSoup(html_content, 'html.parser')

        debug_detection = os.getenv('GRANICUS_DEBUG_DETECTION', '').lower() in ('1', 'true', 'yes')
        if debug_detection:
            logger.info("[DETECT][START] Granicus detection debug enabled (env GRANICUS_DEBUG_DETECTION=1)")
            logger.info(f"[DETECT] HTML length: {len(html_content):,} characters")
            logger.info(f"[DETECT] Count <div.CollapsiblePanelTab*>: {len(soup.find_all('div', class_=['CollapsiblePanelTab', 'CollapsiblePanelTabNotSelected']))}")
            logger.info(f"[DETECT] Presence of TabbedPanels: {bool(soup.find('div', class_='TabbedPanels'))}")
            logger.info(f"[DETECT] Count listingTable: {len(soup.find_all('table', class_='listingTable'))}")
            logger.info(f"[DETECT] Count responsive-table lists: {len(soup.find_all(['ol','ul'], class_='responsive-table'))}")
        
        # Check for CollapsiblePanelTab structure (Type 1, 2, 4)
        collapsible_panels = soup.find_all('div', class_=['CollapsiblePanelTab', 'CollapsiblePanelTabNotSelected'])
        if collapsible_panels:
            logger.info(f"✓ Found CollapsiblePanelTab structure with {len(collapsible_panels)} panels")
            
            # Log panel names for debugging
            panel_names = []
            for panel in collapsible_panels:
                text_container = panel.find(['a', 'h3', 'span', 'div'])
                panel_name = panel.get_text(strip=True)
                if text_container:
                    panel_name = text_container.get_text(strip=True)
                panel_names.append(panel_name)
            logger.info(f"  Available panels: {panel_names}")
            
            # Check if TabbedPanels is INSIDE CollapsiblePanelContent (Type 1)
            for panel in collapsible_panels:
                content_div = panel.find_next_sibling('div', class_='CollapsiblePanelContent')
                if content_div:
                    tabbed_panels_inside = content_div.find('div', class_='TabbedPanels')
                    if tabbed_panels_inside:
                        logger.info("✓ DETECTED TYPE 1: TabbedPanels found INSIDE CollapsiblePanelContent")
                        logger.info("  Structure: CollapsiblePanelTab → CollapsiblePanelContent → TabbedPanels")
                        return "GranicusType1Scraper"
            
            # Check for Type 2 vs Type 4 structure
            # Look for TabbedPanels OUTSIDE of CollapsiblePanelContent
            main_tabbed_panels = soup.find('div', class_='TabbedPanels')
            if main_tabbed_panels:
                # Check if TabbedPanels is outside/above the CollapsiblePanelTab divs
                first_panel = collapsible_panels[0] if collapsible_panels else None
                if first_panel:
                    # Check if main_tabbed_panels comes before the first panel in document order
                    try:
                        panel_pos = str(soup).find(str(first_panel))
                        tabbed_pos = str(soup).find(str(main_tabbed_panels))
                        if tabbed_pos < panel_pos:  # TabbedPanels comes before panels
                            # Now distinguish between Type 2 (listingTable) and Type 4 (responsive-table list)
                            # Check within a sample panel content for the table structure
                            sample_content = first_panel.find_next_sibling('div', class_='CollapsiblePanelContent')
                            if sample_content:
                                listing_table = sample_content.find('table', class_='listingTable')
                                responsive_list = sample_content.find(['ol', 'ul'], class_='responsive-table')
                                if responsive_list:
                                    logger.info("✓ DETECTED TYPE 4: Found responsive-table list structure")
                                    logger.info("  Structure: TabbedPanels (years) → CollapsiblePanelTab → responsive-table list")
                                    return "GranicusType4Scraper"
                                elif listing_table:
                                    logger.info("✓ DETECTED TYPE 2: Found listingTable structure")
                                    logger.info("  Structure: TabbedPanels (years) → CollapsiblePanelTab → listingTable")
                                    return "GranicusType2Scraper"
                    except (AttributeError, ValueError):
                        pass

            # Additional heuristic (NEW): Even if the ordering test above failed, attempt to classify
            # by inspecting each panel's content directly before giving up on structured detection.
            for panel in collapsible_panels:
                content_div = panel.find_next_sibling('div', class_='CollapsiblePanelContent')
                if not content_div:
                    continue
                has_inner_tabbed = bool(content_div.find('div', class_='TabbedPanels'))
                listing_table_inside = content_div.find('table', class_='listingTable')
                responsive_list_inside = content_div.find(['ol','ul'], class_='responsive-table')
                # If responsive list but no inner TabbedPanels => Type 4 (single-year or no year tabs visible)
                if responsive_list_inside and not has_inner_tabbed:
                    logger.info("✓ DETECTED TYPE 4 (heuristic): Found responsive-table list inside panel content without inner TabbedPanels")
                    return "GranicusType4Scraper"
                # If listing table inside panel content without inner TabbedPanels => likely Type 2
                if listing_table_inside and not has_inner_tabbed:
                    logger.info("✓ DETECTED TYPE 2 (heuristic): Found listingTable inside panel content without inner TabbedPanels")
                    return "GranicusType2Scraper"
        
        # Evaluate structures without collapsible panels
        main_tabbed_panels = soup.find('div', class_='TabbedPanels') or soup.find('div', id=re.compile(r'TabbedPanels?1', re.I))
        # Gather table variants once
        listing_tables_case = soup.find_all('table', class_='listingTable')
        if not listing_tables_case:
            listing_tables_case = soup.find_all('table', class_=re.compile(r'listingtable2?', re.I))
        # Type5 precedence: no panels, no TabbedPanels, but listingtable-style tables present
        if not collapsible_panels and not main_tabbed_panels and listing_tables_case:
            logger.info(f"✓ DETECTED TYPE 5: Found {len(listing_tables_case)} listingtable-style tables without panels or TabbedPanels")
            return "GranicusType5Scraper"
        # Type3: no panels, but has TabbedPanels OR listing tables (direct year/tabless listing)
        if not collapsible_panels and (main_tabbed_panels or listing_tables_case):
            logger.info("✓ DETECTED TYPE 3: No CollapsiblePanelTab structure, has TabbedPanels/listingTable")
            logger.info("  Structure: TabbedPanels (years) → listingTable (direct) or direct tables")
            if main_tabbed_panels:
                logger.info(f"  Found TabbedPanels: {main_tabbed_panels.get('id', 'no id')} class='{main_tabbed_panels.get('class', [])}'")
            if listing_tables_case:
                logger.info(f"  Found {len(listing_tables_case)} listingTable(s)")
            return "GranicusType3Scraper"
        
        # Default fallback: try Type 1 first as it's most common
        logger.warning("⚠ Could not definitively detect scraper type from HTML structure")
        logger.warning("  Defaulting to Type 1 (most common)")

        if debug_detection:
            # Save HTML for offline inspection when detection failed
            try:
                out_dir = Path("debug_detection")
                out_dir.mkdir(parents=True, exist_ok=True)
                # Short hash for file uniqueness
                import hashlib
                digest = hashlib.sha1(html_content.encode('utf-8')).hexdigest()[:10]
                out_file = out_dir / f"undetected_{digest}.html"
                out_file.write_text(html_content, encoding='utf-8')
                logger.info(f"[DETECT] Saved undetected HTML to {out_file}")
            except Exception as e:
                logger.error(f"[DETECT] Failed to write undetected HTML debug file: {e}")
            logger.info("[DETECT][END] Fallback to Type1 after heuristics.")
        return "GranicusType1Scraper"

    def scrape(
        self,
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None,   
        download: bool = False, 
        **kwargs 
    ) -> AssetCollection:
        site_description = self.place or self.url 

        logger.info(
            f"Starting Granicus scrape for site: '{site_description}' URL: {self.url} "
            f"(Committees: {self.committee_names if self.committee_names else 'N/A'})"
        )

        if not self.scraper_instances_with_info:
            logger.error(f"No Granicus scraper types initialized for site '{site_description}'.")
            return AssetCollection()        # Use the first scraper instance to fetch HTML, assuming all inherit _fetch_html
        initial_html_content = self.scraper_instances_with_info[0]["instance"]._fetch_html(self.url)

        if not initial_html_content:
            logger.error(f"Failed to fetch initial HTML content from {self.url} for site '{site_description}'. Aborting scrape.")
            return AssetCollection()        # Detect the appropriate scraper type based on HTML structure
        detected_scraper_name = self._detect_scraper_type(initial_html_content)
        logger.info("=" * 50)
        logger.info(f"🎯 USING DETECTED SCRAPER: {detected_scraper_name}")
        logger.info("=" * 50)
        
        # Find the detected scraper instance
        detected_scraper_info = None
        for scraper_info in self.scraper_instances_with_info:
            if scraper_info["name"] == detected_scraper_name:
                detected_scraper_info = scraper_info
                break
        
        if not detected_scraper_info:
            logger.error(f"Detected scraper {detected_scraper_name} not found in available scrapers for site '{site_description}'.")
            return AssetCollection()

        # Use only the detected scraper for all committees
        all_assets = AssetCollection()
        committees_to_scrape = self.committee_names if self.committee_names else [None]
        
        for committee_name in committees_to_scrape:
            scraper_instance = detected_scraper_info["instance"]
            scraper_name = detected_scraper_info["name"]
            
            logger.info(f"Using detected scraper {scraper_name} for site '{site_description}' (Committee: {committee_name})...")
            
            # Skip scrapers that require panel name when none is provided
            if scraper_instance.requires_panel_name() and not committee_name:
                logger.info(
                    f"{scraper_name} requires a committee/panel name, "
                    f"but none was provided. Skipping for site '{site_description}'."
                )
                continue
            
            assets_from_this_committee = scraper_instance.extract_and_process_meetings(
                html_content=initial_html_content,
                site_url=self.url,
                site_place=self.place, 
                site_state=self.state_or_province, 
                site_committee_name=committee_name, 
                site_timezone=self.timezone 
            )

            if assets_from_this_committee and len(assets_from_this_committee) > 0:
                logger.info(
                    f"Successfully extracted {len(assets_from_this_committee)} assets "
                    f"using {scraper_name} for site '{site_description}' (Committee: {committee_name})."
                )
                all_assets.extend(assets_from_this_committee)
            else:
                logger.info(
                    f"{scraper_name} did not yield assets for "
                    f"site '{site_description}' (Committee: {committee_name})."
                )

        # Automatic targeted fallback: If detected Type5 produced zero assets, try Type3 automatically
        if len(all_assets) == 0 and detected_scraper_name == "GranicusType5Scraper":
            logger.info(
                "Type5 produced zero assets; attempting automatic fallback to Type3 (single-page tables sometimes mimic Type5 detection)."
            )
            fallback_type3 = None
            for scraper_info in self.scraper_instances_with_info:
                if scraper_info["name"] == "GranicusType3Scraper":
                    fallback_type3 = scraper_info["instance"]
                    break
            if fallback_type3:
                for committee_name in committees_to_scrape:
                    if fallback_type3.requires_panel_name() and not committee_name:
                        continue
                    logger.info(
                        f"[FALLBACK->Type3] Trying GranicusType3Scraper for site '{site_description}' (Committee: {committee_name})..."
                    )
                    fb_assets = fallback_type3.extract_and_process_meetings(
                        html_content=initial_html_content,
                        site_url=self.url,
                        site_place=self.place,
                        site_state=self.state_or_province,
                        site_committee_name=committee_name,
                        site_timezone=self.timezone
                    )
                    if fb_assets:
                        logger.info(
                            f"[FALLBACK->Type3] Extracted {len(fb_assets)} assets for committee {committee_name}."
                        )
                        all_assets.extend(fb_assets)
                if len(all_assets) == 0:
                    logger.info("[FALLBACK->Type3] No assets produced by Type3 fallback either.")
            else:
                logger.warning("Type3 scraper instance not available for fallback.")

        # --- Date Filtering on the aggregated AssetCollection ---
        final_assets_to_return = all_assets
        start_date_obj: Optional[datetime] = None
        end_date_obj: Optional[datetime] = None
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                logger.warning(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD. No start date filter applied for '{site_description}'.")
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            except ValueError:
                logger.warning(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD. No end date filter applied for '{site_description}'.")

        if start_date_obj or end_date_obj:
            if len(final_assets_to_return) > 0:
                filtered_assets = AssetCollection()
                for asset in final_assets_to_return: 
                    if not isinstance(asset.meeting_date, datetime):
                        logger.warning(f"Asset '{asset.asset_name}' for site '{site_description}' has invalid meeting_date type: {type(asset.meeting_date)}. Skipping date filter for this asset.")
                        filtered_assets.append(asset) 
                        continue

                    meeting_date_naive = asset.meeting_date.replace(tzinfo=None) if asset.meeting_date.tzinfo else asset.meeting_date

                    if start_date_obj and meeting_date_naive < start_date_obj:
                        continue
                    if end_date_obj and meeting_date_naive > end_date_obj:
                        continue
                    filtered_assets.append(asset) 
                
                logger.info(f"Returning {len(filtered_assets)} assets after date filtering for site '{site_description}'.")
                final_assets_to_return = filtered_assets
            else:
                logger.info(f"No assets were selected by any scraper, so no date filtering applied for site '{site_description}'.")
        else:
            logger.info(f"No date filtering requested for site '{site_description}'.")

        logger.info(f"Granicus scrape for site '{site_description}' (Committees: {self.committee_names}) finished. Returning {len(final_assets_to_return)} assets.")
        # Optional: Try all scrapers if we got zero assets (env-controlled)
        import os
        if len(final_assets_to_return) == 0 and os.getenv('GRANICUS_TRY_ALL_ON_EMPTY', '').lower() in ('1','true','yes'):
            logger.info("No assets from detected scraper; GRANICUS_TRY_ALL_ON_EMPTY=1 so attempting other scraper types as a fallback.")
            tried_names = {detected_scraper_name}
            for scraper_info in self.scraper_instances_with_info:
                if scraper_info['name'] in tried_names:
                    continue
                alt_instance = scraper_info['instance']
                alt_name = scraper_info['name']
                logger.info(f"[FALLBACK] Trying alternative scraper {alt_name}...")
                alt_assets_all = AssetCollection()
                for committee_name in committees_to_scrape:
                    if alt_instance.requires_panel_name() and not committee_name:
                        continue
                    alt_assets = alt_instance.extract_and_process_meetings(
                        html_content=initial_html_content,
                        site_url=self.url,
                        site_place=self.place,
                        site_state=self.state_or_province,
                        site_committee_name=committee_name,
                        site_timezone=self.timezone
                    )
                    if alt_assets:
                        alt_assets_all.extend(alt_assets)
                if alt_assets_all:
                    logger.info(f"[FALLBACK] {alt_name} produced {len(alt_assets_all)} assets. Using these results.")
                    final_assets_to_return = alt_assets_all
                    break
                else:
                    logger.info(f"[FALLBACK] {alt_name} produced 0 assets.")
            logger.info(f"Fallback process complete. Returning {len(final_assets_to_return)} assets after trying alternates.")
        return final_assets_to_return