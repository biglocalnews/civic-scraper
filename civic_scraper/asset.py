"""
TITLE: asset.py
AUTHOR: Chris Stock & Amy DiPierro
VERSION: 2020-08-26
DESCRIPTION: Defines the Asset and AssetList classes.

Asset:
    Attributes:
        url: str, the URL to download an asset. Ex: https://ca-eastpaloalto.civicplus.com/AgendaCenter/ViewFile/Agenda/_04282020-1613
        asset_name: str, the title of an asset. Ex: City Council Special Budget Meeting - April 4, 2020
        committee_name: str, the name of the committee that generated the asset. Ex: City Council
        place: str, the name of the place associated with the asset in lowercase with spaces and punctuation removed. Ex: eastpaloalto
        state_or_province: str, the two-letter abbreviation for the state or province associated with an asset. Ex: ca
        asset_type: str, one of the following strings: 'agenda', 'minutes', 'audio', 'video', 'agenda_packet', 'captions'
        meeting_date: datetime.date corresponding to the time the meeting was held or today if no date given
        meeting_time: datetime.time corresponding to the time the meetings was held or midnight if no time given
        meeting_id: str, the name of the platform being scraped, state_or_province and place
                    followed by the unique meeting ID the platform assigned to the meeting
                    Ex: civicplus_ca_eastpaloalto_01272020-1589
        scraped_by: str, describes the module and version that produced the asset. Ex: 'civicplus.py_1.0.0'
        content_type: str, the file type of the asset as given by HTTP headers. Ex: 'application/pdf'
        content_length: str, the size of the asset in bytes

    Public methods:
        download: downloads an asset to a given target_path
        append_to_csv: writes a new line to a csv containing metadata about a given asset

AssetList:
    Attributes:
        asset_args: dict, a dictionary containing metadata corresponding to the attributes of an Asset object.

    Public methods:
        download_assets: a wrapper around Asset.download, it downloads each asset instance in an AssetList
        to_csv: a wrapper around append_to_csv, it writes out a csv containing metadata about each asset instance
                in an AssetList


From Python (example):

    from civic_scraper.scrapers import SUPPORTED_SCRAPERS

    cp = SUPPORTED_SITES['civicplus'] # Or choose another supported scraper
    site = cp(base_url="https://ca-eastpaloalto.civicplus.com/AgendaCenter") # Or choose another url
    metadata = site.scrape("2020-01-01", "2020-05-01") # Optional: Choose start_date, end_date and other parameters
    metadata.download(target_dir="test") # Downloads assets to the directory "test". Can also choose optional file_size and file_type
    metadata.to_csv(target_path="test.csv") # Downloads csv titled "test.csv"

"""

# Libraries
import csv
import os
import requests
import re
from collections import OrderedDict
import datetime
import logging
import sys

# Parameters
SUPPORTED_ASSET_TYPES = ['agenda', 'minutes', 'audio', 'video', 'agenda_packet', 'captions']

# Logging
module_logger = logging.getLogger('civic_scraper.asset')


# Code

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
        self.logger = logging.getLogger('civic_scraper.asset.Asset')
        self.logger.info('creating an instance of Asset')
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
        while not asset_type_valid:
            if asset_type in SUPPORTED_ASSET_TYPES:
                asset_type_valid = True
            else:
                print("The asset_type is: ", asset_type)
                print("The value of asset_type must be one of the following: ", SUPPORTED_ASSET_TYPES)
                break

        scraped_by_valid = False
        while not scraped_by_valid:
            if re.match(r".+\.py_v\d{4}-\d{2}-\d{2}", scraped_by) != None:
                scraped_by_valid = True
            else:
                print("The format of scraped_by should be 'module.py_vYYYY-MM-DD'.")
                break

        valid_list = [url_valid, state_or_province_valid, asset_type_valid, scraped_by_valid]

        if False in valid_list:
            print("Cannot initialize Asset object. Invalid input.")
            sys.exit()

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

    def download(self, target_dir=os.getcwd(), file_size=None, asset_list=SUPPORTED_ASSET_TYPES):
        """
       Downloads an asset into a target directory.

        Input:
            target_dir: str, target directory name. Default is the current working directory.
            file_size: int, size of file in megabytes. Default is None.
            asset_type: list of strings, one or more possible asset types to download. Default is all asset types.
        Output: asset in target directory
        Returns: Full path to downloaded file
       """
        self.logger.info('downloading an instance of Asset')
        file_name = "{}_{}_{}_{}.pdf".format(self.place, self.state_or_province, self.asset_type, self.meeting_date)
        asset = self.url
        file_size = self._mb_to_bytes(file_size)

        if file_size is None and self.asset_type in asset_list:
            response = requests.get(asset, allow_redirects=True)
            if not os.path.isdir(target_dir):
                self.logger.info('Making directory for asset')
                os.mkdir(target_dir)
            full_path = os.path.join(target_dir, file_name)

            with open(full_path, 'wb') as file:
                file.write(response.content)

            self.logger.info('Asset downloaded')

            return full_path

        elif self.asset_type in asset_list and int(self.content_length) <= int(file_size):
            response = requests.get(asset, allow_redirects=True)
            if not os.path.isdir(target_dir):
                self.logger.info('Making directory for asset')
                os.mkdir(target_dir)
            full_path = os.path.join(target_dir, file_name)

            with open(full_path, 'wb') as file:
                file.write(response.content)

            self.logger.info('Asset downloaded')

            return full_path

    def append_to_csv(self, target_path, write_header=False):
        """
        Append the asset metadata in csv format to target_path.
        If write_header is True, first write a line containing the header
        names. If false, only write one line containing the values.

        Input:
            target_path: A required path for the csv
            write_header: A flag indicating whether to write the csv header or not. Default is False.

        Output: csv written to the target_path

        Returns: Nothing.
        """
        self.logger.info('appending row to csv')
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

        # Writing the .csv
        with open(target_path, 'a') as file:
            dict_writer = csv.DictWriter(file, metadata_dict.keys())
            if write_header:
                dict_writer.writeheader()
            if self.url is not None:
                dict_writer.writerow(metadata_dict)

        self.logger.info('done appending row to csv')

    def __repr__(self):
        return f'Asset(url: {self.url}, asset_name: {self.asset_name}, committee_name: {self.committee_name}, place: {self.place}, state_or_province: {self.state_or_province},  asset_type: {self.asset_type}, meeting_date: {self.meeting_date}, meeting_time: {self.meeting_time}, meeting_id: {self.meeting_id}, scraped_by: {self.scraped_by}, content_type: {self.content_type}, content_length: {self.content_length})'

    def _mb_to_bytes(self, file_size):
        """
        Converts file_size from megabytes to bytes.
        Input: File size in megabytes.
        Returns: File size in bytes.
        """

        if file_size is None:
            return None
        else:
            return int(file_size) * 1e7


class AssetCollection(object):

    def __init__(self, assets):
        """
        Initialize AssetCollection

        Input:
            assets: a list of Asset instances.
        """
        self.logger = logging.getLogger('civic_scraper.asset.AssetCollection')
        self.logger.info('creating an instance of AssetCollection')

        for asset in assets:
            assert isinstance(asset, Asset)

        self.assets = assets

    def __iter__(self):
        return iter(self.assets)

    def __next__(self):
        return next(self)

    def __len__(self):
        return len(self.assets)

    def __repr__(self):
        return f'AssetCollection({self.assets})'

    def download(self, target_dir=os.getcwd(), file_size=None,
                 asset_list=SUPPORTED_ASSET_TYPES):
        """
        Write assets to target_dir.

        Input:
            target_dir: str, the directory to which a user downloads assets.
                        Default is the current working directory.
            file_size: int, an optional parameter to limit the size of files
                        to be downloaded given in megabytes. Default is None.
            asset_list: list of strings, an optional parameter to limit the type
                        of files to be downloaded. Default is all file types.
                        Valid file types are: 'agenda', 'minutes', 'audio', 'video',
                        'agenda_packet', and 'captions'.

        Output: Downloaded assets.

        Returns: List of file paths to downloaded assets.
        """
        self.logger.info("running AssetCollection.download")

        downloaded_file_paths = []

        for item in self.assets:
            downloaded_file_path = item.download(target_dir, file_size, asset_list)
            downloaded_file_paths.append(downloaded_file_path)

        self.logger.info("done running AssetCollection.download")

        return downloaded_file_paths

    def to_csv(
            self,
            target_path=None,
            appending=False,
    ):
        """
        Write metadata about the asset list to a csv.

        Input:
            target_path: str, optional parameter giving the path to the csv to be created.
                        If target_path is given, write a file to that path.
                        If not given, create a file in the current working directory.
            appending: bool, optional flag for whether or not to overwrite an existing csv.
                        If appending is True, append to any file that's already there.
                        If appending is False, overwrite any file that's already there.

        Output: csv with metadata

        Returns: Nothing.
        """
        self.logger.info("running AssetCollection.to_csv")
        if target_path is not None:
            path = os.path.abspath(target_path)
        else:
            file_name = '-'.join([
                self.assets[0].scraped_by,
                self.assets[0].place,
                self.assets[0].state_or_province,
                datetime.datetime.utcnow().isoformat()
            ]) + '.csv'
            target_dir = os.getcwd()
            path = os.path.join(target_dir, file_name)
            path = os.path.abspath(path)

        # determine whether the file is new or already exists
        new_file = not os.path.exists(path)
        if new_file:
            containing_dir = os.path.split(path)[0]
            os.makedirs(containing_dir, exist_ok=True)
        elif not appending:
            # if appending is False, remove whatever's already there
            os.remove(path)
            new_file = True

        # write lines of data, including header if it's a new file
        for i, asset in enumerate(self.assets):
            write_header = (i == 0) and new_file
            asset.append_to_csv(path, write_header=write_header)

        self.logger.info("done running AssetCollection.to_csv")

if __name__ == '__main__':
    # The following is merely an example of how to call this code.
    import logging
    from civic_scraper.scrapers import SUPPORTED_SITES

    logger = logging.getLogger('civic_scraper')
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler('asset.log')
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    cp = SUPPORTED_SITES['civicplus']
    logger.info('creating an instance of civic_scraper.scrapers.CivicPlusSite')
    site = cp(base_url="https://ca-eastpaloalto.civicplus.com/AgendaCenter")
    logger.info('done creating an instance of civic_scraper.scrapers.CivicPlusSite')
    logger.info('calling civic_scraper.scrapers.CivicPlusSite.scrape')
    metadata = site.scrape("2020-01-01", "2020-05-01")
    logger.info('done calling civic_scraper.scrapers.CivicPlusSite.scrape')

    logger.info('downloading an instance of civic_scraper.scrapers.CivicPlusSite')
    metadata.download(target_dir="test", asset_list=['agenda'])
    logger.info('done downloading an instance of civic_scraper.scrapers.CivicPlusSite')
    logger.info('calling civic_scraper.Asset.to_csv')
    metadata.to_csv(target_path="/Users/amydipierro/GitHub/test.csv", appending=True)
    metadata.to_csv(appending=False)
    logger.info('done calling civic_scraper.Asset.to_csv')
