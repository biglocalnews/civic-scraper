"""
BoardDocs exporter implementation for civic-scraper.
"""
import csv
import os
from typing import List, Dict, Any


class BoardDocsExporter:
    """Exports BoardDocs meeting data to CSV file"""

    def __init__(self, state_or_province: str, place: str):
        """
        Initialize the CSV exporter.

        Args:
            state_or_province: State or province abbreviation (e.g., 'pa')
            place: Municipality abbreviation (e.g., 'stco')
        """
        self.state_or_province = state_or_province
        self.place = place

    def save_meetings_to_csv(self, meetings: List[Dict[str, Any]], target_year: str, output_dir: str = None) -> str:
        """
        Save meetings data to a CSV file for the specified year.

        Args:
            meetings: List of meeting dictionaries
            target_year: Year to filter meetings by
            output_dir: Optional directory to save file (defaults to './output_data')

        Returns:
            Path to the created CSV file
        """
        # Create output directory if it doesn't exist
        if not output_dir:
            # Get the directory of the current file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Construct the output directory relative to the script directory
            output_dir = os.path.join(script_dir, '..', '..', '..', 'output_data')

        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Construct filename based on state and place values
        filename = f'{self.state_or_province}_{self.place}_board_{target_year}.csv'
        filepath = os.path.join(output_dir, filename)

        with open(filepath, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            # Write header row
            writer.writerow(['asset_name', 'date', 'date (Formatted)', 'year', 'month', 'unique_id',
                             'place', 'state_province', 'asset_type', 'agenda_content', 'minutes_content'])

            # Write data rows - filter for target year
            for meeting in meetings:
                if meeting.get('year') == target_year:
                    writer.writerow([
                        meeting.get('name', ''),
                        meeting.get('numberdate', ''),
                        meeting.get('date_formatted', ''),
                        meeting.get('year', ''),
                        meeting.get('month', ''),
                        meeting.get('unique', ''),
                        meeting.get('place', ''),
                        meeting.get('state_province', ''),
                        meeting.get('asset_type', 'meeting'),
                        meeting.get('agenda_content', ''),
                        meeting.get('minutes_content', '')
                    ])

        return filepath
