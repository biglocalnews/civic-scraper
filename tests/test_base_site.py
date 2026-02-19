from civic_scraper.base.site import Site

def test_site_default():
    "Site should receive a url"

    class Example(Site):
        pass

    site = Example("https://foo.com")
    assert hasattr(site, "url")
    assert site.runtime.__class__.__name__ == "date"
