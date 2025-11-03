from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
import json

HEADERS = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Connection": "keep-alive",
        }



def read_website_html(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.text
    else:   
        return None

def get_div_by_class(html_code, class_name):
    soup = BeautifulSoup(html_code, 'html.parser')
    div_tag = soup.find('div', id=class_name)
    if div_tag:
        #print(div_tag)
        return str(div_tag)
    else:
        print("Returning None")
        return None


def parse_meeting_rows(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    meetings = []
    for row in soup.select("tr.meeting-row"):
        meeting = {}
        for td in row.find_all("td"):
            sortable_type = td.get("data-sortable-type")
            if sortable_type == "mtgName":
                meeting["meeting_name"] = td.get_text(strip=True)
            elif sortable_type == "mtgType":
                meeting["meeting_type"] = td.get_text(strip=True)
            elif sortable_type == "mtgTime":
                meeting["meeting_datetime"] = td.get_text(strip=True)
        # Extract links (Agenda, PDF, Media, etc.) from all <a> tags in the row
        links = []
        for a in row.find_all("a", href=True):
            links.append({
                "text": a.get_text(strip=True),
                "url": urljoin(base_url, a["href"])
            })
        meeting["links"] = links

        meetings.append(meeting)
    return meetings

urls = [
    "https://agendaonline.mymanatee.org/OnBaseAgendaOnline/Meetings/Search?dropid=11&mtids=107&dropsv=01%2F01%2F2021%2000%3A00%3A00&dropev=01%2F01%2F2040%2000%3A00%3A00",
    "https://www.modestogov.com/749/City-Council-Agendas-Minutes",
    "https://meetings.cob.org/",
    "https://boccmeetings.jocogov.org/onbaseagendaonline",
    "https://agendaonline.mymanatee.org/OnBaseAgendaOnline/",
    "https://meetings.cityofwestsacramento.org/OnBaseAgendaOnline",
]


raw_html=read_website_html(urls[4])
if raw_html is not None:
    outer_html=get_div_by_class(raw_html,class_name="meetings-list")
    print(outer_html)
    if outer_html is not None:
        meeting_info=parse_meeting_rows(outer_html,base_url=urls[0])
    else:
        print("something went wrong")

    print(json.dumps(meeting_info, indent=4))

else:
    print("something went wrong")








