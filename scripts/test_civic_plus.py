import sys
import os
from datetime import datetime
import json

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from civic_scraper.platforms.civic_plus.site import Site as CivicPlusSite

# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Example CivicPlus URL
civic_plus_url = "http://nc-nashcounty.civicplus.com/AgendaCenter"
# civic_plus_url = "https://www.collegetownship.org/AgendaCenter"

# Below URL's not working current module
# civic_plus_url ="https://www.twp.ferguson.pa.us/minutes-and-agendas-portal"
# civic_plus_url = "https://twp.patton.pa.us/AgendaCenter/Planning-Commission-6"

scraper = CivicPlusSite(civic_plus_url)

# Scrape meetings using the scrape function with a date range
start_date_str = "2023-01-01"
end_date_str = "2023-12-31" 
assets = scraper.scrape(start_date=start_date_str, end_date=end_date_str)

# Convert the AssetCollection to a list of dictionaries for JSON output
output_data = [asset.__dict__ for asset in assets]
print(json.dumps(output_data, indent=4, cls=DateTimeEncoder))

# Optional: You can also test with cache and download options
# assets_with_options = scraper.scrape(start_date=start_date_str, end_date=end_date_str, 
#                                     cache=True, download=True, file_size=10)
# output_data_with_options = [asset.__dict__ for asset in assets_with_options]
# print("\nMeetings with additional options:")
# print(json.dumps(output_data_with_options, indent=4, cls=DateTimeEncoder))