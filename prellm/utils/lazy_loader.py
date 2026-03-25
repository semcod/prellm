"""Base class for lazy loading resources."""

from __future__ import annotations


class LazyLoader:
    """Base class for components that need lazy loading of resources."""
    
    def __init__(self) -> None:
        self._loaded = False
    
    def _ensure_loaded(self) -> None:
        """Ensure the resource is loaded, calling _load() if needed."""
        if not self._loaded:
            self._load()
            self._loaded = True
    
    def _load(self) -> None:
        """Override this method in subclasses to implement the actual loading logic."""
        raise NotImplementedError("Subclasses must implement _load() method")
