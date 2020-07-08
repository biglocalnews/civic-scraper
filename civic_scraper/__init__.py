from .scrapers.civicplus import CivicPlusSite
from .scrapers.granicus import GranicusSite

SUPPORTED_SCRAPERS = {
    'granicus': GranicusSite,
    'civicplus': CivicPlusSite,
}