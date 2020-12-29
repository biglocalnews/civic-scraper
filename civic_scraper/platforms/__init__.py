from .civic_plus.site import Site as CivicPlusSite
from .granicus import GranicusSite

SUPPORTED_SITES = {
    'granicus': GranicusSite,
    'civicplus': CivicPlusSite,
}
