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
python scripts/bulk_artist_manager.py monitor --artists 1,2,3,4
python scripts/bulk_artist_manager.py tag --artists 1,2,3 --tag-ids 5,6 --add
python scripts/bulk_artist_manager.py export --output artists.json --format json
python scripts/bulk_artist_manager.py list-by-tag --tag-name rock
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
python scripts/system_maintenance.py backup create
python scripts/system_maintenance.py backup list
python scripts/system_maintenance.py blocklist view
python scripts/system_maintenance.py health
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
python scripts/library_manager.py wanted list
python scripts/library_manager.py wanted search --limit 5
python scripts/library_manager.py profiles quality
python scripts/library_manager.py queue view
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
python scripts/monitoring.py status --verbose
python scripts/monitoring.py monitor --interval 30
python scripts/monitoring.py history --hours 48
python scripts/monitoring.py export --output health_report.json
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
python scripts/data_utils.py export artists --output artists.json --include-albums
python scripts/data_utils.py import artists --input artists.json --dry-run
python scripts/data_utils.py export config --output config.json
python scripts/data_utils.py export wanted --output wanted.csv --format csv
```

## Installation and Setup

### Prerequisites

1. Install the lidarr-api package:
   ```bash
   pip install lidarr-api
   ```

2. Make sure all scripts are executable:
   ```bash
   chmod +x scripts/*.py
   ```

### Configuration

All scripts support the same connection options:

**Option 1: Command Line Arguments**
```bash
python script.py --url http://localhost:8686 --api-key your-api-key [command]
```

**Option 2: Configuration File**
```bash
# First, save your connection settings
python -c "
from lidarr_api.config import Config
config = Config()
config.save_connection_settings('http://localhost:8686', 'your-api-key')
"

# Then use scripts without connection args
python scripts/script.py [command]
```

**Option 3: Custom Config Path**
```bash
python scripts/script.py --config /path/to/config.json [command]
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
python scripts/monitoring.py status

# View wanted albums and trigger search for top 10
python scripts/library_manager.py wanted list --page-size 10
python scripts/library_manager.py wanted search --limit 10

# Check download queue
python scripts/library_manager.py queue view
```

**Weekly Cleanup:**
```bash
# View and clean blocklist
python scripts/system_maintenance.py blocklist view
python scripts/system_maintenance.py blocklist clear

# Create backup
python scripts/system_maintenance.py backup create
```

**Migration Between Servers:**
```bash
# Export from old server
python scripts/data_utils.py export artists --output artists.json --include-albums
python scripts/data_utils.py export config --output config.json

# Import to new server
python scripts/data_utils.py import tags --input config.json --execute
python scripts/data_utils.py import artists --input artists.json --execute
```

**Bulk Operations:**
```bash
# Monitor all rock artists
python scripts/bulk_artist_manager.py list-by-tag --tag-name rock
python scripts/bulk_artist_manager.py monitor --artists 1,2,3,4,5

# Search for albums by specific artists
python scripts/bulk_artist_manager.py search --artists 10,20,30
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