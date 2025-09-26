import datetime
import itertools
import traceback
from collections import defaultdict, deque
import re
import requests
import json
import logging

import scrapelib
import lxml.html
import lxml.etree as etree
import pytz


class LegistarSession(requests.Session):

    def request(self, method, url, **kwargs):
        response = super(LegistarSession, self).request(method, url, **kwargs)
        payload = kwargs.get('data')

        self._check_errors(response, payload)

        return response

    def _check_errors(self, response, payload):
        if response.url.endswith('Error.aspx'):
            response.status_code = 503
            raise scrapelib.HTTPError(response)

        if not response.text:
            if response.request.method.lower() in {'get', 'post'}:
                response.status_code = 520
                raise scrapelib.HTTPError(response)

        if 'This record no longer exists. It might have been deleted.' in response.text:
            response.status_code = 410
            raise scrapelib.HTTPError(response)

        if payload:
            self._range_error(response, payload)

    def _range_error(self, response, payload):
        '''Legistar intermittently does not return the expected response when
        selecting a time range when searching for events. Right now we
        are only handling the 'All' range
        '''

        if self._range_is_all(payload):

            expected_range = 'All Years'

            page = lxml.html.fromstring(response.text)
            returned_range, = page.xpath(
                "//input[@id='ctl00_ContentPlaceHolder1_lstYears_Input']")

            returned_range = returned_range.value

            if returned_range != expected_range:
                response.status_code = 520
                # In the event of a retry, the new request does not
                # contain the correct payload data.  This comes as a
                # result of not updating the payload via sessionSecrets:
                # so, we do that here.
                payload.update(self.sessionSecrets(page))

                raise scrapelib.HTTPError(response)

    def _range_is_all(self, payload):
        range_var = 'ctl00_ContentPlaceHolder1_lstYears_ClientState'
        all_range = (range_var in payload and
                     json.loads(payload[range_var])['value'] == 'All')
        return all_range


class LegistarScraper(scrapelib.Scraper, LegistarSession):
    date_format = '%m/%d/%Y'

    def __init__(self, *args, **kwargs):
        super(LegistarScraper, self).__init__(*args, **kwargs)

    def lxmlize(self, url, payload=None):
        '''
        Gets page and returns as XML
        '''
        if payload:
            response = self.post(url, payload, verify=False)
        else:
            response = self.get(url, verify=False)
        entry = response.text
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def pages(self, url, payload=None):
        page = self.lxmlize(url, payload)

        yield page

        next_page = page.xpath(
            "//a[@class='rgCurrentPage']/following-sibling::a[1]")
        if payload and 'ctl00$ContentPlaceHolder1$btnSearch' in payload:
            del payload['ctl00$ContentPlaceHolder1$btnSearch']

        while len(next_page) > 0:
            if payload is None:
                payload = {}

            payload.update(self.sessionSecrets(page))

            event_target = next_page[0].attrib['href'].split("'")[1]

            payload['__EVENTTARGET'] = event_target

            page = self.lxmlize(url, payload)

            yield page

            next_page = page.xpath(
                "//a[@class='rgCurrentPage']/following-sibling::a[1]")

    def parseDetails(self, detail_div):
        """
        Parse the data in the top section of a detail page.
        """
        detail_query = ".//*[starts-with(@id, 'ctl00_ContentPlaceHolder1_lbl')"\
                       "     or starts-with(@id, 'ctl00_ContentPlaceHolder1_hyp')"\
                       "     or starts-with(@id, 'ctl00_ContentPlaceHolder1_Label')]"
        fields = detail_div.xpath(detail_query)

        details = {}

        for field_key, field in itertools.groupby(fields, fieldKey):
            field = list(field)
            field_1, field_2 = field[0], field[-1]

            key = field_1.text_content().replace(':', '').strip()

            if field_2.find('.//a') is not None:
                value = []
                for link in field_2.xpath('.//a'):
                    value.append({'label': link.text_content().strip(),
                                  'url': self._get_link_address(link)})

            elif 'href' in field_2.attrib:
                value = {'label': field_2.text_content().strip(),
                         'url': self._get_link_address(field_2)}

            elif self._parse_detail(key, field_1, field_2):
                value = self._parse_detail(key, field_1, field_2)

            else:
                value = field_2.text_content().strip()

            details[key] = value

        return details

    def parseDataTable(self, table):
        """
        Legistar uses the same kind of data table in a number of
        places. This will return a list of dictionaries using the
        table headers as keys.
        """
        headers = table.xpath(".//th[starts-with(@class, 'rgHeader')]")
        rows = table.xpath(".//tr[@class='rgRow' or @class='rgAltRow']")

        keys = []
        for header in headers:
            text_content = header.text_content().replace('&nbsp;', ' ').strip()
            inputs = header.xpath('.//input')
            if text_content:
                keys.append(text_content)
            elif len(inputs) > 0:
                keys.append(header.xpath('.//input')[0].value)
            else:
                keys.append(header.xpath('.//img')[0].get('alt'))

        for row in rows:
            try:
                data = defaultdict(lambda: None)

                for key, field in zip(keys, row.xpath("./td")):
                    text_content = self._stringify(field)

                    if field.find('.//a') is not None:
                        address = self._get_link_address(field.find('.//a'))
                        if address:
                            if key in ['', 'ics'] and 'View.ashx?M=IC' in address:
                                key = 'iCalendar'
                                value = {'url': address}
                            else:
                                value = {'label': text_content,
                                         'url': address}
                        else:
                            value = text_content
                    else:
                        value = text_content

                    data[key] = value

                yield dict(data), keys, row

            except Exception as e:
                print('Problem parsing row:')
                print(etree.tostring(row))
                print(traceback.format_exc())
                raise e

    def _get_link_address(self, link):
        url = None
        if 'onclick' in link.attrib:
            onclick = link.attrib['onclick']
            if (onclick is not None and
                onclick.startswith(("radopen('",
                                    "window.open",
                                    "OpenTelerikWindow"))):
                onclick_path = onclick.split("'")[1]
                if not onclick_path.startswith("/"):
                    onclick_path = "/" + onclick_path
                url = self.BASE_URL + onclick_path
        elif 'href' in link.attrib:
            url = link.attrib['href']

        return url

    def _parse_detail(self, key, field_1, field_2):
        """
        Perform custom parsing on a given key and field from a detail table.
        Available for override on web scraper base classes.
        """
        return None

    def _stringify(self, field):
        for br in field.xpath("*//br"):
            br.tail = "\n" + br.tail if br.tail else "\n"
        for em in field.xpath("*//em"):
            if em.text:
                em.text = "--em--" + em.text + "--em--"
        return field.text_content().replace('&nbsp;', ' ').strip()

    def toTime(self, text):
        time = datetime.datetime.strptime(text, self.date_format)
        time = pytz.timezone(self.TIMEZONE).localize(time)
        return time

    def toDate(self, text):
        return self.toTime(text).date().isoformat()

    def now(self):
        return datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

    def mdY2Ymd(self, text):
        month, day, year = text.split('/')
        return "%d-%02d-%02d" % (int(year), int(month), int(day))

    def sessionSecrets(self, page):

        payload = {}
        payload['__EVENTARGUMENT'] = None
        payload['__VIEWSTATE'] = page.xpath(
            "//input[@name='__VIEWSTATE']/@value")[0]
        try:
            payload['__EVENTVALIDATION'] = page.xpath(
                "//input[@name='__EVENTVALIDATION']/@value")[0]
        except IndexError:
            pass

        return(payload)


def fieldKey(x):
    field_id = x.attrib['id']
    field = re.split(r'hyp|lbl|Label', field_id)[-1]
    field = field.split('Prompt')[0]
    field = field.rstrip('X21')
    return field