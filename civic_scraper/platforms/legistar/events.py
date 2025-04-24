import time
import datetime
from collections import deque
import esprima

from .base import LegistarScraper # Use local import to avoid stale dependencies


class LegistarEventsScraper(LegistarScraper):

    ECOMMENT_JS_URLS = (
        'https://metro.granicusideas.com/meetings.js',
        'https://metro.granicusideas.com/meetings.js?scope=past'
    )

    def __init__(self, *args, event_info_key='Meeting Details', **kwargs):
        super().__init__(*args, **kwargs)
        self.event_info_key = event_info_key


    @property
    def ecomment_dict(self):
        """
        Parse event IDs and eComment links from JavaScript file with lines like:
        activateEcomment('750', '138A085F-0AC1-4A33-B2F3-AC3D6D9F710B', 'https://metro.granicusideas.com/meetings/750-finance-budget-and-audit-committee-on-2020-03-16-5-00-pm-test');
        """
        if getattr(self, '_ecomment_dict', None) is None:
            ecomment_dict = {}

            # Define a callback to apply to each node, e.g.,
            # https://esprima.readthedocs.io/en/latest/syntactic-analysis.html#example-console-calls-removal
            def is_activateEcomment(node, metadata):
                if node.callee and node.callee.name == 'activateEcomment':
                    event_id, _, comment_url = node.arguments
                    ecomment_dict[event_id.value] = comment_url.value

            for url in self.ECOMMENT_JS_URLS:
                response = self.get(url)
                esprima.parse(response.text, delegate=is_activateEcomment)

            self._ecomment_dict = ecomment_dict

        return self._ecomment_dict

    def eventPages(self, since):

        page = self.lxmlize(self.EVENTSPAGE)
        for page in self.eventSearch(page, since):
            yield page

    def should_cache_response(self, response):
        # Never cache the top level events page, because that may result in
        # expired .NET state values.
        return (super().should_cache_response(response) and
                response.url != self.EVENTSPAGE)

    def eventSearch(self, page, since):
        payload = self.sessionSecrets(page)

        payload['ctl00_ContentPlaceHolder1_lstYears_ClientState'] = '{"value":"%s"}' % since

        payload['__EVENTTARGET'] = 'ctl00$ContentPlaceHolder1$lstYears'

        return self.pages(self.EVENTSPAGE, payload)

    def events(self, follow_links=True, since=None):
        # If an event is added to the the legistar system while we
        # are scraping, it will shift the list of events down and
        # we might revisit the same event. So, we keep track of
        # the last few events we've visited in order to
        # make sure we are not revisiting
        scraped_events = deque([], maxlen=10)

        current_year = self.now().year

        if since:
            if since > current_year:
                raise ValueError(
                    'Value of :since cannot exceed {}'.format(current_year))
            else:
                since_year = since - 1

        else:
            since_year = 0

        # Anticipate events will be scheduled for the following year to avoid
        # missing upcoming events during scrapes near the end of the current
        # year.
        for year in range(current_year + 1, since_year, -1):
            no_events_in_year = True

            for page in self.eventPages(year):
                events_table = page.xpath("//div[@id='ctl00_ContentPlaceHolder1_MultiPageCalendar']//table[@class='rgMasterTable']")[0]
                for event, _, _ in self.parseDataTable(events_table):
                    # Removing problematic iCalendar scraper
                    # ical_url = event['iCalendar']['url']
                    # if ical_url in scraped_events:
                    #     continue
                    # else:
                    #     scraped_events.append(ical_url)

                    if follow_links and type(event[self.event_info_key]) == dict:
                        agenda = self.agenda(event[self.event_info_key]['url'])
                    else:
                        agenda = None

                    yield event, agenda
                    no_events_in_year = False

            # We scrape events in reverse chronological order, starting one year
            # in the future. Stop scraping if there are no events in a given
            # year, unless that year is in the future, because whether events
            # have been scheduled in the future is not a reliable indication of
            # whether any happened in the previous year.
            if no_events_in_year and year <= current_year:
                break

    def agenda(self, detail_url):
        page = self.lxmlize(detail_url)

        payload = self.sessionSecrets(page)

        payload.update({"__EVENTARGUMENT": "3:1",
                        "__EVENTTARGET": "ctl00$ContentPlaceHolder1$menuMain"})

        for page in self.pages(detail_url, payload):
            agenda_table = page.xpath(
                "//table[@id='ctl00_ContentPlaceHolder1_gridMain_ctl00']")[0]
            agenda = self.parseDataTable(agenda_table)
            yield from agenda

    def addDocs(self, e, events, doc_type):
        try:
            if events[doc_type] != 'Not\xa0available':
                e.add_document(note=events[doc_type]['label'],
                               url=events[doc_type]['url'],
                               media_type="application/pdf")
        except ValueError:
            pass

    def extractRollCall(self, action_detail_url):
        action_detail_page = self.lxmlize(action_detail_url)
        try:
            rollcall_table = action_detail_page.xpath(
                "//table[@id='ctl00_ContentPlaceHolder1_gridRollCall_ctl00']")[0]
        except IndexError:
            self.warning("No rollcall found in table")
            return []
        roll_call = list(self.parseDataTable(rollcall_table))
        call_list = []
        for call, _, _ in roll_call:
            option = call['Attendance']
            call_list.append((option,
                              call['Person Name']['label']))

        return call_list

    def ical(self, ical_text):
        value = icalendar.Calendar.from_ical(ical_text)
        return value

    def _parse_detail(self, key, field_1, field_2):
        if key == 'eComment':
            return self._get_ecomment_link(field_2) or field_2.text_content().strip()

    def _get_ecomment_link(self, link):
        event_id = link.attrib['data-event-id']
        return self.ecomment_dict.get(event_id, None)