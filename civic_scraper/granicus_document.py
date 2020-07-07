"""
TITLE: Granicus Document
AUTHOR: Amy DiPierro
VERSION: 2020-07-07
USAGE: From the command line, type 'python3 granicus_document.py' followed by link.

The code here creates a GranicusDocument object. Document objects have one public method at
present: download(target_dir).

The script can be run from the command line as follows:

    python3 granicus_document.py

Then enter a link of one of these formats when prompted:

    //ashland-va.granicus.com/AgendaViewer.php?view_id=1&clip_id=19
    http://archive-media.granicus.com:443/OnDemand/ashland-va/ashland-va_dc46642e-f31c-4a7e-8ae0-28c656ba9d58.mp4

Input: A link to a single Granicus document (such as an agenda or minutes)
Output: A directory named according to the domain with a pdf of the document
"""
import re
import requests
import os.path
import string

class GranicusDocument:

    def __init__(self, link):
        """
        Creates a Document object
        """
        
        if re.search(r"Agenda", link) != None:
            self.link = link
            self.doc_type = "agenda"
            self.doc_format = ".pdf"
        elif re.search(r"Minutes", link) != None:
            self.link = link
            self.doc_type = "minutes"
            self.doc_format = ".pdf"
        elif re.search(r"mp3", link) != None:
            self.link = link
            self.doc_type = "audio"
            self.doc_format = ".mp3"
        elif re.search(r"mp4", link) != None:
            self.link = link
            self.doc_type = "video"
            self.doc_format = ".mp4"
        else:
            self.link = None
            self.doc_type = "embedded_video"
            self.doc_format = "html"
        
        self.scraper = 'granicus'


    def download(self, target_dir=None):
        """
        Downloads a document into a target directory.

        Input: Target directory name (target_dir)
        Output: pdf of document in target directory
        """
        url = str(self.link).translate(str.maketrans('', '', string.punctuation))
        file_txt = "{}.txt".format(url)
        file_html = "{}.html".format(url)
        file_av = "{}{}".format(url, self.doc_format)

        if re.search(r"http:", self.link) == None:
            document = "http:{}".format(self.link)
        else:
            document = self.link
        
        if document != None:
            print("Downloading document: ", document)
            response = requests.get(document, allow_redirects=True)
            if not os.path.isdir(target_dir):
                print("Making directory...")
                os.mkdir(target_dir)
            if self.doc_type == ("agenda" or "minutes"):
                 full_txt = os.path.join(target_dir, file_txt)
                 open(full_txt, 'wb').write(response.content)
                 full_html = os.path.join(target_dir, file_html)
                 open(full_html, 'wb').write(response.content)
            else:
                full_path = os.path.join(target_dir, file_av)
                open(full_path, 'wb').write(response.content)

if __name__ == '__main__':
    import os
    link = input("Enter link: ")
    document = GranicusDocument(link=link)
    document.download(target_dir=os.getcwd())
