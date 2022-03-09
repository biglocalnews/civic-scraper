import os
from pathlib import Path

from civic_scraper.utils import default_user_home


class Cache:
    def __init__(self, path=None):
        self.path = path or self._path_from_env or self._path_default

    def write(self, name, content):
        out = Path(self.path, name)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w") as fh:
            fh.write(content)
        return str(out)

    @property
    def assets_path(self):
        "Path for agendas, minutes and other gov file assets"
        return str(Path(self.path).joinpath("assets"))

    @property
    def artifacts_path(self):
        "Path for HTML and other intermediate artifacts from scraping"
        return str(Path(self.path).joinpath("artifacts"))

    @property
    def metadata_files_path(self):
        "Path for metadata files related to file artifacts"
        return str(Path(self.path).joinpath("metadata"))

    @property
    def _path_from_env(self):
        return os.environ.get("CIVIC_SCRAPER_DIR")

    @property
    def _path_default(self):
        return default_user_home()
