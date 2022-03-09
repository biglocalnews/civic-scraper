from unittest.mock import patch

from civic_scraper.base.cache import Cache

from .conftest import file_contents


def test_default_cache_dir(monkeypatch):
    target = "civic_scraper.utils.expanduser"
    with patch(target) as mock_method:
        mock_method.return_value = "/Users/you"
        cache = Cache()
        assert cache.path == "/Users/you/.civic-scraper"


def test_custom_cache_path(tmpdir):
    from civic_scraper.base.cache import Cache

    cache = Cache(tmpdir)
    assert tmpdir == cache.path


def test_write(tmpdir):
    from civic_scraper.base.cache import Cache

    cache = Cache(tmpdir)
    content = "<h1>some content</h1>"
    file_path = "html/search_results_page.html"
    outfile = cache.write(file_path, content)
    scrape_dir = tmpdir.join("html")
    files = [f.basename for f in scrape_dir.listdir()]
    assert "search_results_page.html" in files
    actual_contents = file_contents(outfile)
    assert actual_contents == content
