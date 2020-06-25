"""
TITLE: CivicPlusSite
AUTHOR: Amy DiPierro
VERSION: 2020-06-24
USAGE: From the command line type 'python3 civic_plus_site.py subdomain begin_date end_date'
        where a subdomain is a string corresponding to the first
        portion of each subdomain and begin_date and end_date are written in the
        form yyyymmdd. All three items are required.

Example calls:
    python3 civic_plus_site.py id-kuna 20190101 202006030
    python3 civic_plus_site.py ga-savannah 20190101 20200101

This script scrapes agendas and minutes from CivicPlus Agenda Center websites.
It is an object-oriented rewrite of civicplus.py

Output: pdfs of documents

"""
# Libraries

import logging
import bs4
import requests
from retrying import retry
import re

#TODO: Get logger to work
logger = logging.getLogger(__name__)

class CivicPlusSite:
    """
    In its current configuration, the CivicPlusSite object downloads all documents
    from a given website in a given date range.
    """

    base_url = "civicplus.com/AgendaCenter"

    def __init__(self, subdomain, begin_date, end_date):
        self.url = "https://{}.{}".format(subdomain, self.base_url)
        self.begin_date = begin_date
        self.end_date = end_date

    # Public interface (used by calling code)
    def scrape(self):
        logger.info("START SCRAPE - {}".format(self.url))
        html = self._get_html()
        soup = self._make_soup(html)
        post_params = self._get_post_params(soup)
        document_stubs = self._get_all_docs(post_params)
        filtered_stubs = self._filter_docs(document_stubs, begin_date, end_date)
        document_links = self._make_document_links(filtered_stubs)
        metadata = self._get_metadata_dict(document_links)
        self.download_documents(metadata)
        logger.info("END SCRAPE - {}".format(self.url))

    # Private methods (used by the class itself)

    @retry(
        stop_max_attempt_number=3,
        stop_max_delay=30000,
        wait_exponential_multiplier=1000,
        wait_exponential_max=10000
    )
    def _get_html(self):
        """
        Get HTML response.

        Input: Link of the website we want to scrape.
        Returns: HTML of the website as text.
        """
        try:
            response = requests.get(self.url)
            return response.text
        except:
            print("The url could not be reached.")
            return ""

    def _make_soup(self, html):
        """
        Parses the text we've collected

        Input: Text of website
        Returns: Parsed text
        """
        return bs4.BeautifulSoup(html, 'html.parser')

    def _get_post_params(self, soup):
        """
        Given parsed html text grabs the bits of html -- a year and a cat_id -- needed
        for the POST request.

        Input: Parsed text
        Returns: A dictionary of years and cat_ids
        """
        # Make the dictionary
        year_elements = soup.find_all(href=re.compile("changeYear"))
        years_cat_id = {}
        cat_ids = []
        for element in year_elements:
            link = element.attrs['href']
            year = re.search(r"(?<=\()\d{4}(?=,)", link).group(0)
            cat_id = re.findall(r"\d+(?=,.*')", link)[1]
            cat_ids.append(cat_id)
            years_cat_id[year] = cat_ids

        # Remove duplicates
        years_cat_id_2 = {}
        cat_ids_2 = []
        for year in years_cat_id:
            id_list = years_cat_id[year]
            for id in id_list:
                if id not in cat_ids_2:
                    cat_ids_2.append(id)
            years_cat_id_2[year] = cat_ids_2

        return years_cat_id_2

    @retry(
        stop_max_attempt_number=3,
        stop_max_delay=30000,
        wait_exponential_multiplier=1000,
        wait_exponential_max=10000
    )

    def _get_all_docs(self, post_params):
        """
        Given a dictionary and page URL, makes a post request and harvests all of the links from
        the response to that request.

        Input: Dictionary of years and catIDs, page URL for POST request
        Returns: A dictionary of years and catIDs
        """
        page = "{}/UpdateCategoryList".format(self.url)
        # Get links
        all_links = []
        for year in post_params:
            ids = post_params[year]
            for cat_id in ids:
                payload = {'year': year, 'catID': cat_id, 'term': '', 'prevVersionScreen': 'false'}
                try:
                    response = requests.post(page, params=payload)
                    soup = self._make_soup(response.text)
                    end_links = self._get_links(soup)
                    all_links.append(end_links)
                except:
                    print("In get_all_docs: The POST request failed.")

        return end_links

    def _get_links(self, soup):
        """
        Make a list of links to documents we want to download

        Input: Parsed text of website
        Returns: The latter portion of links to documents to download
        """

        links = soup.table.find_all('a')
        end_links = []
        for link in links:
            if '/Agenda/' or '/Minutes/' in link.attrs['href']:
                end_links.append(link.get('href'))
                end_links = list(filter(None, end_links))
                for end_link in end_links:
                    if ('true' in end_link) or ('http' in end_link) or ('Previous' in end_link) or (
                            'DocumentCenter' in end_link):
                        end_links.remove(end_link)

        return end_links

    def _filter_docs(self, document_stubs, begin_date, end_date):
        # Filter the docs by date
        filtered_stubs = []
        for stub in document_stubs:
            month = re.search(r"(?<=_)\d{2}(?=\d{6}-)", stub).group(0)
            day = re.search(r"(?<=_\d{2})\d{2}(?=\d{4}-)", stub).group(0)
            year = re.search(r"(?<=\d)\d{4}(?=-)", stub).group(0)
            date = int("{}{}{}".format(year, month, day))
            if int(begin_date) <= date <= int(end_date):
                filtered_stubs.append(stub)

        return filtered_stubs



    def _get_metadata_dict(self, document_links):
        """
        Creates a dictionary of metadata from the link of each document URL, then
        writes this metadata dictionary to a csv.

        Input: A list of document URLs
        Returns: A dictionary of metadata
        Output: A csv
        """

        # Make the metadata dictionary

        meta = {}
        place_list = []
        state_or_province_list = []
        date_list = []
        doc_type_list = []
        meeting_id_list = []
        url_list = []
        scraper_list = []
        doc_format_list = []

        if len(document_links) > 0:

            for document in document_links:
                meta = self._get_metadata('place', document, r"(?<=-)\w+(?=\.)", place_list, meta)
                meta = self._get_metadata('state_or_province', document, r"(?<=//)\w{2}(?=-)", state_or_province_list,
                                    meta)
                meta = self._get_metadata('date', document, r"(?<=_)\w{8}(?=-)", date_list, meta)
                meta = self._get_metadata('doc_type', document, r"(?<=e/)\w+(?=/_)", doc_type_list, meta)
                meta = self._get_metadata('meeting_id', document, r"(?<=/_).+$", meeting_id_list, meta)

                url_list.append(document)
                meta['url'] = url_list

                scraper_list.append('civicplus')
                meta['scraper'] = scraper_list

                doc_format_list.append('pdf')
                meta['doc_format'] = doc_format_list

        else:
            meta['place'] = ['no_doc_links']
            meta['state_or_province'] = ['no_doc_links']
            meta['date'] = ['no_doc_links']
            meta['doc_type'] = ['no_doc_links']
            meta['meeting_id'] = ['no_doc_links']
            meta['url'] = ['no_doc_links']
            meta['scraper'] = ['civicplus']
            meta['doc_format'] = ['pdf']

        return meta

    def _make_document_links(self, document_stubs):
        """
        Combines a base URL and a list of partial document links (document_stubs)
        to make full urls.

        Input: A base URL and a list of partial document links (document_stubs)
        Returns: A list of full URLs
        """
        url_list = []

        for stub in document_stubs:
            stub = stub.replace("/AgendaCenter", "")
            text = "{}{}".format(self.url, stub)
            url_list.append(text)

        return url_list


    # TODO: Consider other uses for this metadata
    def _get_metadata(self, key, document, regex, list, meta):
        """
        Performs error handling in the case that certain metadata elements are not extractable from a given URL.

        Input: Elements needed to extract metadata
        Returns: A dictionary
        """
        try:
            item = re.search(regex, document).group(0)
            list.append(item)
            meta[key] = list
            return meta
        except AttributeError as error:
            print("AttributeError in get_metadata.")
            missing_field = "no_{}".format(key)
            list.append(missing_field)
            meta[key] = list
            return meta

    def download_documents(self, metadata):
        """
        Downloads documents discovered by the previous functions

        Input: The metadata dictionary
        Output: .pdfs of each document
        """

        places = metadata['place']
        state_or_provinces = metadata['state_or_province']
        meeting_ids = metadata['meeting_id']
        documents = metadata['url']
        doc_types = metadata['doc_type']

        for index in range(len(documents)):
            file_name = "{}_{}_{}_{}.pdf".format(places[index], state_or_provinces[index], doc_types[index], meeting_ids[index])
            document = documents[index]
            if document != 'no_doc_links':
                print("Downloading document: ", document)
                response = requests.get(document, allow_redirects=True)
                open(file_name, 'wb').write(response.content)

if __name__ == '__main__':
    import sys
    subdomain = sys.argv[1]
    begin_date = sys.argv[2]
    end_date = sys.argv[3]
    site = CivicPlusSite(subdomain, begin_date, end_date)
    site.scrape()

