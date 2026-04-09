import os
import subprocess
from importlib.metadata import PackageNotFoundError, version

# Read the installed package version set by setuptools-scm from the git tag.
# Falls back to "unknown" when the package isn't installed (e.g. running from source).
try:
    __version__ = version("civic-scraper")
except PackageNotFoundError:
    __version__ = "unknown"

# Capture the current git commit for traceability in dev/editable installs.
# Falls back to "unknown" when git isn't available (e.g. installed from PyPI).
try:
    __git_commit__ = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=os.path.dirname(__file__),
        stderr=subprocess.DEVNULL,
    ).decode().strip()
except Exception:
    __git_commit__ = "unknown"
