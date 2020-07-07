"""
TITLE: Document
AUTHOR: Amy DiPierro
VERSION: 2020-06-26
USAGE: From the command line, type 'python3 civic_plus_document.py' followed by link.

The code here creates a Document object. Document objects have one public method at
present: download(target_dir).

The script can be run from the command line as follows:

    python3 civic_plus_document.py link

where link is a URL or series of URLs separated by spaces.

Example calls:

    python3 civic_plus_document.py https://pa-westchester2.civicplus.com/AgendaCenter/ViewFile/Agenda/_10132015-240
    python3 civic_plus_document.py https://pa-westchester2.civicplus.com/AgendaCenter/ViewFile/Agenda/_10132015-240 https://pa-westchester2.civicplus.com/AgendaCenter/ViewFile/Agenda/_09162015-228

Input: A link to a single CivicPlus document (such as an agenda or minutes)
Output: A directory of the form placename-stateorprovincename with a pdf of the document
"""
import re
import requests
import os.path

class CivicPlusDocument:

    def __init__(self, link):
        """
        Creates a Document object
        """
        self.link = link
        self.place = self._get_doc_metadata(r"(?<=-)\w+(?=\.)")
        self.state_or_province = self._get_doc_metadata(r"(?<=//)\w{2}(?=-)")
        self.date = self._get_doc_metadata(r"(?<=_)\w{8}(?=-)")
        self.doc_type = self._get_doc_metadata(r"(?<=e/)\w+(?=/_)")
        self.meeting_id = self._get_doc_metadata(r"(?<=/_).+$")
        self.scraper = 'civicplus'
        self.doc_format = 'pdf'

    def download(self, target_dir=None):
        """
        Downloads a document into a target directory.

        Input: Target directory name (target_dir)
        Output: pdf of document in target directory
        """
        file_name = "{}_{}_{}_{}.pdf".format(self.place, self.state_or_province, self.doc_type, self.meeting_id)
        document = self.link
        if document != 'no_doc_links':
            print("Downloading document: ", document)
            response = requests.get(document, allow_redirects=True)
            if not os.path.isdir(target_dir):
                print("Making directory...")
                os.mkdir(target_dir)
            full_path = os.path.join(target_dir, file_name)
            open(full_path, 'wb').write(response.content)

    # Private methods

    def _get_doc_metadata(self, regex):
        """
        Extracts metadata from a provided document URL.

        Input: Regex to extract metadata
        Returns: Extracted metadata as a string or "no_data" if no metadata is extracted
        """
        try:
            return re.search(regex, self.link).group(0)
        except AttributeError as error:
            return "no_data"

if __name__ == '__main__':
    import sys
    import os
    for index in range(1, len(sys.argv)):
        link = sys.argv[index]
        document = Document(link=link)
        document.download(target_dir=os.getcwd())
