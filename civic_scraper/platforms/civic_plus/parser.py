import re
from datetime import datetime

import bs4

from civic_scraper.base.constants import SUPPORTED_ASSET_TYPES


class ParsingError(Exception):
    pass


class Parser:
    def __init__(self, html):
        self.html = html
        self.soup = bs4.BeautifulSoup(html, "html.parser")

    def parse(self):
        divs = self._get_divs_by_board()
        metadata = self._extract_asset_data(divs)
        return metadata

    def _get_divs_by_board(self):
        "Locate top-level divs containing meeting details for each board or entity"
        return self.soup.find_all("div", id=re.compile(r"cat\d+"))

    def _extract_asset_data(self, divs):
        "Extract asset-level data from each board/entity div"

        # bs4 helper
        def file_links_with_no_title(tag):
            # HTML link appears in meeting title and download menu.
            # This filters out the initial link
            return (
                tag.name == "a"
                and tag.get("href", "").startswith("/AgendaCenter/ViewFile")
                and not tag.has_attr("title")
            )

        metadata = []
        # Links often appear twice (once under meeting title, once in download menu)
        # so we track which we've already seen to avoid duplicate entries
        bookkeeping = set()
        for div in divs:
            cmte_name = self._committee_name(div)
            # Line-item data for each meeting is inside table rows.
            # Typically one row, but possibly multiple if several
            # meetings listed within the time span for a given govt entity
            for row in div.tbody.find_all("tr"):
                meeting_title = self._mtg_title(row)
                meeting_id = self._mtg_id(row)
                links = row.find_all(file_links_with_no_title)
                # Each meeting has multiple asset types
                for link in links:
                    # Skip links to page listing previous agenda versions
                    if self._previous_version_link(link):
                        continue
                    # Skip previously harvested links
                    if link["href"] in bookkeeping:
                        continue
                    metadata.append(
                        {
                            "committee_name": cmte_name,
                            "url_path": link["href"],
                            "meeting_date": self._mtg_date(row),
                            "meeting_time": None,
                            "meeting_title": meeting_title,
                            "meeting_id": meeting_id,
                            "asset_type": self._asset_type(link["href"]),
                        }
                    )
                    bookkeeping.add(link["href"])
        return metadata

    def _committee_name(self, div):
        # If present, remove span that contains
        # arrow ▼ for toggling meeting list
        try:
            div.h2.span.extract()
        except AttributeError:
            pass
        header_node = div.h2 or div.h3
        return header_node.text.strip()

    def _mtg_title(self, row):
        return row.p.text.strip()

    def _mtg_date(self, row):
        month, day, year = re.match(r"_(\d{2})(\d{2})(\d{4}).+", row.a["name"]).groups()
        return datetime(int(year), int(month), int(day))

    def _mtg_id(self, row):
        return row.a["name"]

    def _asset_type(self, url_path):
        if url_path.endswith("packet=true"):
            return "agenda_packet"
        asset_type = url_path.split("/")[3].lower()
        if asset_type in SUPPORTED_ASSET_TYPES:
            return asset_type
        else:
            msg = f"Unexpected asset type ({asset_type}) for {url_path}"
            raise ParsingError(msg)

    def _previous_version_link(self, link):
        return "PreviousVersions" in link["href"]
