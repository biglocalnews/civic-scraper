from civic_scraper.base.site import Site


def test_site_default():
    "Site should receive a url"

    class Example(Site):
        pass

    site = Example("https://foo.com")
    assert hasattr(site, "url")
    assert site.runtime.__class__.__name__ == "date"
    assert not hasattr(site, "parser_kls")


def test_site_with_parser():
    "Site accepts optional Parser class"

    class Parser:
        pass

    class Example(Site):
        pass

    site = Example("https://foo.com", parser_kls=Parser)
    assert hasattr(site, "parser_kls")
