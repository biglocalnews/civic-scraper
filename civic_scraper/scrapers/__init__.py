from .site import Site
from .civicplus import CivicPlusSite
from .granicus import GranicusSite

SUPPORTED_SCRAPERS = {
    'granicus': GranicusSite,
    'civicplus': CivicPlusSite,
}