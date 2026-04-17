from ._version import __version__
from .fred import fred
from .fama_french import ff, ff_search

__all__ = ["ff", "fred", "ff_search", "__version__"]