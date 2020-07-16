"""
TITLE: asset.py
AUTHOR: Chris Stock & Amy DiPierro
VERSION: 2020-07-16
DESCRIPTION: Defines the Asset and AssetList classes.

Asset:
    Attributes:
        url: str, the URL to download an asset. Ex: http://ca-eastpaloalto.civicplus.com/AgendaCenter
        asset_name: str, the title of an asset. Ex: City Council Special Budget Meeting - April 4, 2020
        committee_name: str, the name of the committee that generated the asset. Ex: City Council
        place: str, the name of the place associated with the asset in lowercase with spaces and punctuation removed. Ex: eastpaloalto
        state_or_province: str, the two-letter abbreviation for the state or province associated with an asset. Ex: ca
        asset_type: str, one of the following strings: 'agenda', 'minutes', 'audio', 'video', 'video2', 'agenda_packet', 'captions'
        meeting_date: datetime.date corresponding to the time the meeting was held or today if no date given
        meeting_time: datetime.time corresponding to the time the meetings was held or midnight if no time given
        meeting_id: #TODO: Decide the spec for this.
        scraped_by: str, describes the module and version that produced the asset. Ex: 'civicplus.py_2020-07-16'
        content_type: str, the file type of the asset as given by HTTP headers. Ex: 'application/pdf'
        content_length: str, the size of the asset in bytes

    Public methods:
        download: downloads an asset to a given target_path
        append_metadata: writes a new line to a csv containing metadata about a given asset

AssetList:
    Attributes:
        asset_args: dict, a dictionary containing metadata corresponding to the attributes of an Asset object.

    Public methods:
        download_assets: a wrapper around Asset.download, it downloads each asset instance in an AssetList
        to_csv: a wrapper around append_metadata, it writes out a csv containing metadata about each asset instance
                in an AssetList


From Python (example):

    from civic_scraper.scrapers import SUPPORTED_SCRAPERS

    cp = SUPPORTED_SCRAPERS['civicplus'] # Or choose another supported scraper
    site = cp(base_url="https://ca-eastpaloalto.civicplus.com/AgendaCenter") # Or choose another url
    metadata = site.scrape("20200101", "20200501", file_size=200, type_list=['Minutes']) # Choose start_date, end_date, file_size and type_list
    metadata.download_assets(target_dir="test") # Downloads assets to the directory "test"
    metadata.to_csv("test.csv") # Downloads csv titled "test.csv"

"""

import datetime
import csv
import os
import requests
import re
from collections import OrderedDict

class Asset(object):

    def __init__(
            self,
            url: str,
            asset_name: str = None,
            committee_name: str = None,
            place: str = None,
            state_or_province: str = None,
            asset_type: str = None,
            meeting_date: datetime.date = None,
            meeting_time: datetime.time = None,
            meeting_id: str = None,
            scraped_by: str = None,
            content_type: str = None,
            content_length: str = None
    ):
        """
        Create an instance of the Asset class.
        """
        url_valid = False
        while not url_valid:
            if (url.find("http://") and url.find("https://")) != -1:
                url_valid = True
            else:
                print("URL must start with 'http://' or 'https://'")
                break

        state_or_province_valid = False
        while not state_or_province_valid:
            if len(state_or_province) == 2 and state_or_province.isalpha():
                state_or_province_valid = True
            else:
                print("State or province abbreviation must be exactly two letters.")
                break

        asset_type_valid = False
        asset_type_list = ['agenda', 'minutes', 'video', 'audio', 'captions', 'agenda_packet']
        while not asset_type_valid:
            if asset_type in asset_type_list:
                asset_type_valid = True
            else:
                print("The asset_type is: ", asset_type)
                print("The value of asset_type must be one of the following: 'agenda', 'minutes', 'video', 'audio', 'captions', 'agenda_packet'.")
                break

        meeting_date_valid = False
        while not meeting_date_valid:
            if type(meeting_date) == datetime.date:
                meeting_date_valid = True
            else:
                print("The meeting_date is: ", meeting_date)
                print("The value of meeting_date must be an object of class datetime.date.")
                break

        meeting_time_valid = False
        while not meeting_time_valid:
            if type(meeting_time) == datetime.time:
                meeting_time_valid = True
            else:
                print("The value of meeting_time must be an object of class datetime.time.")
                break

        meeting_id_valid = False
        while not meeting_id_valid:
            if meeting_id == url:
                meeting_id_valid = True
            else:
                print("The meeting_id must equal the URL.")
                break

        scraped_by_valid = False
        while not scraped_by_valid:
            if re.match(r".+\.py_v\d{4}-\d{2}-\d{2}", scraped_by) != None:
                scraped_by_valid = True
            else:
                print("The format of scraped_by should be 'module.py_vYYYY-MM-DD'.")
                break

        valid_list = [url_valid, state_or_province_valid, asset_type_valid, meeting_date_valid, meeting_time_valid, meeting_id_valid, scraped_by_valid]

        if False in valid_list:
            print("Cannot initialize Asset object. Invalid input.")

        else:
            self.url = url
            self.asset_name = asset_name
            self.committee_name = committee_name
            self.place = place
            self.state_or_province = state_or_province
            self.asset_type = asset_type
            self.meeting_date = meeting_date
            self.meeting_time = meeting_time
            self.meeting_id = meeting_id
            self.scraped_by = scraped_by
            self.content_type = content_type
            self.content_length = content_length

    def download(self, target_path=os.getcwd()):
        """
        Downloads a asset into a target directory.

        Input: Target directory name (target_path)
        Output: pdf of asset in target directory
        """
        file_name = "{}_{}_{}_{}.pdf".format(self.place, self.state_or_province, self.asset_type, self.meeting_date)
        asset = self.url
        print("Downloading asset: ", asset)
        response = requests.get(asset, allow_redirects=True)
        if not os.path.isdir(target_path):
            print("Making directory...")
            os.mkdir(target_path)
        full_path = os.path.join(target_path, file_name)

        with open(full_path, 'wb') as file:
            file.write(response.content)

    def append_metadata(self, target_path=os.getcwd(), write_header=False):
        """
        Append the asset metadata in CSV format to target_path.
        If write_header is True, first write a line containing the header
        names. If false, only write one line containing the values.
        """
        # Make the dictionary
        metadata_dict = OrderedDict([
            ('place', self.place),
            ('state_or_province', self.state_or_province),
            ('meeting_date', self.meeting_date),
            ('meeting_time', self.meeting_time),
            ('committee_name', self.committee_name),
            ('meeting_id', self.meeting_id),
            ('asset_type', self.asset_type),
            ('url', self.url),
            ('scraped_by', self.scraped_by),
            ('content_type', self.content_type),
            ('content_length', self.content_length),
        ])

        # Initializing the .csv
        if target_path.find(".csv") == -1:
            file_name = "{}-{}.csv".format(self.place, self.state_or_province)
            full_path = os.path.join(target_path, file_name)
        else:
            full_path = target_path

        file = open(full_path, 'a')

        # Writing the .csv
        with file:
            dict_writer = csv.DictWriter(file, metadata_dict.keys())
            if write_header:
                dict_writer.writeheader()
            if self.url is not None:
                dict_writer.writerow(metadata_dict)


class AssetList(object):

    def __init__(self, asset_args):
        """
        Initialize the AssetList
        """
        # Store the list of asset metadata dictionaries
        self.asset_args = asset_args

        # Make a list of Asset instances
        self.assets = [Asset(**args) for args in asset_args]

    def download_assets(self, target_dir=os.getcwd()):
        """
        Write assets to target_path.
        """
        for item in self.assets:
            item.download(target_dir)

    def to_csv(self, target_path=os.getcwd()):
        """
        Write metadata about the asset list to a csv at target_path.
        """
        for index, value in enumerate(self.assets):
            if os.path.exists(target_path):
                value.append_metadata(target_path)
            else:
                value.append_metadata(target_path, write_header=True)


if __name__ == '__main__':

    from civic_scraper.scrapers import SUPPORTED_SCRAPERS

    cp = SUPPORTED_SCRAPERS['civicplus']
    site = cp(base_url="https://ca-eastpaloalto.civicplus.com/AgendaCenter")
    metadata = site.scrape("20200101", "20200501", type_list=['Minutes'])

    # metadata.download_assets(target_dir="test.pdf")
    metadata.to_csv("test.csv")

