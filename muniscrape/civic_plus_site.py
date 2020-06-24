
class CivicPlusSite:

    base_url = "civicplus.com"

    def __init__(self, subdomain):
        self.url = "{}.{}".format(subdomain, self.base_url)

    # Public interface (used by calling code)
    def scrape(self):
        print("Scraping away: {}!!!".format(self.url))
        # Call private methods here
        #self._get_all_years()


    # Private methods (used by the class iteslf)

    def _get_all_years(self):
        # AgendaCenter
        print("Called _get_all_years")

    def _get_metadata(self):
        if self._metadata:
            return self._metadata
        #TODO: replace with code that 
        # generates metadata and returns
        # the dictionary
        self._metadata = {}
        return self._metadata
        pass

    def _write_metadata_csv(self):
        #TODO: Generate CSV using self._get_metadata()
        pass

if __name__ == '__main__':
    import sys
    subdomain = sys.argv[1]
    site = CivicPlusSite(subdomain)
    site.scrape()
