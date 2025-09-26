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

The package includes multiple command-line tools for different tasks:

#### Artist Search and Management

```bash
lidarr-search "Artist Name" [options]
```

Options:

- `--url`: Lidarr server URL (default: from config or http://localhost:8686)
- `--api-key`: Lidarr API key (default: from config)
- `--timeout`: Request timeout in seconds (default: 60)
- `--retries`: Number of retries for failed requests (default: 3)
- `--force-search`: Trigger album search after adding artist
- `--use-defaults`: Use saved configuration defaults
- `--save-defaults`: Save current selections as defaults
- `--config`: Path to config file (default: ~/.config/lidarr-api/defaults.json)
- `--save-connection`: Save URL and API key to config
- `--debug`: Enable debug output

#### Utility Scripts

Additional utility scripts are available for advanced management:

- **`lidarr-bulk`**: Bulk operations on artists (monitor, unmonitor, tag, search, export, list-by-tag)
- **`lidarr-maintenance`**: System maintenance (backup, blocklist, health checks)
- **`lidarr-library`**: Library management (wanted albums, profiles, imports, queue)
- **`lidarr-monitor`**: Monitoring and health checks (status, monitor, history, export)
- **`lidarr-data`**: Data import/export utilities (export/import artists, config, wanted)

Examples:

```bash
# Bulk operations
lidarr-bulk monitor --artists 1,2,3,4
lidarr-bulk export --output artists.json --format json

# System maintenance
lidarr-maintenance backup create
lidarr-maintenance blocklist view
lidarr-maintenance health

# Library management
lidarr-library wanted list
lidarr-library profiles quality
lidarr-library queue view

# Monitoring
lidarr-monitor status --verbose
lidarr-monitor history --hours 48

# Data utilities
lidarr-data export artists --output artists.json --format json
lidarr-data import artists --input artists.json --dry-run
```

See the [scripts documentation](scripts/README.md) for detailed usage information.

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

- **Complete Lidarr API coverage** - All major API endpoints supported
- **Command-line interface** for artist management and search  
- **Comprehensive utility scripts** for:
  - Bulk operations (monitor, tag, search, export artists)
  - System maintenance (backups, blocklist, health checks)  
  - Library management (wanted albums, profiles, queue, imports)
  - Monitoring and health checks with detailed reporting
  - Data import/export and migration between instances
- **Configuration persistence** - Save connection settings and defaults
- **Automatic retry mechanism** with exponential backoff for failed requests
- **Rate limiting** to prevent server overload (configurable, default 2.0 req/sec)
- **Configurable request timeouts** (default 60 seconds)
- **Comprehensive logging support** with debug capabilities
- **Error handling** for network issues, authentication, and server errors

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

- Python 3.10+
- requests library

## Development

1. Clone the repository
2. Install Poetry: `pip install poetry`
3. Install dependencies: `poetry install`
4. Copy `tests/config.py.example` to `tests/config.py` and update with your Lidarr settings
5. Run tests: `poetry run pytest`
   - For integration tests: `poetry run pytest -m integration`
   - For unit tests only: `poetry run pytest -m "not integration"`

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

This project is licensed under the GNU General Public License v3.0 or later (GPL-3.0-or-later).
