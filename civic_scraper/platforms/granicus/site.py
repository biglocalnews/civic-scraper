import logging
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
        
        def extend(self, assets): super().extend(assets)
    class Cache:
        def __init__(self, path=None): self.path = path
        def get(self, key): return None 
        def set(self, key, value): pass 

from urllib.parse import urlparse 

from .type1 import GranicusType1Scraper
from .type2 import GranicusType2Scraper
from .type3 import GranicusType3Scraper
from .type4 import GranicusType4Scraper

logger = logging.getLogger(__name__)

class GranicusSite(BaseSite):
    """
    Scraper for government sites powered by Granicus.
    It orchestrates different Granicus HTML structure parsers (Type1, Type2, etc.),
    runs all of them, and picks the result using a prioritized logic:
    1. If committee_name is provided, prefer results from panel-specific scrapers.
    2. Otherwise, or if panel-specific scrapers yield no results, pick by most assets overall.
    """

    def __init__(self, url: str, *, 
                 place: Optional[str] = None,
                 state_or_province: Optional[str] = None,
                 cache: Optional[Cache] = None, 
                 timezone: Optional[str] = "US/Eastern", 
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
        
        # Order can still be relevant if multiple scrapers of the same "category" (e.g. panel-specific) tie on asset count.
        self.scraper_instances_with_info = [
            {"instance": GranicusType1Scraper(cache=self.cache), "name": "GranicusType1Scraper"},
            {"instance": GranicusType2Scraper(cache=self.cache), "name": "GranicusType2Scraper"},
            {"instance": GranicusType4Scraper(cache=self.cache), "name": "GranicusType4Scraper"},
            {"instance": GranicusType3Scraper(cache=self.cache), "name": "GranicusType3Scraper"}, # Type 3 is often general
        ]

    def scrape(
        self,
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None,   
        committee_name: Optional[str] = None, 
        download: bool = False, 
        **kwargs 
    ) -> AssetCollection:
        site_description = self.place or self.url 

        logger.info(
            f"Starting Granicus scrape for site: '{site_description}' URL: {self.url} "
            f"(Panel/Committee: {committee_name if committee_name else 'N/A'})"
        )

        if not self.scraper_instances_with_info:
            logger.error(f"No Granicus scraper types initialized for site '{site_description}'.")
            return AssetCollection()

        # Use the first scraper instance to fetch HTML, assuming all inherit _fetch_html
        initial_html_content = self.scraper_instances_with_info[0]["instance"]._fetch_html(self.url)

        if not initial_html_content:
            logger.error(f"Failed to fetch initial HTML content from {self.url} for site '{site_description}'. Aborting scrape.")
            return AssetCollection()

        # Store results along with info about the scraper
        results_data = [] 

        for scraper_info in self.scraper_instances_with_info:
            scraper_instance = scraper_info["instance"]
            scraper_name = scraper_info["name"]
            
            logger.info(f"Attempting scrape with {scraper_name} for site '{site_description}'...")
            
            assets_from_this_type = AssetCollection() # Default to empty
            if scraper_instance.requires_panel_name() and not committee_name:
                logger.info(
                    f"{scraper_name} requires a committee/panel name, "
                    f"but none was provided. Skipping this scraper type for site '{site_description}'."
                )
            else:
                assets_from_this_type = scraper_instance.extract_and_process_meetings(
                    html_content=initial_html_content,
                    site_url=self.url,
                    site_place=self.place, 
                    site_state=self.state_or_province, 
                    site_committee_name=committee_name, 
                    site_timezone=self.timezone 
                )

            if assets_from_this_type and len(assets_from_this_type) > 0:
                logger.info(
                    f"Successfully extracted {len(assets_from_this_type)} assets "
                    f"using {scraper_name} for site '{site_description}'."
                )
            else:
                logger.info(
                    f"{scraper_name} did not yield assets or failed its checks for "
                    f"site '{site_description}' URL: {self.url} (Panel: {committee_name if committee_name else 'N/A'})."
                )
            
            results_data.append({
                "assets": assets_from_this_type if assets_from_this_type else AssetCollection(),
                "scraper_name": scraper_name,
                "requires_panel": scraper_instance.requires_panel_name()
            })
        
        # --- Smarter Result Selection Logic ---
        best_asset_collection = AssetCollection()
        selected_scraper_name = "None (no assets found)"

        panel_specific_candidates = []
        general_candidates = []

        for res_data in results_data:
            if committee_name and res_data["requires_panel"]:
                panel_specific_candidates.append(res_data)
            else: # Scrapers that don't require a panel, or if no committee_name was given
                general_candidates.append(res_data)
        
        # Prioritize panel-specific results if committee_name was given and candidates exist
        if committee_name and panel_specific_candidates:
            # Filter out empty results from panel-specific candidates
            non_empty_panel_specific = [cand for cand in panel_specific_candidates if len(cand["assets"]) > 0]
            if non_empty_panel_specific:
                best_panel_specific_res = max(non_empty_panel_specific, key=lambda x: len(x["assets"]))
                best_asset_collection = best_panel_specific_res["assets"]
                selected_scraper_name = best_panel_specific_res["scraper_name"]
                logger.info(f"Prioritized panel-specific: Selected result from {selected_scraper_name} with {len(best_asset_collection)} assets.")

        # If no suitable panel-specific result, consider general candidates (or all if no committee_name)
        if len(best_asset_collection) == 0:
            all_candidates_for_max = panel_specific_candidates + general_candidates # Consider all if panel-specific failed
            if not committee_name: # If no committee name, all are effectively "general" for selection
                all_candidates_for_max = results_data

            non_empty_overall = [cand for cand in all_candidates_for_max if len(cand["assets"]) > 0]
            if non_empty_overall:
                best_overall_res = max(non_empty_overall, key=lambda x: len(x["assets"]))
                best_asset_collection = best_overall_res["assets"]
                selected_scraper_name = best_overall_res["scraper_name"]
                logger.info(f"Fallback/General: Selected result from {selected_scraper_name} with {len(best_asset_collection)} assets.")
            else:
                 logger.warning(
                    f"No Granicus scraper type was successful in finding any assets for site '{site_description}' URL: {self.url} "
                    f"(Panel: {committee_name if committee_name else 'N/A'})"
                )
        
        # --- Date Filtering on the chosen best_asset_collection ---
        final_assets_to_return = best_asset_collection # Start with the selected collection
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
            if len(final_assets_to_return) > 0: # Only filter if there are assets
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
                
                logger.info(f"Returning {len(filtered_assets)} assets after date filtering (selected from {selected_scraper_name}) for site '{site_description}'.")
                final_assets_to_return = filtered_assets
            else:
                 logger.info(f"No assets were selected by any scraper, so no date filtering applied for site '{site_description}'.")
        else:
            logger.info(f"No date filtering requested for site '{site_description}'.")

        logger.info(f"Granicus scrape for site '{site_description}' (Panel: {committee_name}) finished. "
                      f"Best result from {selected_scraper_name}. Returning {len(final_assets_to_return)} assets.")
        return final_assets_to_return

