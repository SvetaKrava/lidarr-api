# Lidarr API Python Client

A Python library for interacting with the Lidarr API. This client provides a simple interface to communicate with your Lidarr instance.

## Installation

```bash
pip install lidarr-api
```

## Usage

```python
from lidarr_api import LidarrClient

# Initialize the client with custom settings
client = LidarrClient(
    base_url='http://localhost:8686',
    api_key='your-api-key',
    retry_total=3,                # Number of retries for failed requests
    retry_backoff_factor=0.3,     # Backoff factor between retries
    timeout=30,                   # Request timeout in seconds
    rate_limit_per_second=2.0     # Maximum requests per second
)

# Get system status
status = client.get_system_status()

# Search for an artist
results = client.search_artist('The Beatles')

# Get artist details
artist = client.get_artist(artist_id=1234)

# Get albums for an artist
albums = client.get_albums_by_artist(artist_id=1234)

# Get calendar events
calendar = client.get_calendar(start_date='2025-09-18', end_date='2025-10-18')

# Get wanted/missing albums with custom timeout
wanted = client.get_wanted(timeout=60)

# Manage tags
tags = client.get_tags()
new_tag = client.add_tag("new-tag")
client.delete_tag(new_tag['id'])
```

## Features

- Complete Lidarr API coverage
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
| timeout | 30 | Request timeout in seconds |
| rate_limit_per_second | 2.0 | Maximum requests per second |

## Requirements

- Python 3.6+
- requests library

## Development

1. Clone the repository
2. Install development dependencies: `pip install -r requirements.txt`
3. Copy `tests/config.py.example` to `tests/config.py` and update with your Lidarr settings
4. Run tests: `pytest`

## Error Handling

The client includes comprehensive error handling for:

- Network timeouts
- Server errors (500 series)
- Rate limiting (429)
- Authentication errors
- Invalid requests
- Missing resources

All errors are properly logged and can be caught using standard Python exception handling.

## License

MIT License
