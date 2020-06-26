"""
TITLE: scraper_interface.py
AUTHOR: Amy DiPierro
VERSION: 2020-06-26
USAGE: From the command line, type 'python3 scraper_interface.py'

This script demonstrates a simple scraping pipeline, wherein

1) A CivicPlusSite object is created based on user queries (currently hard-coded)
2) A Document object is created for each document discovered on the CivicPlusSite object
3) The download() function is called on every Document object returned by the user query

Input: A link to a single CivicPlus document (such as an agenda or minutes)
Output: A directory of the form placename-stateorprovincename with a pdf of the document
"""

import civic_plus_site as cps
import document

# Initialize a CivicPlusSite object by passing it a subdomain
cp_site_args = {'subdomain': 'pa-westchester2'}
cp_scraper = cps.CivicPlusSite(**cp_site_args)

# Scrape the provided subdomain to get a list of documents matching specified parameters
cp_scraper_args = {
    'start_date': '20150909',
    'end_date': '20151014'
}
document_list = cp_scraper.scrape(**cp_scraper_args)

# Download each document in the list returned by the CivicPlusSite object
for doc in document_list:
    file = document.Document(doc)
    target_dir = "{}_{}/".format(file.place, file.state_or_province)
    file.download(target_dir)
