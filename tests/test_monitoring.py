"""Tests for lidarr_api.monitoring module."""

import pytest
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, mock_open
from lidarr_api.monitoring import (
    system_status_check,
    check_recent_history,
    format_bytes,
    format_duration,
    setup_client
)


@pytest.fixture
def mock_client():
    """Create a mock LidarrClient for testing."""
    client = Mock()

    # Mock system status
    client.get_system_status.return_value = {
        'version': '1.0.2.2587',
        'buildTime': '2023-09-18T10:00:00Z',
        'startTime': '2023-12-01T12:00:00Z',
        'runtimeName': '.NET',
        'runtimeVersion': '6.0.0',
        'osName': 'Linux',
        'osVersion': '5.15.0'
    }

    # Mock disk space
    client.get_disk_space.return_value = [
        {
            'path': '/music',
            'freeSpace': 500 * 1024**3,  # 500GB free
            'totalSpace': 1000 * 1024**3  # 1TB total
        }
    ]

    # Mock queue
    client.get_queue.return_value = {
        'records': [
            {'status': 'downloading'},
            {'status': 'queued'},
            {'status': 'failed'}
        ],
        'totalRecords': 3
    }

    # Mock wanted albums
    client.get_wanted.return_value = {
        'totalRecords': 42
    }

    # Mock history
    now = datetime.now(timezone.utc)
    client.get_history.return_value = {
        'records': [
            {
                'eventType': 'grabbed',
                'date': (now - timedelta(hours=2)).isoformat(),
                'artist': {'artistName': 'Test Artist'},
                'album': {'title': 'Test Album'}
            },
            {
                'eventType': 'trackFileImported',
                'date': (now - timedelta(hours=1)).isoformat(),
                'artist': {'artistName': 'Test Artist'},
                'album': {'title': 'Test Album'}
            },
            {
                'eventType': 'downloadFailed',
                'date': (now - timedelta(hours=3)).isoformat(),
                'artist': {'artistName': 'Failed Artist'},
                'album': {'title': 'Failed Album'}
            }
        ]
    }

    return client


class TestUtilityFunctions:
    """Test utility functions."""

    def test_format_bytes(self):
        """Test byte formatting function."""
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1024**2) == "1.0 MB"
        assert format_bytes(1024**3) == "1.0 GB"
        assert format_bytes(1024**4) == "1.0 TB"
        assert format_bytes(500) == "500.0 B"

    def test_format_duration(self):
        """Test duration formatting function."""
        assert format_duration(30) == "30s"
        assert format_duration(90) == "1m 30s"
        assert format_duration(3661) == "1h 1m"
        assert format_duration(90061) == "1d 1h"


class TestSystemStatusCheck:
    """Test system status checking."""

    @patch('sys.stderr')
    def test_system_status_check_healthy(self, mock_stderr, mock_client):
        """Test system status check when everything is healthy."""
        result = system_status_check(mock_client, verbose=False)

        assert result['status'] == 'healthy'
        assert 'system_info' in result['checks']
        assert 'disk_space' in result['checks']
        assert 'queue' in result['checks']
        assert 'wanted_albums' in result['checks']

        # Check system info
        assert result['checks']['system_info']['version'] == '1.0.2.2587'
        assert result['checks']['system_info']['runtime'] == '.NET 6.0.0'

        # Check disk space
        disk_info = result['checks']['disk_space'][0]
        assert disk_info['path'] == '/music'
        assert disk_info['used_percent'] == 50.0

        # Check queue
        queue_info = result['checks']['queue']
        assert queue_info['total_items'] == 3
        assert queue_info['active_downloads'] == 2
        assert queue_info['failed_downloads'] == 1

        # Check wanted albums
        assert result['checks']['wanted_albums'] == 42

    @patch('sys.stderr')
    def test_system_status_check_with_warnings(self, mock_stderr, mock_client):
        """Test system status check with warning conditions."""
        # Mock high disk usage
        mock_client.get_disk_space.return_value = [
            {
                'path': '/music',
                'freeSpace': 100 * 1024**3,  # 100GB free
                'totalSpace': 1000 * 1024**3  # 1TB total (90% used)
            }
        ]

        result = system_status_check(mock_client, verbose=False)

        assert result['status'] == 'error'  # Over 90% is error
        assert len(result['errors']) > 0
        assert 'Critical: Disk /music is 90.0% full' in result['errors'][0]

    @patch('sys.stderr')
    def test_system_status_check_verbose(self, mock_stderr, mock_client):
        """Test system status check in verbose mode."""
        system_status_check(mock_client, verbose=True)

        # Verbose mode should print additional information
        # We can't easily test print output, but we can ensure it doesn't crash


class TestHistoryCheck:
    """Test history checking functionality."""

    @patch('sys.stdout')
    def test_check_recent_history_24_hours(self, mock_stdout, mock_client):
        """Test checking recent history for 24 hours."""
        check_recent_history(mock_client, hours=24)

        # Check that get_history was called with appropriate parameters
        mock_client.get_history.assert_called_once()
        call_args = mock_client.get_history.call_args
        assert call_args[1]['page'] == 1
        assert call_args[1]['page_size'] == 120  # 24 * 5

    @patch('sys.stdout')
    def test_check_recent_history_1_hour(self, mock_stdout, mock_client):
        """Test checking recent history for 1 hour."""
        check_recent_history(mock_client, hours=1)

        # Check that get_history was called with minimum page size
        call_args = mock_client.get_history.call_args
        assert call_args[1]['page_size'] == 100  # min(1000, max(100, 1*5))

    @patch('sys.stdout')
    def test_check_recent_history_large_timeframe(self, mock_stdout, mock_client):
        """Test checking recent history for large timeframe."""
        check_recent_history(mock_client, hours=300)  # 300 hours

        # Check that page_size is capped at 1000
        call_args = mock_client.get_history.call_args
        assert call_args[1]['page_size'] == 1000

    @patch('sys.stdout')
    def test_check_recent_history_no_records(self, mock_stdout, mock_client):
        """Test history check when no records are found."""
        mock_client.get_history.return_value = {'records': []}

        check_recent_history(mock_client, hours=24)

        # Should handle empty results gracefully

    @patch('sys.stdout')
    def test_check_recent_history_timezone_handling(self, mock_stdout, mock_client):
        """Test that history check properly handles timezone-aware dates."""
        now = datetime.now(timezone.utc)

        # Create records with different date formats
        mock_client.get_history.return_value = {
            'records': [
                {
                    'eventType': 'grabbed',
                    'date': (now - timedelta(hours=1)).isoformat().replace('+00:00', 'Z'),
                    'artist': {'artistName': 'Test Artist'},
                    'album': {'title': 'Test Album'}
                },
                {
                    'eventType': 'trackFileImported',
                    'date': (now - timedelta(hours=2)).isoformat(),  # With timezone
                    'artist': {'artistName': 'Test Artist 2'},
                    'album': {'title': 'Test Album 2'}
                },
                {
                    'eventType': 'downloadFailed',
                    'date': (now - timedelta(days=2)).isoformat().replace('+00:00', ''),  # Old record
                    'artist': {'artistName': 'Old Artist'},
                    'album': {'title': 'Old Album'}
                }
            ]
        }

        check_recent_history(mock_client, hours=24)

        # Should filter out records older than 24 hours


class TestSetupClient:
    """Test client setup function."""

    @patch('lidarr_api.monitoring.LidarrClient')
    def test_setup_client_with_url_and_key(self, mock_client_class):
        """Test setting up client with URL and API key."""
        from argparse import Namespace

        args = Namespace(
            url='http://test:8686',
            api_key='test-key',
            config=None,
            timeout=60,
            retries=3
        )

        setup_client(args)

        mock_client_class.assert_called_once_with(
            base_url='http://test:8686',
            api_key='test-key',
            timeout=60,
            retry_total=3
        )

    @patch('lidarr_api.monitoring.Config')
    @patch('lidarr_api.monitoring.LidarrClient')
    def test_setup_client_from_config(self, mock_client_class, mock_config_class):
        """Test setting up client from config file."""
        from argparse import Namespace

        args = Namespace(
            url=None,
            api_key=None,
            config='test-config.json',
            timeout=30,
            retries=5
        )

        # Mock config
        mock_config = Mock()
        mock_config.get_connection_settings.return_value = {
            'base_url': 'http://config:8686',
            'api_key': 'config-key'
        }
        mock_config_class.return_value = mock_config

        setup_client(args)

        mock_config_class.assert_called_once_with('test-config.json')
        mock_client_class.assert_called_once_with(
            base_url='http://config:8686',
            api_key='config-key',
            timeout=30,
            retry_total=5
        )
