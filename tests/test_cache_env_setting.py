from civic_scraper.base.cache import Cache


def test_env_configured_default(monkeypatch):
    "CIVIC_SCRAPER_DIR env var should configure cache"
    monkeypatch.setenv("CIVIC_SCRAPER_DIR", "/tmp/civic-scraper")
    cache = Cache()
    assert cache.path == "/tmp/civic-scraper"
