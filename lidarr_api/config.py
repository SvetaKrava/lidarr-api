import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.config/lidarr-api/defaults.json")

class Config:
    """
    Configuration management for Lidarr API client.

    This class handles saving and loading of default settings for artist addition,
    making it easier to maintain consistent configurations across multiple operations.

    The configuration is stored in JSON format and includes settings for:
    - Root folder path
    - Quality profile
    - Metadata profile
    - Monitored status
    - Album monitoring options
    - Tags

    Args:
        config_path: Path to the config file. Defaults to ~/.config/lidarr-api/defaults.json

    Example:
        >>> config = Config()
        >>> # Save defaults
        >>> config.save_artist_defaults(
        ...     root_folder={"path": "/music"},
        ...     quality_profile={"id": 1},
        ...     metadata_profile={"id": 1},
        ...     monitored=True,
        ...     album_monitor_option=1,  # 1=All, 2=Future, 3=None
        ...     tags=[{"id": 1, "label": "rock"}]
        ... )
        >>> # Later, load the defaults
        >>> defaults = config.get_artist_defaults()
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            config_path: Optional path to the config file. If not provided,
                       defaults to ~/.config/lidarr-api/defaults.json
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.settings = self.load()

    def load(self) -> Dict[str, Any]:
        """Load settings from config file."""
        if not os.path.exists(self.config_path):
            return {}

        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def save(self) -> None:
        """Save current settings to config file."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.settings, f, indent=2)

    def save_artist_defaults(self,
                           root_folder: Dict[str, Any],
                           quality_profile: Dict[str, Any],
                           metadata_profile: Dict[str, Any],
                           monitored: bool,
                           album_monitor_option: int,
                           tags: List[Dict[str, Any]]) -> None:
        """Save artist addition defaults."""
        self.settings['artist_defaults'] = {
            'root_folder_path': root_folder['path'],
            'quality_profile_id': quality_profile['id'],
            'metadata_profile_id': metadata_profile['id'],
            'monitored': monitored,
            'album_monitor_option': album_monitor_option,
            'tag_ids': [tag['id'] for tag in tags] if tags else []
        }
        self.save()

    def get_artist_defaults(self) -> Optional[Dict[str, Any]]:
        """Get saved artist addition defaults."""
        return self.settings.get('artist_defaults')
