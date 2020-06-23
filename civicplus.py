"""
TITLE: CivicPlus Scraper
AUTHOR: Amy DiPierro
VERSION: 2020-06-23
USAGE: From the command line type 'python3 civicplus.py'

This script scrapes agendas and minutes from CivicPlus Agenda Center websites.

Input: .csv of CivicPlus URLs.
Output: .csv of metadata related to documents available for download, downloaded .pdfs

"""
# Libraries

import bs4
import requests
import re
import pandas as pd
from os import path

# Constants

CIVICPLUS_URLS = 'civicplus_urls.csv'
DOCUMENTS = 'aw-data-documents.csv'

# Code

def main():
    """
    Run this entire script.
    """

    url_list = get_url_list(CIVICPLUS_URLS)
    page_list = get_page_list(url_list)
    for i in range(len(url_list)):
        url = url_list[i]
        print("url: ", url)
        url_html = get_root(url)
        url_soup = make_soup(url_html)
        years_ids = get_years_ids(url_soup)
        page = page_list[i]
        document_stubs = get_all_docs(years_ids, page)
        document_links = make_document_links(url, document_stubs)
        write_to_csv(document_links)
        download_documents(document_links)

def get_url_list(csv):
    """
    Opens a .csv of CivicPlus URLs, reads them in line by line, formats them
    and returns a list of URLs.

    Input: A .csv
    Returns: A list
    """
    url_list = []
    with open(csv, 'r') as file:
        next(file)
        for line in file.readlines():
            url = "https://{}/AgendaCenter".format(line.strip().split(',')[0])
            url_list.append(url)

    return url_list

def get_page_list(url_list):
    """
    Given a list of URLs, reformats them for the crawler.

    Input: A list
    Returns: A new list
    """
    page_list = []
    for url in url_list:
        page_url = "{}/UpdateCategoryList".format(url)
        page_list.append(page_url)
    return page_list

def get_root(url):
    """
    Get the root URL link.

    Input: Link of the website we want to scrape.
    Returns: HTML of the website as text.
    """
    try:
        response = requests.get(url)
        return response.text
    except:
        print("The url ", url, " timed out.")
        return " "

def make_soup(html):
    """
    Parses the text we've collected

    Input: Text of website
    Returns: Parsed text
    """
    return bs4.BeautifulSoup(html, 'html.parser')

def get_years_ids(soup):
    """
    Given parsed html text grabs the bits of html -- a year and a catID -- needed
    for the POST request.

    Input: Parsed text
    Returns: A dictionary of years and catIDs
    """
    # Make the dictionary
    year_elements = soup.find_all(href=re.compile("changeYear"))
    years_catID = {}
    catIDs = []
    for element in year_elements:
        link = element.attrs['href']
        year = re.search(r"(?<=\()20\d{2}(?=,)", link).group(0)
        catID = re.findall(r"\d+(?=,.*')", link)[1]
        catIDs.append(catID)
        years_catID[year] = catIDs

    # Remove duplicates
    years_catID_2 = {}
    catIDs_2 = []
    for year in years_catID:
        id_list = years_catID[year]
        for id in id_list:
            if id not in catIDs_2:
                catIDs_2.append(id)
        years_catID_2[year] = catIDs_2

    return years_catID_2

def get_all_docs(years_ids, page):
    """
    Given a dictionary and page URL, makes a post request and harvests all of the links from
    the response to that request.

    Input: Dictionry of years and catIDs, page URL for POST request
    Returns: A dictionary of years and catIDs
    """
    # Get links
    all_links = []
    for year in years_ids:
        ids = years_ids[year]
        for id in ids:
            payload = {'year': year, 'catID': id, 'term': '', 'prevVersionScreen': 'false'}
            response = requests.post(page, params=payload)
            soup = make_soup(response.text)
            end_links = get_links(soup)
            all_links.append(end_links)

    # Remove lists for which no links have been found
    for list in all_links:
        if list == []:
            all_links.remove(list)

    return all_links

def get_links(soup):
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
                if ('true' in end_link) or ('http' in end_link) or ('Previous' in end_link) or ('DocumentCenter' in end_link):
                    end_links.remove(end_link)

    return end_links

def make_document_links(url, document_stubs):
    """
    Combines a list of base URLs and a list of partial document links (document_stubs)
    to make full urls.

    Input: A list of URLs and a list of partial document links (document_stubs)
    Returns: A list of full URLs
    """
    url_list = []

    for document_list in document_stubs:
        for stub in document_list:
            stub = stub.replace("/AgendaCenter", "")
            text = "{}{}".format(url, stub)
            url_list.append(text)

    return url_list

def write_to_csv(document_links):
    """
    Creates a dictionary of metadata from the link of each document URL, then
    writes this metadata dictionary to a csv.

    Input: A list of document URLs
    Output: A csv
    """

    # Make the metadata dictionary

    dict = {}
    place_list = []
    state_or_province_list = []
    date_list = []
    doc_type_list = []
    meeting_id_list = []
    url_list = []
    scraper_list = []
    doc_format_list = []

    for document in document_links:
        dict = get_metadata('place', document, r"(?<=-)\w+(?=\.)", place_list, dict)
        dict = get_metadata('state_or_province', document, r"(?<=//)\w{2}(?=-)", state_or_province_list, dict)
        dict = get_metadata('date', document,r"(?<=_)\w{8}(?=-)", date_list, dict)
        dict = get_metadata('doc_type', document, r"(?<=e/)\w+(?=/_)", doc_type_list, dict)
        dict = get_metadata('meeting_id', document, r"(?<=/_).+$", meeting_id_list, dict)

        url_list.append(document)
        dict['url'] = url_list

        scraper_list.append('civicplus')
        dict['scraper'] = scraper_list

        doc_format_list.append('pdf')
        dict['doc_format'] = doc_format_list

    # Write the dictionary to a .csv

    if path.exists(DOCUMENTS):
        pd.DataFrame.from_dict(data=dict).to_csv(DOCUMENTS, mode='a', header=False)
    else:
        pd.DataFrame.from_dict(data=dict).to_csv(DOCUMENTS, header=True)

def get_metadata(key, document, regex, list, dict):
    """
    Performs error handling in the case that certain metadata elements are not extractable from a given URL.
    
    Input: Elements needed to extract metadata
    Returns: A dictionary 
    """
    try:
        item = re.search(regex, document).group(0)
        list.append(item)
        dict[key] = list
        return dict
    except AttributeError as error:
        print("AttributeError in get_metadata.")
        missing_field = "no_{}".format(key)
        list.append(missing_field)
        dict[key] = list
        return dict

def download_documents(document_links):
    """
    Downloads documents discovered by the previous functions

    Input: A list of URLs to documents
    Output: .pdfs of each document
    """
    for document in document_links:
        place = re.search(r"(?<=-)\w+(?=\.)", document).group(0)
        state_or_province = re.search(r"(?<=//)\w{2}(?=-)", document).group(0)
        meeting_id = re.search(r"(?<=/_).+$", document).group(0)
        file_name = "{}_{}_{}.pdf".format(place, state_or_province, meeting_id)
        response = requests.get(document, allow_redirects=True)
        open(file_name, 'wb').write(response.content)

if __name__ == "__main__":
    main()
