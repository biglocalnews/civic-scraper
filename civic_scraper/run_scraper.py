"""
TITLE: run_scraper.py
AUTHOR: Chris Stock
VERSION: 2020-07-08
DESCRIPTION:
Given a scraper type, an endpoint, and possibly scraping arguments,
this script collects a list of documents on the site and writes
that list as a csv to a specified path.

USAGE:
Within Python:
doc_list = run_scraper(
    scraper_type='civicplus',
    endpoint='http://pa-westchester2.civicplus.com/AgendaCenter',
    scraper_args={"start_date": "20150909", "end_date": "20151014"},
    target_path='path/to/target.csv'
)

From the command line:
python run_scraper.py \
    civicplus \
    http://pa-westchester2.civicplus.com/AgendaCenter \
    path/to/target.csv \
    --scraper_args {\"start_date\": \"20150909\", \"end_date\": \"20151014\"}
"""

import json
from civic_scraper.scrapers import SUPPORTED_SCRAPERS


def run_scraper(
        scraper_type: str,
        endpoint: str,
        target_path: str,
        scraper_args: dict = None,
    ):
    """
    Run a specified scraper on a specified site, possibly with arguments,
    and write the resulting document list as a csv to a specified path

    Args:
        scraper_type: the type of scraper ('legistar', 'civicplus')
        endpoint: the endpoint
            ('http://pa-westchester2.civicplus.com/AgendaCenter')
        target_path: the location to write the csv of results to
            ('path/to/target.csv')
        scraper_args: a dict of additonal args to pass to Site.scrape()
            ({"start_date": "20150909", "end_date": "20151014"})

    Returns:
        a DocumentList instance of the retrieved documents
    """
    # process arguments
    scraper_args = {} if scraper_args is None else scraper_args

    # instantiate the specified scraper
    try:
        scraper = SUPPORTED_SCRAPERS[scraper_type]
    except KeyError:
        raise ValueError('Unable to instantiate scraper: '
                         '{}'.format(scraper_type))
    site = scraper(endpoint)

    # scrape the specified site
    try:
        doc_list = site.scrape(**scraper_args)
    except Exception:
        raise Exception('Unable to scrape with args: '
                        '{}'.format(scraper_args))

    # write results to the specified file location
    try:
        doc_list.to_csv(target_path)
    except Exception:
        raise Exception('Unable to write document list to path: '
                        '{}'.format(target_path))
    return doc_list

if __name__ == '__main__':
    """
    Call run_scraper from the command line.
    """

    # parse arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'scraper_type',
        type=str
    )
    parser.add_argument(
        'endpoint',
        type=str,
    )
    parser.add_argument(
        'target_path',
        type=str,
    )
    parser.add_argument(
        '--scraper_args',
        type=json.loads,  # imports a dict from escaped JSON
        default={},
    )
    args = parser.parse_args()

    # call function
    document_list = run_scraper(
        scraper_type=args.scraper_type,
        endpoint=args.endpoint,
        target_path=args.target_path,
        scraper_args=args.scraper_args,
    )

