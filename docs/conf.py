import os
import sys
from datetime import datetime

# Insert the parent directory into the path
sys.path.insert(0, os.path.abspath(".."))

extensions = ["myst_parser", "sphinx.ext.autodoc", "sphinx.ext.napoleon"]
templates_path = ["_templates"]
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
master_doc = "index"

project = "civic-scraper"
year = datetime.now().year
copyright = f"{year} Big Local News"

exclude_patterns = ["_build"]

pygments_style = "sphinx"

html_theme = "sphinx_rtd_theme"
