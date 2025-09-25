"""
Lidarr API Python Client Package

This package provides a Python interface for interacting with Lidarr servers via the Lidarr API.
It exposes the main `LidarrClient` class for programmatic access, including built-in retry logic,
rate limiting, and configuration management.
"""
from .client import LidarrClient

__version__ = "0.1.0"
__all__ = ["LidarrClient"]
