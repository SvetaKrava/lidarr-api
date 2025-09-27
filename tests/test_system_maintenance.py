"""Tests for lidarr_api.system_maintenance module."""

import pytest
from unittest.mock import Mock, patch
from lidarr_api.system_maintenance import (
    setup_client, create_backup, list_backups, restore_backup,
    view_blocklist, clear_blocklist, remove_blocklist_item, system_health
)


@pytest.fixture
def mock_client():
    """Create a mock LidarrClient for testing."""
    client = Mock()

    # Mock system status
    client.get_system_status.return_value = {
        'version': '1.0.0.0',
        'buildTime': '2023-01-01T00:00:00Z',
        'isDebug': False,
        'isProduction': True,
        'isAdmin': True,
        'isUserInteractive': False,
        'startupPath': '/app',
        'appData': '/config',
        'osName': 'Linux',
        'osVersion': '5.4.0',
        'isMonoRuntime': False,
        'runtimeVersion': '.NET 6.0.0',
        'databaseVersion': '0.2.0',
        'databaseType': 'SQLite',
        'authentication': 'None',
        'migrationVersion': 100,
        'urlBase': '',
        'runtimeName': '.NET'
    }

    # Mock backups
    client.get_system_backup.return_value = [
        {
            'name': 'backup1.zip',
            'path': '/config/Backups/backup1.zip',
            'type': 'manual',
            'time': '2023-12-01T10:00:00Z',
            'id': 1
        }
    ]

    # Mock health check
    client.get_health.return_value = [
        {
            'source': 'IndexerRssCheck',
            'type': 'warning',
            'message': 'Test warning message',
            'wikiUrl': 'https://wiki.servarr.com/'
        }
    ]

    # Mock blocklist
    client.get_blocklist.return_value = {
        'records': [
            {
                'id': 1,
                'artistId': 1,
                'albumId': 1,
                'sourceTitle': 'Blocked Item',
                'date': '2023-12-01T10:00:00Z'
            }
        ],
        'totalRecords': 1
    }

    # Mock command responses
    client.create_backup.return_value = {'id': 1}
    client.restore_backup.return_value = {'success': True}
    client.delete_blocklist.return_value = {'success': True}
    client.remove_from_blocklist.return_value = {'success': True}

    return client


class TestSetupClient:
    """Test client setup function."""

    @patch('lidarr_api.system_maintenance.LidarrClient')
    def test_setup_client_with_url_and_key(self, mock_client_class):
        """Test setting up client with URL and API key."""
        from argparse import Namespace

        args = Namespace(
            url='http://test:8686',
            api_key='test-key',
            config=None,
            timeout=60,
            retries=3,
            rate_limit=2.0
        )

        setup_client(args)

        mock_client_class.assert_called_once_with(
            base_url='http://test:8686',
            api_key='test-key',
            timeout=60,
            retry_total=3,
            rate_limit_per_second=2.0
        )


class TestCreateBackup:
    """Test backup creation functionality."""

    @patch('sys.stderr')
    def test_create_backup_success(self, mock_stderr, mock_client):
        """Test successful backup creation."""
        create_backup(mock_client)

        mock_client.create_backup.assert_called_once()

    @patch('sys.stderr')
    def test_create_backup_with_error(self, mock_stderr, mock_client):
        """Test backup creation with error."""
        mock_client.create_backup.side_effect = Exception("Backup failed")

        with pytest.raises(Exception):
            create_backup(mock_client)


class TestListBackups:
    """Test backup listing functionality."""

    @patch('sys.stderr')
    @patch('sys.stdout')
    def test_list_backups(self, mock_stdout, mock_stderr, mock_client):
        """Test listing available backups."""
        list_backups(mock_client)

        mock_client.get_system_backup.assert_called_once()
        assert mock_stdout.write.called

    @patch('sys.stderr')
    @patch('sys.stdout')
    def test_list_backups_no_backups(self, mock_stdout, mock_stderr, mock_client):
        """Test listing when no backups exist."""
        mock_client.get_system_backup.return_value = []

        list_backups(mock_client)

        mock_client.get_system_backup.assert_called_once()


class TestRestoreBackup:
    """Test backup restoration functionality."""

    @patch('sys.stderr')
    @patch('builtins.input', return_value='y')
    def test_restore_backup_confirmed(self, mock_input, mock_stderr, mock_client):
        """Test restoring backup with confirmation."""
        restore_backup(mock_client, 'backup1.zip')

        mock_client.restore_backup.assert_called_once_with('backup1.zip')

    @patch('sys.stderr')
    @patch('builtins.input', return_value='n')
    def test_restore_backup_cancelled(self, mock_input, mock_stderr, mock_client):
        """Test cancelling backup restoration."""
        restore_backup(mock_client, 'backup1.zip')

        mock_client.restore_backup.assert_not_called()


class TestViewBlocklist:
    """Test blocklist viewing functionality."""

    @patch('sys.stderr')
    @patch('sys.stdout')
    def test_view_blocklist_default_pagination(self, mock_stdout, mock_stderr, mock_client):
        """Test viewing blocklist with default pagination."""
        view_blocklist(mock_client)

        mock_client.get_blocklist.assert_called_once()
        assert mock_stdout.write.called

    @patch('sys.stderr')
    @patch('sys.stdout')
    def test_view_blocklist_custom_pagination(self, mock_stdout, mock_stderr, mock_client):
        """Test viewing blocklist with custom pagination."""
        view_blocklist(mock_client, page=2, page_size=10)

        mock_client.get_blocklist.assert_called_once()
        assert mock_stdout.write.called

    @patch('sys.stderr')
    @patch('sys.stdout')
    def test_view_blocklist_empty(self, mock_stdout, mock_stderr, mock_client):
        """Test viewing empty blocklist."""
        mock_client.get_blocklist.return_value = {
            'records': [],
            'totalRecords': 0
        }

        view_blocklist(mock_client)

        mock_client.get_blocklist.assert_called_once()


class TestClearBlocklist:
    """Test blocklist clearing functionality."""

    @patch('sys.stderr')
    @patch('builtins.input', return_value='y')
    def test_clear_blocklist_confirmed(self, mock_input, mock_stderr, mock_client):
        """Test clearing blocklist with confirmation."""
        clear_blocklist(mock_client)

        mock_client.delete_blocklist.assert_called_once()

    @patch('sys.stderr')
    @patch('builtins.input', return_value='n')
    def test_clear_blocklist_cancelled(self, mock_input, mock_stderr, mock_client):
        """Test cancelling blocklist clearing."""
        clear_blocklist(mock_client)

        mock_client.delete_blocklist.assert_not_called()


class TestRemoveBlocklistItem:
    """Test blocklist item removal functionality."""

    @patch('sys.stderr')
    def test_remove_blocklist_item_success(self, mock_stderr, mock_client):
        """Test successful blocklist item removal."""
        remove_blocklist_item(mock_client, 1)

        mock_client.remove_from_blocklist.assert_called_once_with(1)

    @patch('sys.stderr')
    def test_remove_blocklist_item_failure(self, mock_stderr, mock_client):
        """Test blocklist item removal failure."""
        mock_client.remove_from_blocklist.side_effect = Exception("Remove failed")

        with pytest.raises(Exception):
            remove_blocklist_item(mock_client, 1)


class TestSystemHealth:
    """Test system health check functionality."""

    @patch('sys.stderr')
    @patch('sys.stdout')
    def test_system_health_with_issues(self, mock_stdout, mock_stderr, mock_client):
        """Test system health check with health issues."""
        system_health(mock_client)

        mock_client.get_health.assert_called_once()
        assert mock_stdout.write.called

    @patch('sys.stderr')
    @patch('sys.stdout')
    def test_system_health_no_issues(self, mock_stdout, mock_stderr, mock_client):
        """Test system health check with no issues."""
        mock_client.get_health.return_value = []

        system_health(mock_client)

        mock_client.get_health.assert_called_once()

    @patch('sys.stderr')
    def test_system_health_with_error(self, mock_stderr, mock_client):
        """Test system health check with API error."""
        mock_client.get_health.side_effect = Exception("API error")

        with pytest.raises(Exception):
            system_health(mock_client)
