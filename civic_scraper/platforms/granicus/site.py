from requests import Session

def fetch_url(url = 'https://brookhavencityga.iqm2.com/Citizens/default.aspx', **kwargs):
    session = Session()
    headers = {"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"}
    response = session.get(url, headers=headers)

    print(response.text)

    return response

if __name__ == '__main__':
    fetch_url()

