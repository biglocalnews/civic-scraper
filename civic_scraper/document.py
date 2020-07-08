import datetime


class Document(object):

    def __init__(
            self,
            url: str,
            doc_name: str = None,
            committee_name: str = None,
            place_name: str = None,
            state_abbr: str = None,
            doc_type: str = None,
            meeting_date: datetime.date = None,
            meeting_time: datetime.time = None,
            doc_format: str = None,
            meeting_id: str = None,
            scraped_by: str = None,
    ):
        """
        Create an instance of the Document class.
        """

        self.url = url
        self.doc_name = doc_name
        self.committee_name = committee_name
        self.place_name = place_name
        self.state_abbr = state_abbr
        self.doc_type = doc_type
        self.meeting_date = meeting_date
        self.meeting_time = meeting_time
        self.doc_format = doc_format
        self.meeting_id = meeting_id
        self.scraped_by = scraped_by

    def download(self, target_path):
        """
        Download the document to target_path.
        """
        # write me!
        raise NotImplementedError

    def append_metadata(self, target_path, write_header=False):
        """
        Append the document metadata in CSV format to target_path.
        If write_header is True, first write a line containing the header
        names. If false, only write one line containing the values.
        """
        # write me!
        raise NotImplementedError


class DocumentList(object):

    def __init__(self, documents):
        self.documents = documents

    def download_documents(self, target_dir):
        """
        Write documents to target_dir
        """
        # write me!
        raise NotImplementedError

    def to_csv(self, target_path):
        """
        Write metadata about the document list to a csv at target_path.
        """
        # write me!
        # this can be a wrapper around Document.append_metadata
        raise NotImplementedError


if __name__ == '__main__':
    import datetime

    # instantiate document
    doc_args = {
        'url': 'https://sanmateocounty.legistar.com/View.ashx?M=A&ID='
            '691905&GUID=86500CA4-50DB-493E-ABCA-1C2446B4B2A6',
        'doc_name': 'Regular Meeting Agenda, Tuesday, Dec. 10, 2019',
        'committee_name': 'San Mateo County Board of Supervisors',
        'place_name': 'San Mateo County',
        'state': 'CA',
        'doc_type': 'agenda',
        'meeting_date': datetime.date(year=2019, month=12, day=10),
        'meeting_time': datetime.time(hour=9),
        'doc_format': 'pdf',
        'meeting_id': 'https://sanmateocounty.legistar.com/View.ashx?M=A&ID='
            '691905&GUID=86500CA4-50DB-493E-ABCA-1C2446B4B2A6',
        'scraped_by': 'legistar-scraper.py_v2020-07-07',
    }
    doc = Document(**doc_args)

    # write document metadata to a csv
    doc.append_metadata('path/to/metadata.csv', write_header=True)

    # download document
    doc.download('path/to/doc_location.pdf')