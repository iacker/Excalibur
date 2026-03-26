"""Excalibur public package."""

__version__ = "1.0.0"

from .cli import main, main_legacy

__all__ = ["main", "main_legacy", "__version__"]
