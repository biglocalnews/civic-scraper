# civic-scraper

- [Overview](#overview)
- [Setup](#setup)
- [Usage](#usage)
  - [Scraping asset information](#scraping-asset-information)
  - [Downloading assets](#downloading-assets)
  - [Exporting asset metadata to csv](#exporting-asset-metadata-to-csv)

## Overview

`civic-scraper` is a Python package that helps identify and download agendas, minutes and other file assets related to government meetings from local public agencies around the U.S.

> License: [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0)

## Setup

```
git clone https://github.com/biglocalnews/civic-scraper
cd civic-scraper
python setup.py install
```

## Usage

To use `civic-scraper` in your own Python code, follow the steps below.

> Note: At present, `civic-scraper` supports only websites using [CivicPlus's Agenda Center](https://www.civicplus.com/civicengage/civicengage/features), but in the future, it will support several types of websites where local governments post information about public meetings.

### Scraping asset information

Create an instance of `CivicPlusSite` by passing it the URL for an
agency's CivicPlus Agenda Center site. Then call the `scrape`
method.


```
# Example for East Palo Alto, CA

from civic_scraper.scrapers import CivicPlusSite
url = 'https://ca-eastpaloalto.civicplus.com/AgendaCenter'
site = CivicPlusSite(url)
assets = site.scrape()
```

By default, `scrape` returns metadata about meeting minutes, agendas and video recordings posted on the current day. **However, it does not automatically download the assets!!** See below for details on how to [download files](#downloading-assets) and [export metadata](#exporting-asset-metadata-to-csv).

Scraping can be modified to capture assets from varying time ranges by
calling `scrape()` with the optional `start_date` and/or `end_date` arguments. Their
values must be strings of the form `YYYY-MM-DD`.

```
# Scrape info from January 1-30, 2020
assets = site.scrape(start_date='2020-01-01', end_date='2020-01-30')
```

### Downloading assets

There are two ways to download all file assets discovered by a scrape.

```
# Scrape metadata first,
# then call download on the response
assets = site.scrape()
assets.download()

# or...

# Scrape and download simultaneously
site.scrape(download=True)
```

By default, the above steps will download all of the assets to the current working directory.

You can exercise more fine-grained control over the download directory and other variables as demonstrated below:

```
# Download meeting minutes that are 20MB
# or less in size to /tmp/assets

assets = site.scrape()
assets.download(
  target_dir='/tmp/assets',
  file_size=20,
  asset_list=['minutes']
)

# OR

site.scrape(
  target_dir='/tmp/assets',
  file_size=20,
  asset_list=['minutes']
)
```

Here are more details on the parameters mentioned above:

* `target_dir` (*str*) - Target download directory. The default is the current working directory.
* `file_size` (*int*) - Limit downloads to files with max file size in megabytes. The default is `None`, in which case all files will be downloaded.
* `asset_list` (*list of str*) -  Limit downloads to one or more asset types. The default is to download all types of documents. Valid options:
  * `agenda`
  * `minutes`
  * `audio`
  * `video`
  * `agenda_packet` - The exhibits and ancillary documents attached to a meeting agenda.
  * `captions` - The transcript of a meeting recording.

### Exporting asset metadata to csv

To bypass downloading of assets and instead generate a CSV of links to the assets and metadata about them:

```
output_file = '/tmp/asset_metadata.csv'

# Scrape, then write
assets = site.scrape()
assets.to_csv(output_file)

# OR


# Scrape and write all at once
site.scrape(csv_export=output_file)
```

You can choose to append to a pre-existing metadata file by using the `append` argument:

```
output_file = '/tmp/asset_metadata.csv'

# Scrape, then write
assets = site.scrape()
assets.to_csv(output_file, append=True)

# OR


# Scrape and write all at once
site.scrape(csv_export=output_file, append=True)
```

Here are more details on the above arguments:

* `target_path` (*str*) - Full path to output file (required).
* `append` (*bool*) - Update a pre-existing file if set to `True`. By default, a pre-existing file will be over-written.

The generated file contains the following information:

* `url` (*str*) - The URL for an asset. Ex: https://ca-eastpaloalto.civicplus.com/AgendaCenter/ViewFile/Agenda/_04282020-1613
* `asset_name` (*str*) - The title of an asset. Ex: City Council Special Budget Meeting - April 4, 2020
* `committee_name` (*str*) - The name of the committee that generated the asset. Ex: City Council
* `place` (*str*) - The name of the place associated with the asset in lowercase with spaces and punctuation removed. Ex: eastpaloalto
* `state_or_province` (*str*) - The lowercase two-letter abbreviation for the state or province associated with an asset. Ex: ca
* `asset_type` (*str*) - One of the following strings: `agenda`, `minutes`, `audio`, `video`, `agenda_packet`, `captions`
* `meeting_date` (*str*) - Date of meeting or blank if no meeting date given in the format YYYY-MM-DD.
* `meeting_time` (*str*) - Time of meeting or blank if no time given.
* `meeting_id`: (*str*) - Platform name, `state_or_province` and `place` followed by unique meeting ID assigned by platform. Ex: civicplus_ca_eastpaloalto_01272020-1589
* `scraped_by` (*str*) - Module and version that produced the asset using [semantic versioning](https://semver.org). Ex: `civicplus.py_1.0.0`
* `content_type` (*str*) - The [MIME type][] of the asset. Ex: `application/pdf`
* `content_length` (*str*) - The size of the asset in bytes.

[MIME type]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types
