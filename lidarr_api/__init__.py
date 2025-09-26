"""
Lidarr API Python Client Package

This package provides a comprehensive Python interface for interacting with 
Lidarr servers via the Lidarr API. It includes the main `LidarrClient` class 
for programmatic access, with built-in retry logic, rate limiting, 
configuration management, and comprehensive command-line utilities.

Features:
- Complete Lidarr API coverage
- Built-in retry logic and rate limiting
- Configuration persistence
- Command-line tools for management tasks
- Comprehensive error handling and logging
"""
from .client import LidarrClient

__version__ = "0.1.0"
__all__ = ["LidarrClient"]
