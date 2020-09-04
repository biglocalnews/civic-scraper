'''
TITLE: test_asset.py
AUTHOR: Amy DiPierro
VERSION: 2020-09-02
USAGE: pytest -q test_asset.py

Tests basic functionality of asset.py
'''
import os
import hashlib

from civic_scraper.scrapers import CivicPlusSite
import pytest


@pytest.mark.vcr()
def test_to_csv_defaults(tmp_path):
    "Tests the default behavior of to_csv() function in AssetCollection"

    # Make the mocker
    # mocked_asset_collection = \
    #     "AssetCollection([Asset(url: http://ks-liberal.civicplus.com/AgendaCenter/ViewFile/Agenda/_08252020-411, " \
    #     "asset_name: None, committee_name: City Commission, place: liberal, state_or_province: ks,  asset_type: " \
    #     "agenda, meeting_date: 2020-08-25, meeting_time: None, meeting_id: civicplus_ks_liberal_08252020-411, " \
    #     "scraped_by: civicplus.py_1.0.0, content_type: application/pdf, content_length: 153651), Asset(url: " \
    #     "http://ks-liberal.civicplus.com/AgendaCenter/ViewFile/Agenda/_08252020-412, asset_name: None, " \
    #     "committee_name: City Commission, place: liberal, state_or_province: ks,  asset_type: agenda, meeting_date: " \
    #     "2020-08-25, meeting_time: None, meeting_id: civicplus_ks_liberal_08252020-412, scraped_by: " \
    #     "civicplus.py_1.0.0, content_type: application/pdf, content_length: 4508590)]) "
    #
    # mocker.patch(
    #     'civic_scraper.scrapers.civicplus.CivicPlusSite.scrape',
    #     return_value=mocked_asset_collection
    # )

    # Create the temporary directory and temporary file
    directory = tmp_path / "sub"
    directory.mkdir()
    temp_csv = directory / "temp_csv_default.csv"

    # Make AssetCollection
    site_url = "http://ks-liberal.civicplus.com/AgendaCenter"
    end_date = "2020-08-26"
    start_date = "2020-08-24"
    cp = CivicPlusSite(site_url)
    asset_collection = cp.scrape(end_date=end_date, start_date=start_date)

    # Call to_csv
    asset_collection.to_csv(target_path=temp_csv)

    # Check that the content of the csv is what we'd expect
    hash_md5 = hashlib.md5()
    with open(temp_csv, 'rb') as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hash_md5.update(chunk)
    assert hash_md5.digest() == b'\x08fh*1j\xa31\x13\x824\x84B\xae\x93\xe9'

    # Check that the csv exists
    assert len(list(tmp_path.iterdir())) == 1
    assert os.path.exists(tmp_path)


@pytest.mark.vcr()
def test_append_to_csv(tmp_path):
    "Tests the behavior of to_csv() function in AssetCollection when appending=True"

    # Create the temporary directory and temporary file
    directory = tmp_path / "sub"
    directory.mkdir()
    temp_csv = directory / "temp_csv_appending.csv"

    # Make AssetCollection
    site_url = "http://ks-liberal.civicplus.com/AgendaCenter"
    end_date = "2020-08-26"
    start_date = "2020-08-24"
    cp = CivicPlusSite(site_url)
    asset_collection = cp.scrape(end_date=end_date, start_date=start_date)

    # Call to_csv
    asset_collection.to_csv(target_path=temp_csv, appending=True)

    # Check that the content of the csv is what we'd expect
    hash_md5 = hashlib.md5()
    with open(temp_csv, 'rb') as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hash_md5.update(chunk)
    assert hash_md5.digest() == b'\x08fh*1j\xa31\x13\x824\x84B\xae\x93\xe9'

    # Check that the csv exists
    assert os.path.exists(tmp_path)


@pytest.mark.vcr()
def test_append_to_csv_existing(tmp_path):
    "Tests the behavior of to_csv() function in AssetCollection when appending=True and file exists"

    # Create the first temporary directory and temporary file
    directory = tmp_path / "sub"
    directory.mkdir()
    temp_csv_1 = directory / "temp.csv"

    # Create the second temporary directory and temporary file
    temp_csv_2 = directory / "temp_csv_appending2.csv"

    # Make the first AssetCollection
    site_url = "http://ks-liberal.civicplus.com/AgendaCenter"
    start_date = "2020-07-01"
    end_date = "2020-07-30"
    cp = CivicPlusSite(site_url)
    asset_collection_1 = cp.scrape(start_date=start_date, end_date=end_date)

    # Make the second AssetCollection
    site_url = "http://ks-liberal.civicplus.com/AgendaCenter"
    start_date = "2020-08-01"
    end_date = "2020-09-03"
    cp = CivicPlusSite(site_url)
    asset_collection_2 = cp.scrape(start_date=start_date, end_date=end_date)

    # Call to_csv
    asset_collection_1.to_csv(target_path=temp_csv_1)
    asset_collection_2.to_csv(target_path=temp_csv_2)

    # Check that the content of the csv is what we'd expect
    hash_md5 = hashlib.md5()
    with open(temp_csv_2, 'rb') as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hash_md5.update(chunk)
    assert hash_md5.digest() == b'B\xee\xcc(\xc3\xee\xbe\x00m\x95iG\xd5\ne('

    # Check that the files both exist
    assert os.path.exists(temp_csv_1)
    assert os.path.exists(temp_csv_2)


@pytest.mark.vcr()
def test_download_defaults(tmp_path):
    '''
    Test default behavior of CivicPlus.download
    '''
    # Make AssetCollection
    site_url = "https://ca-napacounty.civicplus.com/AgendaCenter"
    start_date = "2020-08-24"
    end_date = "2020-09-03"
    cp = CivicPlusSite(site_url)
    asset_collection = cp.scrape(start_date=start_date, end_date=end_date)

    # Set parameters
    directory = tmp_path / "sub"
    directory.mkdir()

    # Download the assets
    asset_collection.download(target_dir=directory)

    # Check that files we expect to download get downloaded
    assert len(asset_collection) == 6
    expected_asset_hashes = []
    actual_asset_hashes = []
    for asset in os.listdir(directory):
        full_path = directory / asset
        hash_md5 = hashlib.md5()
        with open(full_path, 'rb') as file:
            for chunk in iter(lambda: file.read(4096), b""):
                hash_md5.update(chunk)
        actual_asset_hashes.append(hash_md5.digest())

    for hash in expected_asset_hashes:
        assert hash in actual_asset_hashes


@pytest.mark.vcr()
def test_download_file_size(tmp_path):
    '''
    Test behavior of CivicPlus.download with optional file_size parameter
    '''
    # Make AssetCollection
    site_url = "https://ca-napacounty.civicplus.com/AgendaCenter"
    start_date = "2020-08-24"
    end_date = "2020-09-03"
    cp = CivicPlusSite(site_url)
    asset_collection = cp.scrape(start_date=start_date, end_date=end_date)

    # Set parameters
    directory = tmp_path / "sub"
    directory.mkdir()
    file_size = 0.05

    # Download the assets
    asset_collection.download(target_dir=directory, file_size=file_size)

    # Check that files we expect to download get downloaded
    assert len(asset_collection) == 6
    expected_asset_hash = b'\xe9\x7f0\x1a\xd3s\xeb\x98\x0c\x94gb\xae\xd4\xb5\x91'
    actual_asset_hashes = []
    for asset in os.listdir(directory):
        if asset != ".DS_Store":
            full_path = '{}/{}'.format(directory, asset)
            hash_md5 = hashlib.md5()
            with open(full_path, 'rb') as file:
                for chunk in iter(lambda: file.read(4096), b""):
                    hash_md5.update(chunk)
            actual_asset_hashes.append(hash_md5.digest())
    actual_asset_hash = actual_asset_hashes[0]
    assert expected_asset_hash == actual_asset_hash

@pytest.mark.vcr()
def test_download_asset_list(tmp_path):
    '''
    Test behavior of CivicPlus.download with optional asset_list parameter
    '''
    # Make AssetCollection
    site_url = "https://ca-napacounty.civicplus.com/AgendaCenter"
    start_date = "2020-05-31"
    end_date = "2020-06-02"
    cp = CivicPlusSite(site_url)
    asset_collection = cp.scrape(start_date=start_date, end_date=end_date)

    # Set parameters
    directory = tmp_path / "sub"
    directory.mkdir()
    asset_list = ['minutes']

    # Download the assets
    asset_collection.download(target_dir=directory, asset_list=asset_list)

    # Check that files we expect to download get downloaded
    assert len(asset_collection) == 2
    expected_asset_hash = b';eJ\xfe\x8ef\xd7\x8d\x8f\xd5\x16h9c\xfa\xac'
    actual_asset_hashes = []
    for asset in os.listdir(directory):
        if asset != ".DS_Store":
            full_path = '{}/{}'.format(directory, asset)
            hash_md5 = hashlib.md5()
            with open(full_path, 'rb') as file:
                for chunk in iter(lambda: file.read(4096), b""):
                    hash_md5.update(chunk)
            actual_asset_hashes.append(hash_md5.digest())
    actual_asset_hash = actual_asset_hashes[0]
    assert expected_asset_hash == actual_asset_hash
