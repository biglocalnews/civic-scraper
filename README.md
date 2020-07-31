# civic-scraper

A Python package to identify and download agendas, minutes and more from local public meetings around the U.S.

## In Python

To invoke `civic-scraper` in Python code, follow the steps below.

### 1. Choose a type of site to scrape (optional)

The first step to scraping public meetings is to create a `Site` object. (Note: At present, `civic-scraper` supports only websites using CivicPlus's Agenda Center, but in the future, it will support several types of websites where local governments post information about public meetings.)

To create an instance of a `CivicPlusSite` object -- the subclass of `Site` specific to CivicPlus Agenda Center websites -- first select it from the dictionary of `SUPPORTED_SITES` specified in `__init__.py`.

```
from civic_scraper.scrapers import SUPPORTED_SITES
cp = SUPPORTED_SITES['civicplus']
```

### 2. Create a CivicPlusSite instance

Now that you've selected `CivicPlusSite` from the dictionary, you can initialize a `CivicPlusSite` object by passing it a CivicPlus `base_url` of the form *https://tk.civicplus.com/AgendaCenter*, where *tk* is the string specific to the website, such as *ca-eastpaloalto*.

For example, you would create a `CivicPlusSite` object for East Palo Alto, Calif. like this:

```
base_url = 'https://ca-eastpaloalto.civicplus.com/AgendaCenter'
site = cp(base_url)
```

Note that if you've skipped step 1, you can initialize a CivicPlusSite directly like this:

```
from civic_scraper.scrapers import CivicPlusSite
base_url = 'https://ca-eastpaloalto.civicplus.com/AgendaCenter'
site = CivicPlusSite(base_url)
```

A `CivicPlusSite` instance has two attributes:

* `self.base_url`: str, the `base_url` entered to initialize the instance.
* `self.runtime`: str, the date the instance was initialized in the form YYYYMMDD.

### 3. Scrape the CivicPlusSite instance

`CivicPlusSite` has just one public method, `scrape()`. Calling it is easy:

`asset_collection = site.scrape()`

By default, this method returns an instance of an `AssetCollection` object containing all assets (like meeting minutes, agendas and video recordings) posted on the day the `CivicPlusSite` object was initialized. However, you can specify a different time range, when you scrape any `CivicPlusSite` instance by calling `scrape()` with an optional `start_date` and/or `end_date`, where both `start_date` and `end_date` are a string of the form YYYYMMDD.

```
start_date = '20200101'
end_date = '20200130'
asset_collection = site.scrape(start_date, end_date)
```

But what if you want to manually initialize an `AssetCollection`? Here's how.

`Asset(**asset_args)`,

where `asset_args` is a dictionary containing the following metadata about an `Asset`: 

* `url`: str, the URL to download an asset. Ex: https://ca-eastpaloalto.civicplus.com/AgendaCenter/ViewFile/Agenda/_04282020-1613
* `asset_name`: str, the title of an asset. Ex: City Council Special Budget Meeting - April 4, 2020
* `committee_name`: str, the name of the committee that generated the asset. Ex: City Council
* `place`: str, the name of the place associated with the asset in lowercase with spaces and punctuation removed. Ex: eastpaloalto
* `state_or_province`: str, the lowercase two-letter abbreviation for the state or province associated with an asset. Ex: ca
* `asset_type`: str, one of the following strings: 'agenda', 'minutes', 'audio', 'video', 'video2', 'agenda_packet', 'captions'
* `meeting_date`: datetime.date corresponding to the time the meeting was held or today if no date given
* `meeting_time`: datetime.time corresponding to the time the meetings was held or midnight if no time given
* `meeting_id`: #TODO: Decide the spec for this.
* `scraped_by`: str, describes the module and version that produced the asset. Ex: 'civicplus.py_2020-07-16'
* `content_type`: str, the file type of the asset as given by HTTP headers. Ex: 'application/pdf'
* `content_length`: str, the size of the asset in bytes

When an `Asset` instance is created, this metadata is used to create the instance's attributes, which correspond to each key-value pair in the dictionary. For example, if you initialized an Asset like this...

```
from civic_scraper.asset import Asset
import datetime
Asset(
    url = 'https://ca-eastpaloalto.civicplus.com/AgendaCenter/ViewFile/Agenda/_04282020-1613',
    asset_name = 'Budget Meeting',
    committee_name = 'Budget Committee',
    place = 'eastpaloalto',
    state_or_province = 'ca',
    asset_type = 'agenda',
    meeting_date = datetime.date(2020, 4, 28),
    meeting_time = datetime.time(12, 0),
    meeting_id = 'https://ca-eastpaloalto.civicplus.com/AgendaCenter/ViewFile/Agenda/_04282020-1613',
    scraped_by = 'civicplus.py_v2020-07-16',
    content_length = 1775883 
)
```

...then you would get an `Asset` with attributes like `self.url` = 'https://ca-eastpaloalto.civicplus.com/AgendaCenter/ViewFile/Agenda/_04282020-1613'.

Since `AssetCollection` instances are simply lists of `Asset` instances, you can initialize an `AssetCollection` by calling `AssetCollection(assets)`, where `assets` is a list of `Asset` instances. (This is exactly what happens under the hood in `civicplus.py` when you call `scrape()`!)

Now that you have an `AssetCollection`, you can download the assets and save metadata about them to a csv.

### 4. Download assets

To download all of the assets in an `AssetCollection`, call `asset_collection.download()`, where `asset_collection` is an `AssetCollection` instance.

By default, this will download all of the assets to the current working directory. However, `download` has three optional arguments:

* `target_dir`: str, the current working directory is the default.
* `file_size`: int, the file size in megabytes. If specified, limits downloads to assets under the provided size. The default is `None`, in which case all files will be downloaded.
* `asset_list`: list of str, with one or more of the following asset types: 'agenda', 'minutes', 'audio', 'video', 'video2', 'agenda_packet', 'captions'. The default is all of the available asset types.

If need be, you can also download an individual `Asset` instance by calling `download` on an `Asset` instance using the same optional arguments. Here is an example call:

```
asset = Asset(**asset_args)
asset.download(target_dir='test', file_size=20, asset_list=['minutes'])
```

### 5. Export a csv of metadata for a given AssetCollection

Suppose you don't want to download all of the assets locally, but just want links to the assets and metadata about them? In that case, you can call `to_csv` on any `AssetCollection` like this:

`asset_collection.to_csv(target_path, target_dir, appending)`, where 

* `target_path`: str, an optional file path
* `target_dir`: str, an optional directory
* `appending`: bool, an optional argument that allows `to_csv` to overwrite an existing file with the same full file path if `False` (the default) or append new rows to an existing file with the same file path if `True`

If you wish to write out metadata for an individual `Asset` instance, you can call `append_to_csv` on the asset. This function takes two arguments:

* `target_path`: str,  required file path to write out the csv
* `write_header`: bool, a value indicating whether to write the header (dictionary key values) to a csv if True, or not to write the header if False (the default)
  
## Contents of this package at a glance.

At present, this repository contains the following production-ready code:

* **__init__.py**: Contains a dictionary of `SUPPORTED_SITES`, that is, of subclasses of `Site` available to be initialized.
* **scrapers/site.py**: A `Site` base class, representing a given website that `civic-scraper` can scrape. This code is production-ready.
* **scrapers/civicplus.py**: A subclass of `Site` specific to websites using the CivicPlus website type. This code is production-ready.
* **asset.py**: A module with two classes, both production-ready: 
  * An `Asset` class modeling a specific asset, such as a meeting agenda, meeting minutes or meeting video, which is available for `civic-scraper` to scrape.
  * An `AssetCollection` class modeling all of the assets available for `civic-scraper` to scrape. It is a list of `Asset` instances.

In the future, this repository will contain the code for a variety `Site` subclasses, each corresponding to a different public meeting website type.

### Command line invocation

TBD
