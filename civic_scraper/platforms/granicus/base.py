import requests
from bs4 import BeautifulSoup
import re

# import json # Not strictly needed in base after refactor, but type scrapers might use it.
from datetime import datetime, time as dt_time  # Added dt_time for meeting_time
from urllib.parse import (
    urljoin,
    urlparse,
    quote_plus,
)  # Added quote_plus for filename sanitization
import os
from abc import ABC, abstractmethod
import logging

# Attempt to import from civic_scraper, with placeholders if not found (for standalone testing)
try:
    from civic_scraper.base.asset import Asset, AssetCollection
    from civic_scraper.base.cache import Cache  # Actual Cache class

    # Assuming civic_scraper.__version__ might be available
    try:
        from civic_scraper import __version__ as CIVIC_SCRAPER_VERSION
    except ImportError:
        CIVIC_SCRAPER_VERSION = "unknown"
except ImportError:
    logger_init = logging.getLogger(__name__)  # Temp logger for this block
    logger_init.warning(
        "Could not import Asset, AssetCollection, or Cache from civic_scraper. "
        "Using placeholder definitions. Ensure civic_scraper is installed and in PYTHONPATH for full functionality."
    )
    from dataclasses import dataclass  # Keep dataclass for placeholder Asset

    @dataclass
    class Asset:  # Placeholder matching the fields from user's asset.py
        url: str
        asset_name: str = None  # Title of an asset. Ex:  City Council Regular Meeting
        committee_name: str = None
        place: str = (
            None  # Lowercase with spaces and punctuation removed. Ex: menlopark
        )
        place_name: str = None  # Human-readable place name. Ex: Menlo Park
        state_or_province: str = None
        asset_type: str = None  # Ex: agenda
        meeting_date: datetime = None  # Date of meeting
        meeting_time: dt_time = None  # Time of meeting
        meeting_id: str = None  # Unique meeting ID
        scraped_by: str = None
        content_type: str = None
        content_length: str = None

    class AssetCollection(list):  # Placeholder now correctly inherits from list
        def __init__(self, *args):
            super().__init__(*args)

        # No 'add' method here, use 'append' as it's a list

    class Cache:  # Placeholder reflecting the user-provided Cache structure
        def __init__(self, path=None):
            self.path = path  # In real Cache, _path_from_env or _path_default are used if path is None
            logger_init.info(f"Placeholder Cache initialized with path: {self.path}")

        def write(self, name, content):  # Expects string content
            out_path_str = name
            if self.path:
                out_path_str = os.path.join(self.path, name)

            out = Path(out_path_str)
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(content)
            logger_init.debug(f"Placeholder Cache: wrote to {str(out)}")
            return str(out)

        @property
        def artifacts_path(self):
            if not self.path:
                return "placeholder_artifacts"
            return str(Path(self.path).joinpath("artifacts"))

    from pathlib import Path

    CIVIC_SCRAPER_VERSION = "placeholder_version"


logger = logging.getLogger(__name__)


class GranicusBaseScraper(ABC):
    """
    Abstract base class for scraping Granicus platforms.
    """

    def __init__(self, cache: Cache | None = None):
        self.base_url = None
        self.cache = cache

    def _generate_cache_name_from_url(self, url: str) -> str:
        """
        Generates a filesystem-friendly name from a URL for caching.
        """
        parsed_url = urlparse(url)
        name_parts = [parsed_url.netloc]
        path_segments = [segment for segment in parsed_url.path.split("/") if segment]
        name_parts.extend(path_segments)

        if parsed_url.query:
            name_parts.append(parsed_url.query)

        base_name = "_".join(name_parts)
        sanitized_name = re.sub(r"[^\w.\-_]", "_", base_name)
        max_len = 100
        return sanitized_name[:max_len] + ".html"

    def _fetch_html(self, url: str) -> str | None:
        """
        Fetches HTML content from a specified URL.
        If a Cache object with a 'write' method is provided, it saves the fetched HTML string.
        """
        can_write_cache = self.cache and hasattr(self.cache, "write")

        if not self.cache:
            logger.debug(
                f"No cache object provided to GranicusBaseScraper for URL: {url}."
            )
        elif not can_write_cache:
            logger.warning(
                f"The provided Cache object (type: {type(self.cache)}) does not have the expected "
                f"'write' method. Proceeding without writing to cache for this request: {url}."
            )

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()

            html_text = response.text

            if can_write_cache and html_text:
                try:
                    cache_file_name = self._generate_cache_name_from_url(url)
                    artifact_cache_name = os.path.join("artifacts", cache_file_name)

                    logger.info(
                        f"Writing fetched HTML for {url} to cache as: {artifact_cache_name}"
                    )
                    self.cache.write(artifact_cache_name, html_text)
                except Exception as e:
                    logger.error(f"Error writing HTML for {url} to cache: {e}")

            return html_text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching URL {url}: {e}")
            return None

    def _debug_save_html(self, url: str, html_content: str):
        site_name_for_file = (
            self._extract_site_name_internal(url) if self.base_url else "unknown_site"
        )
        debug_html_dir = "debug_html_direct_save"
        if not os.path.exists(debug_html_dir):
            os.makedirs(debug_html_dir, exist_ok=True)
        safe_site_name = re.sub(r"[^\w\-_\.]", "_", site_name_for_file)
        filename = os.path.join(
            debug_html_dir,
            f"{safe_site_name}_raw_{self.__class__.__name__}_{datetime.now().strftime('%Y%m%d%H%M%S')}.html",
        )
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"Saved direct debug HTML to {filename}")
        except IOError as e:
            logger.error(f"Failed to save direct debug HTML: {e}")

    def _make_absolute_url(self, link_url: str | None) -> str | None:
        if not link_url or not self.base_url:
            return None
        if isinstance(link_url, str) and link_url.startswith(("http://", "https://")):
            return link_url
        try:
            return urljoin(self.base_url, link_url)
        except ValueError:
            logger.warning(
                f"Could not make absolute URL from base '{self.base_url}' and link '{link_url}'"
            )
            return link_url

    def _extract_site_name_internal(self, url: str) -> str:
        parsed_url = urlparse(url)
        domain_parts = parsed_url.netloc.split(".")
        if "granicus" in domain_parts:
            try:
                granicus_index = domain_parts.index("granicus")
                if granicus_index > 0:
                    return domain_parts[granicus_index - 1]
            except ValueError:
                pass
        if (
            len(domain_parts) > 1
            and domain_parts[-2] == "granicus"
            and domain_parts[-1] in ["com", "org", "us", "gov", "ca", "gov.uk", "net"]
        ):
            return domain_parts[0]
        return parsed_url.netloc.replace(".", "_")

    def _normalize_meeting_id_component(self, name: str) -> str:
        if not name:
            return "unknown"
        name = str(name)
        name = re.sub(r"[^\w\s-]", "", name)
        name = re.sub(r"\s+", "-", name.strip())
        return name.lower()

    def _parse_date_time_to_objects(
        self, date_str: str | None, time_str: str | None
    ) -> tuple[datetime | None, dt_time | None]:
        parsed_date_obj = None
        parsed_time_obj = None

        if date_str:
            clean_date_str = date_str.replace("\xa0", " ").strip()
            clean_date_str = re.sub(r"\s*-\s*", " ", clean_date_str)
            clean_date_str = re.sub(r"\s+", " ", clean_date_str)

            if not time_str:
                time_in_date_match = re.search(
                    r"(\d{1,2}(?:[:\.]\d{2})?\s*(?:AM|PM|am|pm)?)", clean_date_str
                )
                if time_in_date_match:
                    potential_time = time_in_date_match.group(1).strip()
                    # Ensure that the matched string is a plausible time (contains ':' or AM/PM)
                    # and not just a number that could be a day of the month.
                    # Day numbers are typically 1-31, so we need stricter validation
                    has_time_separators = ":" in potential_time or "." in potential_time
                    has_ampm = re.search(r"(AM|PM)", potential_time, re.I)

                    # Additional check: if it's just a 1-2 digit number without separators or AM/PM,
                    # it's likely a day number, not a time
                    is_likely_day_number = (
                        not has_time_separators
                        and not has_ampm
                        and potential_time.isdigit()
                        and 1 <= int(potential_time) <= 31
                    )

                    # Only treat as time if it has time indicators AND is not likely a day number
                    if (has_time_separators or has_ampm) and not is_likely_day_number:
                        time_str = potential_time
                        # Only modify clean_date_str if a valid time was extracted
                        clean_date_str = clean_date_str.replace(
                            time_in_date_match.group(1), "", 1
                        ).strip()
                    # else: potential_time was likely just a day number, do not treat as time or modify clean_date_str

            try:
                import dateutil.parser

                parsed_date_obj = dateutil.parser.parse(
                    clean_date_str, ignoretz=True
                ).replace(hour=0, minute=0, second=0, microsecond=0)
            except (ValueError, ImportError, OverflowError, TypeError):
                logger.debug(
                    f"dateutil.parser failed for date '{clean_date_str}', trying manual formats."
                )
                date_formats_to_try = [
                    "%B %d, %Y",
                    "%b %d, %Y",
                    "%m/%d/%Y",
                    "%Y-%m-%d",
                    "%A, %B %d, %Y",
                    "%b. %d, %Y",
                    "%B %d %Y",
                    "%b %d %Y",
                    "%m-%d-%y",
                    "%m/%d/%y",
                ]
                for fmt in date_formats_to_try:
                    try:
                        parsed_date_obj = datetime.strptime(
                            clean_date_str, fmt
                        ).replace(hour=0, minute=0, second=0, microsecond=0)
                        break
                    except ValueError:
                        continue

            if not parsed_date_obj:
                logger.warning(
                    f"Could not parse date string: '{date_str}' (cleaned: '{clean_date_str}')"
                )
                return None, None

        if time_str:
            time_str_cleaned = time_str.replace(".", ":").replace("\xa0", " ").strip()
            time_formats_to_try = [
                "%I:%M %p",
                "%H:%M",
                "%I:%M%p",
                "%H:%M%p",
                "%I %p",
                "%H:%M:%S",
            ]
            for fmt in time_formats_to_try:
                try:
                    parsed_time_obj = datetime.strptime(
                        time_str_cleaned.upper(), fmt
                    ).time()
                    break
                except ValueError:
                    continue

            if not parsed_time_obj and time_str_cleaned:
                time_match_aggressive = re.match(
                    r"(\d{1,2})(?:[:\.]?(\d{2}))?\s*(AM|PM)?", time_str_cleaned, re.I
                )
                if time_match_aggressive:
                    hour_str, minute_str, ampm_str = time_match_aggressive.groups()
                    hour = int(hour_str)
                    minute = int(minute_str) if minute_str else 0
                    if ampm_str:
                        ampm = ampm_str.lower()
                        if ampm == "pm" and hour < 12:
                            hour += 12
                        elif ampm == "am" and hour == 12:
                            hour = 0
                    elif not ampm_str and len(hour_str) >= 3 and minute == 0:
                        if hour > 23:
                            try:
                                temp_hour = int(hour_str[:-2])
                                temp_minute = int(hour_str[-2:])
                                if 0 <= temp_hour <= 23 and 0 <= temp_minute <= 59:
                                    hour = temp_hour
                                    minute = temp_minute
                            except ValueError:
                                pass
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        parsed_time_obj = dt_time(hour, minute)

            if not parsed_time_obj:
                logger.warning(
                    f"Could not parse time string: '{time_str_cleaned}'. Defaulting time part if date is valid."
                )
        return parsed_date_obj, parsed_time_obj

    def _transform_to_asset_collection(
        self,
        extracted_items: list[dict],
        site_url: str,
        site_place: str | None,
        site_state: str | None,
        site_committee_name: str | None,
        site_timezone: str | None,
    ) -> AssetCollection:
        asset_collection = AssetCollection()
        site_identifier = (
            self._extract_site_name_internal(site_url)
            if not site_place
            else self._normalize_meeting_id_component(site_place)
        )

        for item in extracted_items:
            meeting_name_raw = item.get("name")
            raw_date_str = item.get("date")
            raw_time_str = item.get("time")

            meeting_date_obj, meeting_time_obj = self._parse_date_time_to_objects(
                raw_date_str, raw_time_str
            )

            # --- Fallback Recovery Logic ---
            # Some Granicus Type1 tables (and possibly others) have column shifts where
            # the scraped 'date' field actually contains an asset label like 'Agenda'
            # and the meeting date appears in the 'name' field (e.g. name='September 2, 2025', date='Agenda').
            # If the primary parse failed BUT the name looks like a date, attempt to recover.
            if meeting_name_raw and (meeting_date_obj is None) and raw_date_str:
                probable_asset_label = str(raw_date_str).strip().lower()
                # Common non-date tokens that indicate the date column was mis-read
                non_date_tokens = {"agenda", "minutes", "video", "packet", "agenda packet", "agendapacket"}
                # Heuristic: only attempt if raw_date_str is a known non-date token OR contains no digits
                if (probable_asset_label in non_date_tokens) or not any(ch.isdigit() for ch in probable_asset_label):
                    alt_date_obj, _ = self._parse_date_time_to_objects(meeting_name_raw, raw_time_str)
                    if alt_date_obj:
                        logger.info(
                            "Recovered meeting date from 'name' field after failing to parse 'date' field. "
                            f"Name='{meeting_name_raw}', RawDate='{raw_date_str}'"
                        )
                        meeting_date_obj = alt_date_obj
                        # Keep meeting_name_raw as-is (it's the date string). Optionally could assign a generic title.
                        # If in future we want a friendlier asset_name, we could do:
                        # meeting_name_raw = f"{site_committee_name or 'Meeting'} - {alt_date_obj.strftime('%B %d, %Y')}"

            if not meeting_name_raw or not meeting_date_obj:
                logger.warning(
                    f"Skipping item due to missing name or unparsable date: Name='{meeting_name_raw}', RawDate='{raw_date_str}'"
                )
                continue

            final_meeting_datetime = meeting_date_obj
            if meeting_time_obj:
                final_meeting_datetime = datetime.combine(
                    meeting_date_obj, meeting_time_obj
                )

            committee_for_asset = (
                site_committee_name
                if site_committee_name
                else item.get("committee", "Unknown Committee")
            )

            date_str_for_id = final_meeting_datetime.strftime("%Y-%m-%d")
            meeting_id_source_component = self._normalize_meeting_id_component(
                item.get("meeting_id_source", "")
            )

            norm_committee = self._normalize_meeting_id_component(committee_for_asset)
            norm_meeting_name = self._normalize_meeting_id_component(meeting_name_raw)

            if meeting_id_source_component and meeting_id_source_component != "unknown":
                meeting_id_str = f"granicus-{site_identifier}-{norm_committee}-{date_str_for_id}-{meeting_id_source_component}"
            else:
                meeting_id_str = f"granicus-{site_identifier}-{norm_committee}-{date_str_for_id}-{norm_meeting_name}"

            asset_type_to_url_key_map = {
                "agenda": item.get("agenda_url"),
                "minutes": item.get("minutes_url"),
                "video": item.get("video_url"),
                "agenda_packet": item.get("packet_url"),
            }

            for asset_type_key, asset_url_raw in asset_type_to_url_key_map.items():
                if asset_url_raw:
                    # Ignore placeholder javascript void links (not real downloadable/streaming assets)
                    if isinstance(asset_url_raw, str) and asset_url_raw.lower().startswith('javascript:void'):
                        continue
                    absolute_asset_url = self._make_absolute_url(asset_url_raw)
                    if not absolute_asset_url:
                        logger.warning(
                            f"Could not make absolute URL for {asset_type_key} of meeting '{meeting_name_raw}'. Raw URL: {asset_url_raw}"
                        )
                        continue

                    try:
                        asset = Asset(
                            url=absolute_asset_url,
                            asset_name=meeting_name_raw,
                            committee_name=committee_for_asset,
                            place=site_place,
                            state_or_province=site_state,
                            asset_type=asset_type_key,
                            meeting_date=final_meeting_datetime,
                            meeting_time=meeting_time_obj,
                            meeting_id=meeting_id_str,
                            scraped_by=f"civic-scraper-granicus-{CIVIC_SCRAPER_VERSION}",
                            content_type=None,
                            content_length=None,
                        )
                        asset_collection.append(asset)  # Changed from add to append
                    except Exception as e:
                        logger.error(
                            f"Error creating Asset object for {asset_type_key} of meeting '{meeting_name_raw}': {e}",
                            exc_info=True,
                        )

        return asset_collection

    @abstractmethod
    def _extract_meeting_details_internal(
        self, soup: BeautifulSoup, panel_name: str | None
    ) -> list[dict]:
        pass

    def extract_and_process_meetings(
        self,
        html_content: str,
        site_url: str,
        site_place: str | None,
        site_state: str | None,
        site_committee_name: str | None,
        site_timezone: str | None,
    ) -> AssetCollection:
        self.base_url = site_url
        soup = BeautifulSoup(html_content, "html.parser")

        try:
            logger.info(
                f"Attempting extraction with {self.__class__.__name__} for panel: {site_committee_name if site_committee_name else 'N/A'}"
            )
            raw_meetings = self._extract_meeting_details_internal(
                soup, site_committee_name
            )

            if not raw_meetings:
                logger.info(
                    f"{self.__class__.__name__} found no raw meeting data for panel: {site_committee_name if site_committee_name else 'N/A'}."
                )
                return AssetCollection()

            logger.info(
                f"{self.__class__.__name__} extracted {len(raw_meetings)} raw meeting items."
            )

            asset_collection = self._transform_to_asset_collection(
                raw_meetings,
                site_url,
                site_place,
                site_state,
                site_committee_name,
                site_timezone,
            )

            logger.info(
                f"{self.__class__.__name__} processed data into {len(asset_collection)} assets."
            )
            return asset_collection
        except Exception as e:
            logger.error(
                f"Error during extraction/processing with {self.__class__.__name__}: {e}",
                exc_info=True,
            )
            return AssetCollection()

    def requires_panel_name(self) -> bool:
        return True
