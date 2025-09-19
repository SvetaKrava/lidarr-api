import requests
import logging
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class LidarrClient:
    def __init__(self,
                 base_url: str,
                 api_key: str,
                 retry_total: int = 3,
                 retry_backoff_factor: float = 0.3,
                 timeout: int = 60,  # Increased default timeout
                 rate_limit_per_second: float = 2.0):
        """
        Initialize the Lidarr API client.

        Args:
            base_url: The base URL of your Lidarr instance (e.g., 'http://localhost:8686')
            api_key: Your Lidarr API key
            retry_total: Number of retries for failed requests
            retry_backoff_factor: Backoff factor between retries
            timeout: Request timeout in seconds (default 60)
            rate_limit_per_second: Maximum number of requests per second
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.rate_limit = 1.0 / rate_limit_per_second
        self.last_request_time = 0.0

        # Set up logging
        self.logger = logging.getLogger('lidarr_api')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        # Set up session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=retry_total,
            backoff_factor=retry_backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"],  # Allow retries on all methods
            raise_on_status=True
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.session.headers.update({
            'X-Api-Key': api_key,
            'Content-Type': 'application/json'
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make a request to the Lidarr API with rate limiting."""
        # Apply rate limiting
        now = time.time()
        time_since_last_request = now - self.last_request_time
        if time_since_last_request < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last_request
            self.logger.debug(f"Rate limiting - sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)

        url = f"{self.base_url}/api/v1/{endpoint}"
        self.logger.debug(f"Making {method} request to {url}")

        # Add timeout to all requests
        kwargs['timeout'] = kwargs.get('timeout', self.timeout)

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            self.last_request_time = time.time()
            return response.json() if response.content else None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {str(e)}")
            raise

    def _bool_to_str(self, value: bool) -> str:
        """Convert boolean to lowercase string for API parameters."""
        return str(value).lower()

    def get_system_status(self) -> Dict[str, Any]:
        """Get information about the system Lidarr is running on."""
        return self._request('GET', 'system/status')

    def get_artist(self, artist_id: int) -> Dict[str, Any]:
        """Get artist information by ID."""
        return self._request('GET', f'artist/{artist_id}')

    def get_all_artists(self) -> List[Dict[str, Any]]:
        """Get all artists in the library."""
        return self._request('GET', 'artist')

    def search_artist(self, term: str) -> List[Dict[str, Any]]:
        """Search for artists."""
        return self._request('GET', 'artist/lookup', params={'term': term})

    def get_albums_by_artist(self, artist_id: int) -> List[Dict[str, Any]]:
        """Get all albums for a specific artist."""
        return self._request('GET', 'album', params={'artistId': artist_id})

    def add_artist(self, artist_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new artist to Lidarr."""
        return self._request('POST', 'artist', json=artist_data)

    def get_calendar(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get calendar events."""
        params = {}
        if start_date:
            params['start'] = start_date
        if end_date:
            params['end'] = end_date
        return self._request('GET', 'calendar', params=params)

    def get_quality_profiles(self) -> List[Dict[str, Any]]:
        """Get all quality profiles."""
        return self._request('GET', 'qualityprofile')

    def get_quality_profile(self, profile_id: int) -> Dict[str, Any]:
        """Get a specific quality profile by ID."""
        return self._request('GET', f'qualityprofile/{profile_id}')

    def get_import_lists(self) -> List[Dict[str, Any]]:
        """Get all configured import lists."""
        return self._request('GET', 'importlist')

    def test_import_list(self, import_list_id: int) -> Dict[str, Any]:
        """Test an import list by ID."""
        return self._request('POST', f'importlist/test/{import_list_id}')

    def get_wanted(self,
                  page: int = 1,
                  page_size: int = 10,
                  include_artist: bool = True) -> Dict[str, Any]:
        """
        Get wanted/missing albums.

        Args:
            page: Page number to return
            page_size: Number of items per page
            include_artist: Whether to include artist information
        """
        params = {
            'page': page,
            'pageSize': page_size,
            'includeArtist': self._bool_to_str(include_artist)
        }
        # Use a longer timeout for this endpoint
        return self._request('GET', 'wanted/missing', params=params, timeout=60)

    def get_album(self, album_id: int) -> Dict[str, Any]:
        """Get album information by ID."""
        return self._request('GET', f'album/{album_id}')

    def update_album(self, album_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update album information."""
        return self._request('PUT', f'album/{album_id}', json=data)

    def get_track_file(self, track_file_id: int) -> Dict[str, Any]:
        """Get track file information by ID."""
        return self._request('GET', f'trackfile/{track_file_id}')

    def delete_track_file(self, track_file_id: int) -> None:
        """Delete a track file by ID."""
        return self._request('DELETE', f'trackfile/{track_file_id}')

    def get_metadata(self, artist_id: int) -> Dict[str, Any]:
        """Get metadata for an artist."""
        return self._request('GET', f'artistmetadata/{artist_id}')

    def search_album(self, album_id: int) -> Dict[str, Any]:
        """Search for a specific album by ID."""
        return self._request('POST', 'command', json={
            'name': 'AlbumSearch',
            'albumIds': [album_id]
        })

    def get_root_folders(self) -> List[Dict[str, Any]]:
        """Get all configured root folders."""
        return self._request('GET', 'rootfolder')

    def add_root_folder(self, path: str) -> Dict[str, Any]:
        """Add a new root folder."""
        return self._request('POST', 'rootfolder', json={'path': path})

    def delete_root_folder(self, folder_id: int) -> None:
        """Delete a root folder by ID."""
        return self._request('DELETE', f'rootfolder/{folder_id}')

    def get_queue(self,
                 page: int = 1,
                 page_size: int = 10,
                 include_artist: bool = True,
                 include_album: bool = True) -> Dict[str, Any]:
        """Get the current download queue."""
        params = {
            'page': page,
            'pageSize': page_size,
            'includeArtist': self._bool_to_str(include_artist),
            'includeAlbum': self._bool_to_str(include_album)
        }
        return self._request('GET', 'queue', params=params)

    def delete_queue_item(self,
                         queue_id: int,
                         blacklist: bool = False,
                         remove_from_client: bool = True) -> None:
        """
        Remove an item from the queue.

        Args:
            queue_id: ID of the queue item to remove
            blacklist: Whether to blacklist the release
            remove_from_client: Whether to remove the download from the client
        """
        params = {
            'blacklist': self._bool_to_str(blacklist),
            'removeFromClient': self._bool_to_str(remove_from_client)
        }
        return self._request('DELETE', f'queue/{queue_id}', params=params)

    def get_history(self,
                   page: int = 1,
                   page_size: int = 10,
                   include_artist: bool = True) -> Dict[str, Any]:
        """Get download history."""
        params = {
            'page': page,
            'pageSize': page_size,
            'includeArtist': self._bool_to_str(include_artist)
        }
        return self._request('GET', 'history', params=params)

    def get_disk_space(self) -> List[Dict[str, Any]]:
        """Get disk space information for all root folders."""
        return self._request('GET', 'diskspace')

    def get_manual_import(self, folder: str) -> List[Dict[str, Any]]:
        """Get manual import items from a folder."""
        return self._request('GET', 'manualimport', params={'folder': folder})

    def execute_manual_import(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute manual import of files."""
        return self._request('POST', 'command', json={
            'name': 'ManualImport',
            'files': files
        })

    def get_album_releases(self, album_id: int) -> List[Dict[str, Any]]:
        """Get all releases for an album."""
        return self._request('GET', f'album/{album_id}/releases')

    def get_release_by_id(self, release_id: int) -> Dict[str, Any]:
        """Get a specific release by ID."""
        return self._request('GET', f'release/{release_id}')

    def update_artist_monitor(self, artist_id: int, monitored: bool = True) -> Dict[str, Any]:
        """Update the monitored status of an artist."""
        artist = self.get_artist(artist_id)
        artist['monitored'] = monitored
        return self._request('PUT', f'artist/{artist_id}', json=artist)

    def get_artist_editor(self) -> List[Dict[str, Any]]:
        """Get all artists for bulk editing."""
        return self._request('GET', 'artist/editor')

    def update_artists_monitor(self, artist_ids: List[int], monitored: bool) -> Dict[str, Any]:
        """Update monitored status for multiple artists."""
        return self._request('PUT', 'artist/editor', json={
            'artistIds': artist_ids,
            'monitored': monitored
        })

    def get_tags(self) -> List[Dict[str, Any]]:
        """Get all tags."""
        return self._request('GET', 'tag')

    def add_tag(self, tag_label: str) -> Dict[str, Any]:
        """Add a new tag."""
        return self._request('POST', 'tag', json={'label': tag_label})

    def delete_tag(self, tag_id: int) -> None:
        """Delete a tag."""
        return self._request('DELETE', f'tag/{tag_id}')

    def get_tag_details(self, tag_id: int) -> Dict[str, Any]:
        """Get details about what items are tagged with a specific tag."""
        return self._request('GET', f'tag/detail/{tag_id}')

    def get_system_backup(self) -> List[Dict[str, Any]]:
        """Get list of available backups."""
        return self._request('GET', 'system/backup')

    def restore_system(self, backup_file: str) -> Dict[str, Any]:
        """Restore system from backup."""
        return self._request('POST', 'system/restore', json={'file': backup_file})

    def start_backup(self) -> Dict[str, Any]:
        """Start a manual backup."""
        return self._request('POST', 'system/backup', json={'type': 'manual'})

    def get_blocklist(self,
                     page: int = 1,
                     page_size: int = 10,
                     include_artist: bool = True) -> Dict[str, Any]:
        """Get blocklisted releases."""
        params = {
            'page': page,
            'pageSize': page_size,
            'includeArtist': self._bool_to_str(include_artist)
        }
        # Use a longer timeout for this endpoint
        return self._request('GET', 'blocklist', params=params, timeout=60)

    def delete_blocklist(self, blocklist_id: int) -> None:
        """Remove an item from the blocklist."""
        return self._request('DELETE', f'blocklist/{blocklist_id}')

    def clear_blocklist(self) -> None:
        """Remove all items from the blocklist."""
        return self._request('DELETE', 'blocklist')

    def get_metadata_profiles(self) -> List[Dict[str, Any]]:
        """Get all metadata profiles."""
        return self._request('GET', 'metadataprofile')

    def get_metadata_profile(self, profile_id: int) -> Dict[str, Any]:
        """Get a specific metadata profile by ID."""
        return self._request('GET', f'metadataprofile/{profile_id}')

    def search_artist_albums(self, artist_id: int) -> Dict[str, Any]:
        """Trigger a search for all albums by an artist."""
        return self._request('POST', 'command', json={
            'name': 'ArtistSearch',
            'artistIds': [artist_id]
        })
