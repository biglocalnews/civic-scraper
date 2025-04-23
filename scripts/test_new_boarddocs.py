import sys
import os
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from civic_scraper.platforms.boarddocs.site import BoardDocsSite
import json

# Assuming assets.py is in the same directory or importable

boarddocs_url = "https://go.boarddocs.com/pa/stco/board.nsf/Public"
scraper = BoardDocsSite(boarddocs_url)

# Scrape meetings using the new scrape function
assets = scraper.scrape()

# Convert the AssetCollection to a list of dictionaries for JSON output
output_data = [asset.__dict__ for asset in assets]
print(json.dumps(output_data, indent=4))

# Optional: You can also test with date ranges
# start_date_str = "2024-01-01"
# end_date_str = "2024-12-31"
# assets_with_dates = scraper.scrape(start_date=start_date_str, end_date=end_date_str)
# output_data_with_dates = [asset.__dict__ for asset in assets_with_dates]
# print("\nMeetings within date range:")
# print(json.dumps(output_data_with_dates, indent=4))