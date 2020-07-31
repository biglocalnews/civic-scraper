# civic-scraper

- [Overview](#overview)
- [Setup](#setup)
- [Usage](#usage)
  - [Scraping asset information](#scraping-asset-information)
  - [Downloading assets](#downloading-assets)
  - [Export asset metadata to csv](#export-asset-metadata-to-csv)

## Overview

`civi-scraper` is a Python package that helps identify and download agendas, minutes and more from local public agencies around the U.S.

## Setup

```
git clone https://github.com/biglocalnews/civic-scraper
cd civic-scraper
python setup.py install
```

## Usage

To use `civic-scraper` in your own Python code, follow the steps below.

> Note: At present, `civic-scraper` supports only websites using CivicPlus's Agenda Center, but in the future, it will support several types of websites where local governments post information about public meetings.

### Scraping asset information

Create an instance of `CivicPlusSite` by passing it the URL of for an
agency's Civic Plus Agenda Center site. Then call the `scrape`
method.

Below is an example for East Palo Alto, CA:

```
from civic_scraper.scrapers import CivicPlusSite
url = 'https://ca-eastpaloalto.civicplus.com/AgendaCenter'
site = CivicPlusSite(url)
assets = site.scrape()
```

By default, `scrape` returns metadata about meeting minutes, agendas and video recordings posted on the current day.

> However, it does not automatically download the assets!! See below
> for details on how to download information.

Scraping can be modified to capture assets from varying time ranges by
calling `scrape()` with the optional `start_date` and/or  `end_date` arguments. The
value must be a string of the form `YYYYMMDD`.

```
# Scrape from January 1-30, 2020
assets = site.scrape(start_date='20200101', end_date='20200130')
```

### Downloading assets

There are two ways to download all of the file assets discovered by a scrape.

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

* `target_dir` (*str*) - Target download directory (default: current working directory).
* `file_size` (*int*) - Limit downloads to files with max file size in megabytes. Default is `None`, in which case all files will be downloaded.
* `asset_list` (*list of str*) -  Limit downloads to one more or more asset types (default: all types are downloaded). Valid options:
  * `agenda`
  * `minutes`
  * `audio`
  * `video`
  * `video2` - TK explanation
  * `agenda_packet` - TK explanation
  * `captions` - TK explanation

### Export asset metadata to csv

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

You can choose to append to a pre-existing metadata file by using the
`append` argument:

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
* `append` (*bool*) - An optional argument that allows `to_csv` to add data to an existing file. By default, a pre-existing file will be over-written.

The generated file contains the following information:

* `url` (*str*) - The URL for an asset. Ex: https://ca-eastpaloalto.civicplus.com/AgendaCenter/ViewFile/Agenda/_04282020-1613
* `asset_name` (*str*) - The title of an asset. Ex: City Council Special Budget Meeting - April 4, 2020
* `committee_name` (*str*) - The name of the committee that generated the asset. Ex: City Council
* `place` (*str*) - The name of the place associated with the asset in lowercase with spaces and punctuation removed. Ex: eastpaloalto
* `state_or_province` (*str*) - The lowercase two-letter abbreviation for the state or province associated with an asset. Ex: ca
* `asset_type` (*str*) - One of the following strings: `agenda`, `minutes`, `audio`, `video`, `video2`, `agenda_packet`, `captions`
* `meeting_date` (*TK: human readable format*) Date of meeting or today if no date given (TODO: We should leave blank if date is not determined, rather than filling in current day)
* `meeting_time` (*TK: human readable format*) corresponding to the time the meetings was held or midnight if no time given (TODO: We should leave blank if no time was obtained)
* `meeting_id`: TODO: Decide the spec for this.
* `scraped_by` (*str*) - Module and version that produced the asset. Ex: `civicplus.py_2020-07-16` (TODO: We should use semantic versioning for this)
* `content_type` (*str*) - The [MIME type][] of the asset. Ex: `application/pdf`
* `content_length` (*str*) - The size of the asset in bytes.

[MIME type]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types
