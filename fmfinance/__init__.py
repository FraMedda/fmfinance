from ._version import __version__
from .fred import FredReader
from .fama_french import FFReader, FFSearch

__all__ = ["FredReader", "FFReader", "FFSearch", "__version__"]