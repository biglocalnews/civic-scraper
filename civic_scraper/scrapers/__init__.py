from .site import Site
from .civicplus import CivicPlusSite
from .granicus import GranicusSite

SUPPORTED_SITES = {
    'granicus': GranicusSite,
    'civicplus': CivicPlusSite,
}