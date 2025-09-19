# Lidarr API Python Client

A Python library for interacting with the Lidarr API. This client provides a simple interface to communicate with your Lidarr instance.

## Installation

```bash
pip install lidarr-api
```

## Usage

### Basic Usage

```python
from lidarr_api import LidarrClient
from lidarr_api.config import Config

# Initialize with explicit connection settings
client = LidarrClient(
    base_url='http://localhost:8686',
    api_key='your-api-key',
    retry_total=3,                # Number of retries for failed requests
    retry_backoff_factor=0.3,     # Backoff factor between retries
    timeout=60,                   # Request timeout in seconds (default increased from 30)
    rate_limit_per_second=2.0     # Maximum requests per second
)

# Or load connection settings from config
config = Config()
settings = config.get_connection_settings()
if settings:
    client = LidarrClient(**settings)

# Save connection settings for later use
config.save_connection_settings(
    base_url='http://localhost:8686',
    api_key='your-api-key'
)

# Get system status
status = client.get_system_status()

# Search for an artist
results = client.search_artist('The Beatles')

# Get artist details
artist = client.get_artist(artist_id=1234)

# Get albums for an artist
albums = client.get_albums_by_artist(artist_id=1234)
```

### Command Line Interface

The package includes a command-line tool for searching and adding artists:

```bash
lidarr-search "Artist Name" [options]
```

Options:

- `--url`: Lidarr server URL (default: from config or <http://localhost:8686>)
- `--api-key`: Lidarr API key (default: from config)
- `--timeout`: Request timeout in seconds (default: 60)
- `--retries`: Number of retries for failed requests (default: 3)
- `--force-search`: Trigger album search after adding artist
- `--use-defaults`: Use saved configuration defaults
- `--save-defaults`: Save current selections as defaults
- `--config`: Path to config file (default: ~/.config/lidarr-api/defaults.json)
- `--save-connection`: Save URL and API key to config
- `--debug`: Enable debug output

### Configuration Management

The library supports saving and loading both connection settings and artist addition defaults:

```python
from lidarr_api import LidarrClient
from lidarr_api.config import Config

# Initialize with custom config path
config = Config('/path/to/config.json')

# Save connection settings
config.save_connection_settings(
    base_url='http://localhost:8686',
    api_key='your-api-key'
)

# Load connection settings
settings = config.get_connection_settings()
if settings:
    client = LidarrClient(**settings)

# Save artist addition defaults
config.save_artist_defaults(
    root_folder={"path": "/music"},
    quality_profile={"id": 1},
    metadata_profile={"id": 1},
    monitored=True,
    album_monitor_option=1,  # 1=All, 2=Future, 3=None
    tags=[{"id": 1, "label": "rock"}]
)

# Get saved artist addition defaults
defaults = config.get_artist_defaults()
```

## Features

- Complete Lidarr API coverage
- Command-line interface for artist management
- Configuration persistence
- Automatic retry mechanism for failed requests
- Rate limiting to prevent server overload
- Configurable request timeouts
- Comprehensive logging support
- System status information
- Artist search and management
- Album management and releases
- Calendar events
- Quality profile management
- Import list handling
- Wanted/missing albums tracking
- Queue management
- History tracking
- Tag management
- Blocklist management
- Disk space monitoring
- Backup/restore operations

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| base_url | Required | The base URL of your Lidarr instance |
| api_key | Required | Your Lidarr API key |
| retry_total | 3 | Number of retries for failed requests |
| retry_backoff_factor | 0.3 | Backoff factor between retries |
| timeout | 60 | Request timeout in seconds |
| rate_limit_per_second | 2.0 | Maximum requests per second |

## Requirements

- Python 3.6+
- requests library

## Development

1. Clone the repository
2. Install development dependencies: `pip install -r requirements.txt`
3. Copy `tests/config.py.example` to `tests/config.py` and update with your Lidarr settings
4. Run tests: `pytest`
   - For integration tests: `pytest -m integration`
   - For unit tests only: `pytest -m "not integration"`

## Error Handling

The client includes comprehensive error handling for:

- Network timeouts
- Server errors (500 series)
- Rate limiting (429)
- Authentication errors
- Invalid requests
- Missing resources

All errors are properly logged and can be caught using standard Python exception handling. The client automatically retries failed requests with exponential backoff.

### Logging

The client uses Python's standard logging module. You can configure logging level and handlers:

```python
import logging
logging.getLogger('lidarr_api').setLevel(logging.DEBUG)
```

## License

MIT License
