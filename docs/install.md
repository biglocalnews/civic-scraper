(install)=

# Installation

## Install

```
pip install civic-scraper
```

Upon installation, you should have access to the {code}`civic-scraper` tool on the command line:

```
civic-scraper --help
```

You should also be able to import the {code}`civic_scraper` package from a Python script:

```
import civic_scraper
print(civic_scraper.__version__)
```

:::{note}
See {ref}`the usage docs <usage>` for details on using *civic-scraper* on
the command line and in custom scripts.
:::

(default-cache-dir)=

## Default cache directory

By default, files downloaded by the CLI tool and underlying Python library code
will be saved to the {code}`.civic-scraper` folder in the user's home directory.

On Linux/Mac systems, this will be {code}`~/.civic-scraper/`.

(customize-cache-dir)=

## Customize cache directory

To use an alternate cache directory, set the below environment variable
(e.g. in a {code}`~/.bashrc` or {code}`~/.bash_profile` configuration file):

```
export CIVIC_SCRAPER_DIR=/tmp/some_other_dir
```
