import html
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import demjson3 as demjson
import lxml.html
from requests import Session

import civic_scraper
from civic_scraper import base
from civic_scraper.base.asset import Asset, AssetCollection
from civic_scraper.base.cache import Cache


class CivicClerkSite(base.Site):
    def __init__(self, url, place=None, state_or_province=None, cache=Cache()):

        self.url = url
        self.base_url = "https://" + urlparse(url).netloc
        self.civicclerk_instance = urlparse(url).netloc.split(".")[0]
        self.place = place
        self.state_or_province = state_or_province
        self.cache = cache

        self.session = Session()
        self.session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"
        )

        # Raise an error if a request gets a failing status code
        self.session.hooks = {
            "response": lambda r, *args, **kwargs: r.raise_for_status()
        }

    def create_asset(self, asset, committee_name, meeting_datetime, meeting_id):
        asset_url, asset_name = asset
        asset_type = "Meeting"

        e = {
            "url": asset_url,
            "asset_name": asset_name,
            "committee_name": committee_name,
            "place": None,
            "state_or_province": None,
            "asset_type": asset_type,
            "meeting_date": meeting_datetime.date(),
            "meeting_time": meeting_datetime.time(),
            "meeting_id": meeting_id,
            "scraped_by": f"civic-scraper_{civic_scraper.__version__}",
            "content_type": "txt",
            "content_length": None,
        }
        return Asset(**e)

    def get_meeting_id(self, event):
        link = event.xpath("./td[contains(@id, '_3')]//a")[0]
        href = link.attrib["href"]
        pattern = r".*?\((?P<id>.*?),.*"
        match = re.match(pattern, href)
        return (
            match.group("id"),
            "civicclerk_{}_{}".format(self.civicclerk_instance, match.group("id")),
        )

    def get_agenda_items(self, text):
        event_tree = lxml.html.fromstring(text)

        event_frame = event_tree.xpath("//iframe[@id='docViewer']")[0]

        if "src" not in event_frame.attrib:
            return []

        event_frame_url = self.base_url + event_frame.attrib["src"]

        frame_response = self.session.get(event_frame_url)
        frame_tree = lxml.html.fromstring(frame_response.text)
        frame_has_table = True if frame_tree.xpath("//table") else False

        assets = []

        if frame_has_table:
            assets_list = frame_tree.xpath(
                "//tr[./td[@class='dx-wrap dxtl dxtl__B0' and not(@colspan)]]"
            )
            for item in assets_list:
                link_tr_text = item.xpath("./following-sibling::tr[1]")[0]
                for tr in link_tr_text.xpath(".//a"):
                    if tr.attrib["href"] != "#":
                        asset_url = self.base_url + "/Web" + tr.attrib["href"][2:]
                        asset_name = tr.xpath("./text()")[0]
                        assets.append((asset_url, asset_name))
        else:
            no_agenda_str = "Agenda content has not been published for this meeting."
            if no_agenda_str not in frame_tree.xpath("//text()"):
                assets.append((event_frame_url, None))

        return assets

    def events(self):

        yield from self._future_events()
        yield from self._past_events()

    def _future_events(self):

        callback_id = "aspxroundpanelCurrent$pnlDetails$grdEventsCurrent"
        for page in self._paginate(callback_id):
            events = page.xpath(
                "//table[@id='aspxroundpanelCurrent_pnlDetails_grdEventsCurrent_DXMainTable']/tr[@class='dxgvDataRow_CustomThemeModerno']"
            )
            yield from events

    def _past_events(self):

        callback_id = "aspxroundpanelRecent2$ASPxPanel4$grdEventsRecent2"
        for page in self._paginate(callback_id):
            events = page.xpath(
                "//table[@id='aspxroundpanelRecent2_ASPxPanel4_grdEventsRecent2_DXMainTable']/tr[@class='dxgvDataRow_CustomThemeModerno']"
            )
            yield from events

    def _paginate(self, callback_id):

        response = self.session.get(self.url)

        tree = lxml.html.fromstring(response.text)

        yield tree

        # The first page of results is embedded in the full html
        # page. Subsequent pages of results will be extracted from
        # partial html returned from an endpoint intended for AJAX

        # Set up the pagination payload with it's constant values
        payload = {}
        payload["__EVENTARGUMENT"] = None
        payload["__EVENTTARGET"] = None
        (payload["__VIEWSTATE"],) = tree.xpath("//input[@name='__VIEWSTATE']/@value")
        (payload["__VIEWSTATEGENERATOR"],) = tree.xpath(
            "//input[@name='__VIEWSTATEGENERATOR']/@value"
        )
        (payload["__EVENTVALIDATION"],) = tree.xpath(
            "//input[@name='__EVENTVALIDATION']/@value"
        )
        payload["__CALLBACKID"] = callback_id

        # To get the next page of results from the AJAX endpoint,
        # it's basically a post request with a 'PBN' argument. But,
        # we also have to pass around the callback state that
        # the endpoint expects
        (event_callback_source,) = tree.xpath(
            """//script[contains(text(), "var dxo = new ASPxClientGridView('{}');")]/text()""".format(
                callback_id.replace("$", "_")
            )
        )

        callback_state = demjson.decode(
            re.search(
                r"^dxo\.stateObject = \((?P<body>.*)\);$",
                event_callback_source,
                re.MULTILINE,
            ).group("body")
        )

        # You may wonder why we are encoding the callback_state back to a string
        # right after we decoded it from a string.
        #
        # The reasons is that the original string uses single quotes and is
        # not html-escaped, and we need to use double quotes and html escape.
        payload[callback_id] = html.escape(demjson.encode(callback_state))

        item_keys = callback_state["keys"]
        payload["__CALLBACKPARAM"] = "c0:KV|61;{};GB|20;12|PAGERONCLICK3|PBN;".format(
            demjson.encode(item_keys)
        )

        # We'll break when we attempt to paginate to a next
        # page but we get the same keys
        previous_item_keys = None

        while item_keys != previous_item_keys:

            response = self.session.post(self.url, payload)
            previous_item_keys = item_keys

            data_str = re.match(r".*?/\*DX\*/\((?P<body>.*)\)", response.text).group(
                "body"
            )

            data = demjson.decode(data_str)

            table_tree = lxml.html.fromstring(data["result"]["html"])

            yield table_tree

            callback_state = data["result"]["stateObject"]

            payload[callback_id] = html.escape(demjson.encode(callback_state))

            item_keys = callback_state["keys"]
            payload["__CALLBACKPARAM"] = (
                "c0:KV|61;"
                + demjson.encode(callback_state["keys"])
                + ";GB|20;12|PAGERONCLICK3|PBN;"
            )

    def scrape(self, download=True):

        ac = AssetCollection()

        for event in self.events():
            committee_name = event.xpath("./td[contains(@id, '_3')]//text()")[1].strip()
            str_datetime = event.xpath("./td[contains(@id, '_4')]//text()")[0].strip()
            meeting_datetime = datetime.strptime(str_datetime, "%m/%d/%Y %I:%M %p")
            meeting_id_num, meeting_id = self.get_meeting_id(event)

            event_url = f"{self.base_url}/Web/DocumentFrame.aspx?id={meeting_id_num}&mod=-1&player_tab=-2"
            event_response = self.session.get(event_url)

            agenda_items = self.get_agenda_items(event_response.text)

            if agenda_items:
                assets = [
                    self.create_asset(a, committee_name, meeting_datetime, meeting_id)
                    for a in agenda_items
                ]
                for a in assets:
                    ac.append(a)

        if download:
            asset_dir = Path(self.cache.path, "assets")
            asset_dir.mkdir(parents=True, exist_ok=True)
            for asset in ac:
                if asset.url:
                    dir_str = str(asset_dir)
                    asset.download(target_dir=dir_str, session=self.session)

        return ac
