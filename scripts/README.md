# Lidarr API Utility Scripts

This directory contains utility scripts that extend the functionality of the Lidarr API Python client. These scripts provide command-line interfaces for common Lidarr management tasks.

## Available Scripts

### 1. Bulk Artist Manager (`bulk_artist_manager.py`)

Perform bulk operations on artists in your Lidarr library.

**Features:**

- Bulk monitor/unmonitor artists
- Bulk tag management (add/remove tags)
- Search for albums across multiple artists
- Export artist lists to JSON/CSV
- List artists by tag

**Examples:**

```bash
lidarr-bulk monitor --artists 1,2,3,4
lidarr-bulk tag --artists 1,2,3 --tag-ids 5,6 --add
lidarr-bulk export --output artists.json --format json
lidarr-bulk list-by-tag --tag-name rock
```

### 2. System Maintenance (`system_maintenance.py`)

System maintenance and administrative tasks for Lidarr.

**Features:**

- Backup management (create, list, restore)
- Blocklist management (view, clean, remove items)
- System health monitoring
- Disk space monitoring

**Examples:**

```bash
lidarr-maintenance backup create
lidarr-maintenance backup list
lidarr-maintenance blocklist view
lidarr-maintenance health
```

### 3. Library Manager (`library_manager.py`)

Comprehensive library management utilities.

**Features:**

- Wanted/missing albums management
- Quality and metadata profile management
- Import list management
- Download queue monitoring and management

**Examples:**

```bash
lidarr-library wanted list
lidarr-library wanted search --limit 5
lidarr-library profiles quality
lidarr-library queue view
```

### 4. Monitoring (`monitoring.py`)

Advanced monitoring and health check capabilities.

**Features:**

- Comprehensive system health checks
- Continuous queue monitoring with alerts
- Recent download history analysis
- Performance metrics collection
- Export detailed health reports

**Examples:**

```bash
lidarr-monitor status --verbose
lidarr-monitor monitor --interval 30
lidarr-monitor history --hours 48
lidarr-monitor export --output health_report.json
```

### 5. Data Utilities (`data_utils.py`)

Data import/export and migration utilities.

**Features:**

- Export artist libraries to JSON/CSV
- Import artist lists from files
- Configuration backup and restore
- Wanted albums export
- Tag management across instances

**Examples:**

```bash
# Export artists with albums
lidarr-data export artists --output artists.json --include-albums

# Import artists (dry run first)  
lidarr-data import artists --input artists.json --dry-run

# Export configuration
lidarr-data export config --output config.json

# Export wanted albums to CSV
lidarr-data export wanted --output wanted.csv --format csv
```

## Installation and Setup

### Prerequisites

1. Install the lidarr-api package:

   ```bash
   pip install lidarr-api
   ```

   All CLI tools will be available after installation.

### Configuration

All scripts support the same connection options:

#### Option 1: Command Line Arguments

```bash
lidarr-bulk --url http://localhost:8686 --api-key your-api-key [command]
lidarr-data --url http://localhost:8686 --api-key your-api-key [command]
lidarr-library --url http://localhost:8686 --api-key your-api-key [command]
lidarr-maintenance --url http://localhost:8686 --api-key your-api-key [command]
lidarr-monitor --url http://localhost:8686 --api-key your-api-key [command]
```

#### Option 2: Configuration File

```bash
# First, save your connection settings
python -c "
from lidarr_api.config import Config
config = Config()
config.save_connection_settings('http://localhost:8686', 'your-api-key')
"

# Then use scripts without connection args
lidarr-bulk [command]
lidarr-data [command]
# etc.
```

#### Option 3: Custom Config Path

```bash
lidarr-bulk --config /path/to/config.json [command]
lidarr-data --config /path/to/config.json [command]
# etc.
```

### Global Options

All scripts support these common options:

- `--url`: Lidarr server URL
- `--api-key`: Lidarr API key
- `--config`: Path to configuration file
- `--timeout`: Request timeout in seconds (default: 60)
- `--retries`: Number of retries for failed requests (default: 3)

## Usage Examples

### Common Workflows

**Daily Maintenance:**

```bash
# Check system health
lidarr-monitor status

# View wanted albums and trigger search for top 10
lidarr-library wanted list --page-size 10
lidarr-library wanted search --limit 10

# Check download queue
lidarr-library queue view
```

**Weekly Cleanup:**

```bash
# View and clean blocklist
lidarr-maintenance blocklist view
lidarr-maintenance blocklist clear

# Create backup
lidarr-maintenance backup create
```

**Migration Between Servers:**

```bash
# Export from old server
lidarr-data export artists --output artists.json --include-albums
lidarr-data export config --output config.json

# Import to new server
lidarr-data import tags --input config.json --execute
lidarr-data import artists --input artists.json --execute
```

**Bulk Operations:**

```bash
# Monitor all rock artists
lidarr-bulk list-by-tag --tag-name rock
lidarr-bulk monitor --artists 1,2,3,4,5

# Search for albums by specific artists
lidarr-bulk search --artists 10,20,30
```

## Error Handling

All scripts include comprehensive error handling and will:

- Validate connection settings before proceeding
- Provide helpful error messages
- Support graceful cancellation (Ctrl+C)
- Return appropriate exit codes:
  - 0: Success
  - 1: General error
  - 2: Critical error (monitoring script)
  - 130: Cancelled by user

## Output Formats

Scripts support multiple output formats where applicable:

- **JSON**: Structured data, good for programmatic use
- **CSV**: Spreadsheet compatible, good for analysis
- **Console**: Human-readable table format

## Performance Considerations

- Scripts use the client's built-in rate limiting (2.0 requests/second by default)
- Large operations (bulk imports, exports) may take time
- Use `--dry-run` options when available to preview changes
- Monitor memory usage for very large libraries

## Integration with Other Tools

These scripts can be easily integrated with:

- **Cron jobs**: For automated maintenance
- **Shell scripts**: For complex workflows
- **Monitoring systems**: Using exit codes and JSON output
- **CI/CD pipelines**: For automated testing and deployment

## Contributing

When adding new scripts:

1. Follow the existing argument parsing pattern
2. Include comprehensive help text and examples
3. Support both verbose and quiet operation modes
4. Implement proper error handling and exit codes
5. Add documentation to this README

## Support

For issues with these scripts:

1. Check the main project documentation
2. Verify your Lidarr server is accessible and the API key is valid
3. Use `--debug` or `--verbose` flags for more detailed output
4. Check Lidarr's logs for server-side errors
