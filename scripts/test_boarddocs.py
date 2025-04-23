#!/usr/bin/env python
"""
Command-line script to scrape BoardDocs meetings.
"""
import sys
import os
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from civic_scraper.platforms.boarddocs.site import BoardDocsSite
from civic_scraper.platforms.boarddocs.exporter import BoardDocsExporter


def main():
    """Main entry point for the BoardDocs scraper"""
    # Direct assignment of values instead of using argparse
    # url = 'https://go.boarddocs.com/pa/stco/Board.nsf'
    url = "https://go.boarddocs.com/nc/dpsnc/Board.nsf"
    year = '2025'
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
    
    # Create BoardDocs site instance without committee_id
    site = BoardDocsSite(url)
    
    print(f"Scraping meetings from {site.url}")
    
    # Get available committees
    committee = site._get_committee_id()

    if not committee:
        print("No committees found. Exiting.")
        return
    
    print(f"Selected committee: {committee}")
    print(f"Target year: {year}")
    
    # Get all meetings using the selected committee_id
    meetings = site.get_meetings(committee_id=committee)
    
    # Filter meetings for target year
    target_meetings = [m for m in meetings if m.get('year') == year]
    
    print(f"Found {len(target_meetings)} meetings for {year}")
    
    # Export to CSV if meetings found
    if target_meetings:
        exporter = BoardDocsExporter(site.state_or_province, site.place)
        csv_path = exporter.save_meetings_to_csv(target_meetings, year, output_dir)
        print(f"Meeting data saved to {csv_path}")
    else:
        print(f"No meetings found for {year}")


if __name__ == "__main__":
    main()