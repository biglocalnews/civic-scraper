"""
Constant definitions for the civic-scraper library.
"""

# Standard asset types across all platforms
ASSET_TYPES = [
    "agenda",
    "minutes",
    "video",
    "audio",
    "packet",
    "attachment",
    "summary",
    "transcript",
]

# Mapping of platform-specific asset types to standard types
ASSET_TYPE_MAPPINGS = {
    "legistar": {
        "agenda": "agenda",
        "minutes": "minutes",
        "Agenda": "agenda",
        "Minutes": "minutes",
    },
    "civic_plus": {
        "Agenda": "agenda",
        "Minutes": "minutes",
        "Agenda Packet": "packet",
        "Video": "video",
        "Audio": "audio",
        "Summary": "summary",
    },
    "granicus": {
        "Agenda": "agenda",
        "Minutes": "minutes",
        "Video": "video",
    },
    "boarddocs": {
        "meeting_meta_link": "agenda",
    },
}

# Default timeout for HTTP requests (in seconds)
REQUEST_TIMEOUT = 30

# Standard date format for all platforms
DATE_FORMAT = "%Y-%m-%d"

# Identifier for the scraper
SCRAPED_BY = "civic-scraper"
