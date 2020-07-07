# civic-scraper

Scraper to download civic documents from local government websites.

## CivicPlusSite

* download_csv(): Produces a csv file in which every row corresponds to a document. It has the following fields
  * place (str) - The place name that forms the second part of the domain name after the "-", e.g., "oakbluffs".
  * state_or_province (str) - The abbreviation of a state or province that forms first part of the domain name before the "-", e.g., "ma". 
  * meeting_date (str) - The date a meeting was held in the form "mmddyyyy"
  * committee - The name of the committee that held a meeting. Currently hardcoded to `None` because of difficulty scraping this data
  * doc_format (str) - The file format of the document available for download. Hardcoded to "pdf"
  * meeting_id (str) - The meeting_id that associates an agenda with corresponding minutes. It follows the format "mmddyyyy-xxxx" where xxxx is a sequence of four numbers. It is extracted from the document URL.
  * site_type (str) - The type of website we're scraping. Hardcoded to "civicplus"
  * doc_type (str) - The type of document available for download. Either "Minutes" or "Agenda"
  * url (str) - The url of the document to download.
  
