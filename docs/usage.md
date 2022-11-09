(usage)=

# Usage

## Overview

*civic-scraper* provides a command-line tool and underlying Python library
that can be used to fetch metadata about government documents and help
download those documents.

The command-line tool makes it easy to get started scraping for basic
use cases, while the Python library offers a wider range of options
for use in custom scripts.

Government agendas and other files downloaded by *civic-scraper* are saved to a
a standard -- but {ref}`configurable <customize-cache-dir>` -- location in
the user's home directory ({code}`~/.civic-scraper` on Linux/Mac).

Below are more details on using the [Command line](cli) as well as
writing [Custom scripts](custom-scripts).

```{note}
`civic-scraper` currently supports scraping of five software [platforms]: Civic Clerk, Civic Plus, Granicus,
Legistar and PrimeGov.
```

(find-a-site)=

## Find a site to scrape

Before you can start scraping government documents, you must first pinpoint
URLs for one or more agencies of interest. Alternatively, you may want
to review our lists of known [Civic Plus sites] or [Legistar sites] to
see if any agencies in your area use one of these platforms.

In addition to Civic Plus and Legistar, *civic-scraper* currently supports 
Civic Clerk, Granicus and PrimeGov.

If your target agency uses one of these [platforms], you should be able to scrape the
site by writing a Python script that uses the appropriate platform scraper class.

If your agency site is not currently supported, you can try reaching out
to us to see if the platform is on our development roadmap. We also
welcome {ref}`open-source contributions <contributing>` if you want to
add support for a new platform.


(cli)=

## Command line

Once you {ref}`install <install>` *civic-scraper* and
{ref}`find a site to scrape <find-a-site>`, you're ready to begin
using the command-line tool.

```{note}
To test drive examples below, you should replace {code}`<site URL>` with
a URL to a Civic Plus site, e.g. <http://nc-nashcounty.civicplus.com/AgendaCenter>.
```

### Getting help

*civic-scraper* provides a {code}`scrape` subcommand as the primary way to
fetch metadata and files from government sites. You can use the tool's {code}`--help`
flag to get details on the available options:

```
civic-scraper scrape --help
```

### Basic usage

By default, *civic-scraper* checks a site for meetings that occur on the current
day and generates a metadata CSV listing information about any available meeting
agendas or minutes:

```
# Scrape current day and generate metadata CSV
civic-scraper scrape --url <site URL>
```

(download-docs-cli)=

### Download documents

*civic-scraper* does not automatically download agendas or minutes by default
since, depending on the {ref}`time period of the scrape <scrape-by-date-cli>` and size of the documents,
this could involve a large quantity of data.

You must explicitly tell *civic-scraper* to download documents by using the
{code}`--download` flag, which will fetch and save agendas/minutes
to *civic-scraper*'s {ref}`cache directory <default-cache-dir>`:

```
civic-scraper scrape --download --url <site URL>
```

(scrape-by-date-cli)=

### Scrape by date

*civic-scraper* provides the ability to set a date range to support
scraping documents from meetings in the past:

```
# Scrape docs from meetings in January 2020
civic-scraper scrape \
  --start-date=2020-01-01 \
  --end-date=2020-01-31 \
  --url <site URL>
```

### Scrape multiple sites

If you need to scrape more than one site at a time,
you can supply a CSV containing URLs to *civic-scraper*.

The input CSV must store site URLs in a column called `url`,
similar to the list of [known sites for the Civic Plus platform].

Let's say we have a *ca_examples.csv* with two agencies in California:

```
state,url
ca, https://ca-alpinecounty.civicplus.com/AgendaCenter
ca, https://ca-anaheim.civicplus.com/AgendaCenter
```

You can scrape both sites by supplying the CSV's path to the
{code}`--urls-file` flag:

```
# Scrape current day for URLs listed in CSV (should contain "url" field)
civic-scraper scrape --urls-file ca_examples.csv
```

(cache-artifacts-cli)=

### Store scraping artifacts

As part of the scraping process, *civic-scraper*
acquires "intermediate" file artifacts such as
HTML pages with links to meeting agendas and minutes.

We believe it's important to keep such file
artifacts for the sake of transparency and reproducibility.

Use the {code}`--cache` flag to store these files in the
{ref}`civic-scraper cache directory <default-cache-dir>`:

```
civic-scraper scrape --cache  --url <site URL>
```

### Putting it all together

The command-line options mentioned above can be used in tandem (with the
exception of {code}`--url` and {code}`--urls-file`, which are mutually
exclusive).

For example, the below command:

```
civic-scraper scrape \
  --cache \
  --download \
  --start-date=2020-01-01 \
  --end-date=2020-01-31 \
  --url <site URL>
```

would performing the following actions:

- Generate a [Metadata CSV] on available documents for meetings in January 2020
- {ref}`Download <download-docs-cli>` agendas and minutes for meetings in the specified date range
- {ref}`Cache <cache-artifacts-cli>` the HTML of search results pages containing links to agendas/minutes

(custom-scripts)=

## Custom scripts

*civic-scraper* provides an importable Python package for users who are comfortable creating their
own scripts. The Python package provides access to a wider variety of features for
added flexibility and support for more advanced scenarios (e.g controlling the location of downloaded
files or avoiding download of excessively large files).

```{note}
In order to use *civic-scraper* in a script, you must install the package and
import one of the platform scraper classes. In the examples below,
we use the {code}`CivicPlusSite` class. See the [platforms] folder on
GitHub for other available platform classes.

Site classes may support slightly different interfaces/features
due to differences in features on each platform.

It's a good idea to review the docstrings and methods for a class
before attempting to use it.
```

### Scrape metadata

Once you {ref}`install <install>` *civic-scraper* and
{ref}`find a site to scrape <find-a-site>`, you're ready to begin
using the `civic_scraper` Python package.

```{note}
Below we use East Palo Alto, CA as an example. More agencies
can be found in the list of [known sites for the Civic Plus platform].
```

Create an instance of {code}`CivicPlusSite` by passing it the URL for an
agency's CivicPlus Agenda Center site.  Then call the {code}`scrape` method:

```
from civic_scraper.platforms import CivicPlusSite
url = 'https://ca-eastpaloalto.civicplus.com/AgendaCenter'
site = CivicPlusSite(url)
assets_metadata = site.scrape()
```

```{note}
{code}`CivicPlusSite` is an alias for more convenient import of the actual Civic Plus class
located at {py:class}`civic_scraper.platforms.civic_plus.site.Site`.
```

{py:meth}`CivicPlusSite.scrape <civic_scraper.platforms.civic_plus.site.Site.scrape>` will automatically store
downloaded assets in the {ref}`default cache directory <default-cache-dir>`.

This location can be customized by {ref}`setting an environment variable <customize-cache-dir>` or by passing an
instance of {py:class}`civic_scraper.base.cache.Cache` to {py:class}`CivicPlusSite <civic_scraper.platforms.civic_plus.site.Site>`:

```
from civic_scraper.base.cache import Cache
from civic_scraper.platforms import CivicPlusSite

url = 'https://ca-eastpaloalto.civicplus.com/AgendaCenter'

# Change output dir to /tmp
site = CivicPlusSite(url, cache=Cache('/tmp'))
assets_metadata = site.scrape()
```

(export-metadata-script)=

### Export metadata to CSV

By default, {py:meth}`CivicPlusSite.scrape <civic_scraper.platforms.civic_plus.site.Site.scrape>` returns an {py:class}`~civic_scraper.base.asset.AssetCollection`
containing {py:class}`~civic_scraper.base.asset.Asset` instances.

The asset instances store metadata about specific meeting agendas and
minutes discovered on the site.

To save a timestamped CSV containing metadata for available assets,
call {py:meth}`AssetCollection.to_csv() <civic_scraper.base.asset.AssetCollection.to_csv>` with a target output directory:

```
# Save metadata CSV
assets_metadata.to_csv('/tmp/civic-scraper/metadata')
```

(download-assets-script)=

### Download assets

There are two primary ways to download file assets discovered by a scrape.

You can trigger downloads by passing {code}`download=True` to
{py:meth}`CivicPlusSite.scrape <civic_scraper.platforms.civic_plus.site.Site.scrape>`:

```
site.scrape(download=True)
```

Or you can loop over the {py:class}`Asset instances <civic_scraper.base.asset.Asset>`
in an {py:class}`~civic_scraper.base.asset.AssetCollection` and
call {py:meth}`~civic_scraper.base.asset.Asset.download` on each with a target output directory:

```
assets_metadata = site.scrape()
for asset in assets_metadata:
    asset.download('/tmp/civic-scraper/assets')
```

### Scrape by date

By default, scraping checks the site for meetings on the current day (based on a
user's local time).

Scraping can be modified to capture assets from different date ranges by
supplying the optional {code}`start_date` and/or {code}`end_date` arguments
to {py:meth}`CivicPlusSite.scrape <civic_scraper.platforms.civic_plus.site.Site.scrape>`.

Their values must be strings of the form {code}`YYYY-MM-DD`:

```
# Scrape info from January 1-30, 2020
assets_metadata = site.scrape(start_date='2020-01-01', end_date='2020-01-30')
```

```{note}
The above will *not* download the assets by default. See {ref}`download assets script <download-assets-script>` for details on saving the discovered files locally.
```

### Advanced configuration

You can exercise more fine-grained control over the size and type of files to download
using the {code}`file_size` and {code}`asset_list` arguments to
{py:meth}`CivicPlusSite.scrape <civic_scraper.platforms.civic_plus.site.Site.scrape>`:

```
# Download only minutes that are 20MB or smaller
site.scrape(
  download=True,
  file_size=20,
  asset_list=['minutes']
)
```

Here are more details on the parameters mentioned above:

- {code}`file_size` - Limit downloads to files with max file size in megabytes.
- {code}`asset_list` -  Limit downloads to one or more [asset types]
  (described below in [Metadata CSV](metadata-csv)). The default is to download all document types.

(metadata-csv)=

## Metadata CSV

*civic-scraper* provides the ability to produce a CSV of metadata about agendas, minutes and other files
discovered during a scrape. The file is automatically generated when using the {ref}`command line <cli>`
and can be exported using {py:meth}`AssetCollection.to_csv <civic_scraper.base.asset.AssetCollection.to_csv>`
in the context of a {ref}`custom script <export-metadata-script>`.

The generated file contains the following information:

- `url` (*str*) - The download link for an asset

- `asset_name` (*str*) - The title of an asset. Ex: City Council Special Budget Meeting - April 4, 2020

- `committee_name` (*str*) - The name of the committee that generated the asset. Ex: City Council

- `place` (*str*) - Name of the place associated with the asset (lowercased, punctuation removed). Ex: eastpaloalto

- `state_or_province` (*str*) - The lowercase two-letter abbreviation for the state or province associated with an asset

- `asset_type` (*str*) - One of the `` _`asset types` `` for meeting-related documents:

  - `agenda`
  - `minutes`
  - `audio`
  - `video`
  - `agenda_packet` - The exhibits and ancillary documents attached to a meeting agenda.
  - `captions` - The transcript of a meeting recording.

- `meeting_date` (*str*) - Date of meeting or blank if no meeting date given in the format {code}`YYYY-MM-DD`.

- `meeting_time` (*str*) - Time of meeting or blank if no time given.

- `meeting_id` (*str*) - A unique meeting ID assigned to the record.

- `scraped_by` (*str*) - Version of *civic-scraper* that produced the asset. Ex: `civicplus_v0.1.0`

- `content_type` (*str*) - The [MIME type] of the asset. Ex: `application/pdf`

- `content_length` (*str*) - The size of the asset in bytes.

(change-download-dir)=

## Changing the download location

By default, *civic-scraper* will store downloaded agendas, minutes and
other files in a {ref}`default directory <default-cache-dir>`.

You can {ref}`customize this location <customize-cache-dir>` by setting
the {code}`CIVIC_SCRAPER_DIR` environment variable.

[civicplus agenda center]: https://www.civicplus.com/civicengage/civicengage/features
[Legistar sites]: https://docs.google.com/spreadsheets/d/1YVn5C0nN_aAITIBGMhNiulnLpF5eo5fF6gpZTQ4oWU8/edit?usp=sharing
[platforms]: https://github.com/biglocalnews/civic-scraper/tree/master/civic_scraper/platforms
[examples folder on github]: https://github.com/biglocalnews/civic-scraper/tree/master/examples
[Civic Plus sites]: https://docs.google.com/spreadsheets/d/e/2PACX-1vQaa2mt0aXGN-gMT1LHgYzDbzrxwF1aQBKCkY5QMoUGlAbFVrv47FaMwPdiISx-kdedTY8_6fiJ0Vi3/pubhtml
[known sites for the civic plus platform]: https://docs.google.com/spreadsheets/d/e/2PACX-1vQaa2mt0aXGN-gMT1LHgYzDbzrxwF1aQBKCkY5QMoUGlAbFVrv47FaMwPdiISx-kdedTY8_6fiJ0Vi3/pubhtml
[mime type]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types
