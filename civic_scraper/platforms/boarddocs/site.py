"""
BoardDocs platform implementation for civic-scraper.
"""
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime

from civic_scraper.base.site import Site as BaseSite
from civic_scraper.platforms.boarddocs.parser import BoardDocsParser


class BoardDocsSite(BaseSite):
    """
    BoardDocs platform implementation for scraping meeting data.
    """

    def __init__(self, url: str, **kwargs):
        """
        Initialize BoardDocs site with URL and optional parameters.

        Args:
            url: BoardDocs site URL
            **kwargs: Additional parameters including:
                - committee_id: Optional committee ID, will be auto-detected if not provided
                - start_date: Optional start date for meeting search
                - end_date: Optional end date for meeting search
        """
        self.url = self._normalize_url(url)
        self.committee_id = kwargs.get('committee_id')
        self.start_date = kwargs.get('start_date')
        self.end_date = kwargs.get('end_date')
        self.session = requests.Session()
        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'civic-scraper/1.0'
        }
        self.parser = BoardDocsParser()

        # Get the state and place from URL
        url_pattern = re.compile(r'https://go\.boarddocs\.com/([^/]+)/([^/]+)/Board\.nsf')
        match = url_pattern.match(self.url)

        if match:
            self.state_or_province = match.group(1)
            self.place = match.group(2)
        else:
            self.state_or_province = ""
            self.place = ""

        # Auto-detect committee_id if not provided
        if not self.committee_id:
            self.committee_id = self._get_committee_id()

    def _normalize_url(self, url: str) -> str:
        """
        Normalize a BoardDocs URL to ensure it has the correct format.
        The expected URL structure is https://go.boarddocs.com/pa/keyc/Board.nsf

        Args:
            url: The input BoardDocs URL

        Returns:
            The normalized URL with proper structure
        """
        # Remove trailing slash if present
        url = url.rstrip('/')

        # Remove '/Public' if present at the end
        if url.endswith('/Public'):
            url = url[:-7]  # Remove '/Public'

        # Ensure URL has http/https prefix
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # Make sure URL ends with 'Board.nsf'
        if not url.endswith('Board.nsf'):
            parts = url.split('Board.nsf')
            if len(parts) > 1:
                # URL has 'Board.nsf' but something after it
                url = parts[0] + 'Board.nsf'

        return url

    def _get_committee_id(self) -> Optional[str]:
        """
        Extract committee_id from the BoardDocs site.

        Returns:
            The extracted committee_id or None if extraction fails
        """
        # Construct the public BoardDocs page URL from the API base URL
        url = self.url.split("/Board.nsf")[0] + "/Board.nsf/Public#"
        committee_id = None

        try:
            response = self.session.get(url)
            response.raise_for_status()
            html_content = response.text

            soup = BeautifulSoup(html_content, 'html.parser')

            # Find the <select> element with name="committeeid"
            select_element = soup.find('select', {'name': 'committeeid'})

            if select_element:
                # Find the first <option> tag within the <select>
                option_element = select_element.find('option')
                if option_element:
                    committee_id = option_element.get('value')

        except Exception as e:
            self.logger.error(f"Error extracting committee ID: {e}")

        return committee_id

    def get_meetings(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Get list of meetings from the BoardDocs platform.

        Args:
            **kwargs: Optional parameters to override instance attributes
                - committee_id: Committee ID to use for this request
                - start_date: Start date for filtering meetings
                - end_date: End date for filtering meetings

        Returns:
            List of meeting dictionaries with metadata
        """
        committee_id = kwargs.get('committee_id', self.committee_id)
        start_date = kwargs.get('start_date', self.start_date)
        end_date = kwargs.get('end_date', self.end_date)

        meetings_data = self._get_meetings_list(committee_id)
        processed_meetings = []

        for meeting_data in meetings_data:
            # Skip if not within date range
            meeting_date = meeting_data.get('numberdate', '')
            if not self._is_in_date_range(meeting_date, start_date, end_date):
                continue

            # Process meeting data
            processed_meeting = self._process_meeting(meeting_data, committee_id)
            if processed_meeting:
                processed_meetings.append(processed_meeting)

        return processed_meetings

    def _get_meetings_list(self, committee_id: str) -> List[Dict[str, Any]]:
        """
        Fetch list of meetings for the specified committee.

        Args:
            committee_id: ID of the committee to fetch meetings for

        Returns:
            List of meeting data dictionaries
        """
        endpoint = f"{self.url}/BD-GetMeetingsList?open"
        data = {'current_committee_id': committee_id}

        try:
            response = self.session.post(endpoint, headers=self.headers, data=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching meetings: {e}")
            return []

    def _is_in_date_range(self, date_str: str, start_date: Optional[str], end_date: Optional[str]) -> bool:
        """
        Check if a date is within the specified range.

        Args:
            date_str: Date string in YYYYMMDD format
            start_date: Start date string in YYYY-MM-DD format (inclusive)
            end_date: End date string in YYYY-MM-DD format (inclusive)

        Returns:
            True if date is within range or no range specified, False otherwise
        """
        if not date_str:
            return False

        try:
            date_obj = datetime.strptime(date_str, "%Y%m%d")

            if start_date:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
                if date_obj < start_date_obj:
                    return False

            if end_date:
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
                if date_obj > end_date_obj:
                    return False

            return True
        except ValueError:
            return False

    def _process_meeting(self, meeting_data: Dict[str, Any], committee_id: str) -> Optional[Dict[str, Any]]:
        """
        Process a single meeting to extract agenda and minutes.

        Args:
            meeting_data: Raw meeting data from API
            committee_id: Committee ID for fetching minutes

        Returns:
            Processed meeting dictionary or None if processing fails
        """
        # Extract basic meeting info
        meeting_id = meeting_data.get('unique', '')
        if not meeting_id:
            return None

        # Format date information
        date_number = meeting_data.get('numberdate', '')
        date_formatted = ''
        year = ''
        month = ''

        if date_number:
            try:
                date_obj = datetime.strptime(date_number, "%Y%m%d")
                date_formatted = date_obj.strftime("%B %d, %Y")
                year = date_obj.strftime("%Y")
                month = date_obj.strftime("%m")
            except ValueError:
                pass

        # Fetch agenda content
        agenda_html = self._get_agenda(meeting_id)
        agenda_content = ""
        if agenda_html:
            try:
                structured_agenda = self.parser.parse_agenda_html(agenda_html)
                agenda_content = self.parser.format_structured_agenda(structured_agenda)
            except Exception as e:
                self.logger.error(f"Error parsing agenda: {e}")
                agenda_content = "Failed to parse agenda."

        # Fetch minutes content
        minutes_html = self._get_minutes(meeting_id, committee_id)
        minutes_content = ""
        if minutes_html:
            try:
                minutes_content = self.parser.parse_minutes_content(minutes_html)
            except Exception as e:
                self.logger.error(f"Error parsing minutes: {e}")
                minutes_content = "Failed to parse minutes."

        # Build result dictionary
        processed_meeting = {
            'name': meeting_data.get('name', ''),
            'numberdate': date_number,
            'date_formatted': date_formatted,
            'year': year,
            'month': month,
            'unique': meeting_id,
            'place': self.place,
            'state_province': self.state_or_province,
            'asset_type': 'meeting',
            'agenda_content': agenda_content,
            'minutes_content': minutes_content
        }

        return processed_meeting

    def _get_agenda(self, meeting_id: str) -> Optional[str]:
        """
        Fetch meeting agenda for a given meeting ID.

        Args:
            meeting_id: Unique meeting identifier

        Returns:
            Agenda HTML content or None if fetch fails
        """
        endpoint = f"{self.url}/BD-GetAgenda?open"
        data = {'id': meeting_id}

        try:
            response = self.session.post(endpoint, headers=self.headers, data=data)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.error(f"Error fetching agenda for meeting ID {meeting_id}: {e}")
            return None

    def _get_minutes(self, meeting_id: str, committee_id: str) -> Optional[str]:
        """
        Fetch meeting minutes for a given meeting ID.

        Args:
            meeting_id: Unique meeting identifier
            committee_id: Committee ID required for minutes fetch

        Returns:
            Minutes HTML content or None if fetch fails
        """
        endpoint = f"{self.url}/BD-GetMinutes?open"
        data = {
            'id': meeting_id,
            'current_committee_id': committee_id
        }

        try:
            response = self.session.post(endpoint, headers=self.headers, data=data)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.error(f"Error fetching minutes for meeting ID {meeting_id}: {e}")
            return None

    def get_meeting_details(self, meeting_id: str, **kwargs) -> Dict[str, Any]:
        """
        Get detailed information for a specific meeting.

        Args:
            meeting_id: Unique meeting identifier
            **kwargs: Optional parameters
                - committee_id: Committee ID to use for this request

        Returns:
            Dictionary with meeting details
        """
        committee_id = kwargs.get('committee_id', self.committee_id)

        # Fetch agenda and minutes
        agenda_html = self._get_agenda(meeting_id)
        minutes_html = self._get_minutes(meeting_id, committee_id)

        # Parse content
        agenda_content = ""
        if agenda_html:
            try:
                structured_agenda = self.parser.parse_agenda_html(agenda_html)
                agenda_content = self.parser.format_structured_agenda(structured_agenda)
            except Exception as e:
                self.logger.error(f"Error parsing agenda: {e}")

        minutes_content = ""
        if minutes_html:
            try:
                minutes_content = self.parser.parse_minutes_content(minutes_html)
            except Exception as e:
                self.logger.error(f"Error parsing minutes: {e}")

        # Return meeting details
        return {
            'unique': meeting_id,
            'agenda_content': agenda_content,
            'minutes_content': minutes_content,
            'raw_agenda': agenda_html,
            'raw_minutes': minutes_html
        }

    def get_committees(self) -> List[Dict[str, Any]]:
        """
        Get list of available committees from the BoardDocs site.

        Returns:
            List of committee dictionaries with id and name
        """
        committees_url = f"{self.url}/BD-GetCommittees"

        try:
            response = self.session.post(committees_url)
            if response.status_code == 200:
                # Try to parse as JSON
                try:
                    return response.json()
                except ValueError:
                    # If not JSON, parse as HTML
                    soup = BeautifulSoup(response.text, 'html.parser')
                    committees = []
                    for option in soup.select('option'):
                        committee_id = option.get('value')
                        committee_name = option.text.strip()
                        if committee_id:
                            committees.append({'id': committee_id, 'name': committee_name})
                    return committees
        except Exception as e:
            self.logger.error(f"Error fetching committees: {e}")

        return []
