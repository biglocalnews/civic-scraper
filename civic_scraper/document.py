import datetime


class Document(object):

    def __init__(
            self,
            url: str,
            doc_name: str = None,
            committee_name: str = None,
            place_name: str = None,
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


class DocumentList(object):

    def __init__(self, documents):
        self.documents = documents

    def download_documents(self, target_dir):
        """
        Write documents to target_dir
        """
        # write me!
        raise NotImplementedError

    def download_metadata(self, target_path):
        """
        Download metadata about the document list to a csv at target_path.
        """
        # write me!
        raise NotImplementedError

