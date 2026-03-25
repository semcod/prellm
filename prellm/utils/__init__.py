"""Utility modules for preLLM."""

from .lazy_imports import lazy_import_global
from .lazy_loader import LazyLoader

__all__ = ["lazy_import_global", "LazyLoader"]
