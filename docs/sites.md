# Sites

The csv **sites_civicplus.csv** contains the following fields:

`end_point`: *(str)* The url of the CivicPlus Agenda Center website to be scraped, e.g., http://ct-greenwich.civicplus.com/AgendaCenter.

`begin_year`: *(int)* The earliest year of any asset posted on this endpoint, e.g., 1998. **NOTE:** When the value of this field is 1899, this is an error
              caused by the way the endpoint works under the hood.

`end_year`: *(int)* The most-recent year of any asset posted on this endpoint, e.g., 2020.

`scraper_type`: *(str)* The name of the scraper used on this endpoint, e.g., civicplus.

`whitelisted`: *(bool)* `TRUE` if we are currently scraping the endpoint, `FALSE` otherwise.

`name`: *(str)* The name of the agency being scraped, e.g., Greenwich. This field is derived from subdomain of the website, but is sometimes
        hand-keyed in the case that the subdomain is not very descriptive, contains an acronym or contains multiple words.

`state`: *(str)* The two-letter abbreviation of the state where the agency being scraped is located, e.g., CT.

`country`: *(str)* The country where the agency being scraped is located. Possible values are "USA" and "CANADA".

`govt_level`: *(str)* The level of governement of the agency. Possible values are "Municipality", "County" or "Other". Some values are hand-keyed
              following a review of agencies categorized as "Other."

`meeting_bodies`: *(str)* A list of all of the agencies available to be scraped from the endpoint.
