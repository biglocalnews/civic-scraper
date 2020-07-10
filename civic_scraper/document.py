import datetime
import csv
import requests
import os

class Document(object):

    def __init__(
            self,
            url: str,
            doc_name: str = None,
            committee_name: str = None,
            place: str = None,
            state_or_province: str = None,
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
        self.place = place
        self.state_or_province = state_or_province
        self.doc_type = doc_type
        self.meeting_date = meeting_date
        self.meeting_time = meeting_time
        self.doc_format = doc_format
        self.meeting_id = meeting_id
        self.scraped_by = scraped_by

    def download(self, target_path=os.getcwd()):
        """
        Downloads a document into a target directory.

        Input: Target directory name (target_path)
        Output: pdf of document in target directory
        """
        file_name = "{}_{}_{}_{}.pdf".format(self.place, self.state_or_province, self.doc_type, self.meeting_date)
        document = self.url
        print("Downloading document: ", document)
        try:
            response = requests.get(document, allow_redirects=True)
            if not os.path.isdir(target_path):
                print("Making directory...")
                os.mkdir(target_path)
            full_path = os.path.join(target_path, file_name)
            open(full_path, 'wb').write(response.content)
        except:
            print(self.url)
            print("Download failed.")

    def append_metadata(self, target_path=os.getcwd(), write_header=False):
        """
        Append the document metadata in CSV format to target_path.
        If write_header is True, first write a line containing the header
        names. If false, only write one line containing the values.
        """
        # Make the dictionary
        metadata_dict = {
            'place': self.place,
            'state_or_province': self.state_or_province,
            'meeting_date': self.meeting_date,
            'meeting_time': self.meeting_time,
            'committee_name': self.committee_name,
            'doc_format': self.doc_format,
            'meeting_id': self.meeting_id,
            'doc_type': self.doc_type,
            'url': self.url,
            'scraped_by': self.scraped_by
        }

        # Initializing the .csv
        file_name = "{}-{}.csv".format(self.place, self.state_or_province)
        full_path = os.path.join(target_path, file_name)
        file = open(full_path, 'a')

        # Writing the .csv
        with file:
            dict_writer = csv.DictWriter(file, metadata_dict.keys())
            if write_header:
                dict_writer.writeheader()
            if self.url is not None:
                dict_writer.writerow(metadata_dict)

class DocumentList(object):

    def __init__(self, documents):
        self.documents = documents

    def download_documents(self, target_path=os.getcwd()):
        """
        Write documents to target_path
        """
        for item in self.documents:
            document = Document(**item)
            document.download()

<<<<<<< HEAD
    def to_csv(self, target_path):
=======
    def write_metadata(self, target_path=os.getcwd()):
>>>>>>> master
        """
        Write metadata about the document list to a csv at target_path.
        """
        for index in range(len(self.documents)):
            # print(self.documents[index])
            document = Document(**self.documents[index])
            if index == 0:
                document.append_metadata(write_header=True)
            document.append_metadata()


if __name__ == '__main__':
    import datetime
    import granicus_site as gs
    import civic_plus_site as cps

    site = cps.CivicPlusSite(subdomain="pa-westchester2")
    metadata = site.scrape(start_date="20200601", end_date="20200801")

    civic_plus = DocumentList(metadata)
    civic_plus.to_csv()

    civic_plus.download_documents()

    # site = gs.GranicusSite(subdomain="sanmateocounty")
    # metadata = site.scrape(start_date="20200601", end_date="20200801")
    #
    # granicus = DocumentList(metadata)
    # granicus.write_metadata()
    #
    # granicus.download_documents()

    # instantiate document
    # doc_args = {
    #     'url': 'https://sanmateocounty.legistar.com/View.ashx?M=A&ID='
    #         '691905&GUID=86500CA4-50DB-493E-ABCA-1C2446B4B2A6',
    #     'doc_name': 'Regular Meeting Agenda, Tuesday, Dec. 10, 2019',
    #     'committee_name': 'San Mateo County Board of Supervisors',
    #     'place': 'San Mateo County',
    #     'state_or_province': 'CA',
    #     'doc_type': 'agenda',
    #     'meeting_date': datetime.date(year=2019, month=12, day=10),
    #     'meeting_time': datetime.time(hour=9),
    #     'doc_format': 'pdf',
    #     'meeting_id': 'https://sanmateocounty.legistar.com/View.ashx?M=A&ID='
    #         '691905&GUID=86500CA4-50DB-493E-ABCA-1C2446B4B2A6',
    #     'scraped_by': 'legistar-scraper.py_v2020-07-07',
    # }
    #
    # doc = Document(**doc_args)
    #
    # # write document metadata to a csv
    # # doc.append_metadata(write_header=True)
    #
    # # download document
    # # doc.download()
    #
    # docs_args = [{
    #     'url': 'https://sanmateocounty.legistar.com/View.ashx?M=A&ID='
    #         '691905&GUID=86500CA4-50DB-493E-ABCA-1C2446B4B2A6',
    #     'doc_name': 'Regular Meeting Agenda, Tuesday, Dec. 10, 2019',
    #     'committee_name': 'San Mateo County Board of Supervisors',
    #     'place': 'San Mateo County',
    #     'state_or_province': 'CA',
    #     'doc_type': 'agenda',
    #     'meeting_date': datetime.date(year=2019, month=12, day=10),
    #     'meeting_time': datetime.time(hour=9),
    #     'doc_format': 'pdf',
    #     'meeting_id': 'https://sanmateocounty.legistar.com/View.ashx?M=A&ID='
    #         '691905&GUID=86500CA4-50DB-493E-ABCA-1C2446B4B2A6',
    #     'scraped_by': 'legistar-scraper.py_v2020-07-07',
    # }, {
    #     'url': 'https://sanmateocounty.legistar.com/View.ashx?M=A&ID='
    #         '691905&GUID=86500CA4-50DB-493E-ABCA-1C2446B4B2A6',
    #     'doc_name': 'Regular Meeting Agenda, Tuesday, Dec. 10, 2019',
    #     'committee_name': 'San Mateo County Board of Supervisors',
    #     'place': 'San Mateo County',
    #     'state_or_province': 'CA',
    #     'doc_type': 'agenda',
    #     'meeting_date': datetime.date(year=2019, month=12, day=10),
    #     'meeting_time': datetime.time(hour=9),
    #     'doc_format': 'pdf',
    #     'meeting_id': 'https://sanmateocounty.legistar.com/View.ashx?M=A&ID='
    #         '691905&GUID=86500CA4-50DB-493E-ABCA-1C2446B4B2A6',
    #     'scraped_by': 'legistar-scraper.py_v2020-07-07',
    # }]
    #
    # docs = DocumentList(docs_args)
    #
    # docs.write_metadata()
    #
    # docs.download_documents()