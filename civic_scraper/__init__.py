from importlib.metadata import PackageNotFoundError, version

# Read the installed package version set by setuptools-scm from the git tag.
# Falls back to "unknown" when the package isn't installed (e.g. running from source).
try:
    __version__ = version("civic-scraper")
except PackageNotFoundError:
    __version__ = "unknown"
