"""Tests for lidarr_api.library_manager module."""

import pytest
from unittest.mock import Mock, patch
from lidarr_api.library_manager import (
    setup_client, list_wanted_albums, search_wanted_albums,
    list_quality_profiles, list_metadata_profiles, list_import_lists,
    test_import_list, view_queue, remove_queue_item
)


@pytest.fixture
def mock_client():
    """Create a mock LidarrClient for testing."""
    client = Mock()

    # Mock wanted albums data
    client.get_wanted_albums.return_value = {
        'records': [
            {
                'id': 1,
                'title': 'Missing Album',
                'releaseDate': '2023-01-01',
                'monitored': True,
                'artist': {'artistName': 'Test Artist 1'}
            }
        ],
        'totalRecords': 1
    }

    # Mock quality profiles
    client.get_quality_profiles.return_value = [
        {'id': 1, 'name': 'FLAC', 'upgradeAllowed': True},
        {'id': 2, 'name': 'MP3-320', 'upgradeAllowed': False}
    ]

    # Mock metadata profiles
    client.get_metadata_profiles.return_value = [
        {'id': 1, 'name': 'Standard'},
        {'id': 2, 'name': 'Minimal'}
    ]

    # Mock import lists
    client.get_import_lists.return_value = [
        {
            'id': 1,
            'name': 'Test List',
            'enable': True,
            'implementation': 'SpotifyPlaylist'
        }
    ]

    # Mock queue data
    client.get_queue.return_value = {
        'records': [
            {
                'id': 1,
                'title': 'Album in Queue',
                'status': 'downloading',
                'size': 1000000000,
                'sizeleft': 500000000,
                'artist': {'artistName': 'Queue Artist'}
            }
        ],
        'totalRecords': 1
    }

    # Mock command responses
    client.test_import_list.return_value = {'success': True}
    client.remove_from_queue.return_value = {'success': True}
    client.search_wanted_albums.return_value = {'id': 1}

    return client


class TestSetupClient:
    """Test client setup function."""

    @patch('lidarr_api.library_manager.LidarrClient')
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


class TestListWantedAlbums:
    """Test wanted albums listing functionality."""

    @patch('sys.stderr')
    @patch('sys.stdout')
    def test_list_wanted_albums_table_format(self, mock_stdout, mock_stderr, mock_client):
        """Test listing wanted albums with table format."""
        from argparse import Namespace

        args = Namespace(format='table', limit=100)

        list_wanted_albums(mock_client, args)

        mock_client.get_wanted_albums.assert_called_once()
        assert mock_stdout.write.called

    @patch('sys.stderr')
    @patch('sys.stdout')
    def test_list_wanted_albums_json_format(self, mock_stdout, mock_stderr, mock_client):
        """Test listing wanted albums with JSON format."""
        from argparse import Namespace

        args = Namespace(format='json', limit=50)

        list_wanted_albums(mock_client, args)

        mock_client.get_wanted_albums.assert_called_once()
        assert mock_stdout.write.called


class TestSearchWantedAlbums:
    """Test wanted album search functionality."""

    @patch('sys.stderr')
    def test_search_wanted_albums_default_limit(self, mock_stderr, mock_client):
        """Test searching wanted albums with default limit."""
        search_wanted_albums(mock_client)

        mock_client.get_wanted_albums.assert_called_once()

    @patch('sys.stderr')
    def test_search_wanted_albums_custom_limit(self, mock_stderr, mock_client):
        """Test searching wanted albums with custom limit."""
        search_wanted_albums(mock_client, limit=5)

        mock_client.get_wanted_albums.assert_called_once()


class TestListQualityProfiles:
    """Test quality profiles listing functionality."""

    @patch('sys.stderr')
    @patch('sys.stdout')
    def test_list_quality_profiles(self, mock_stdout, mock_stderr, mock_client):
        """Test listing quality profiles."""
        list_quality_profiles(mock_client)

        mock_client.get_quality_profiles.assert_called_once()
        assert mock_stdout.write.called


class TestListMetadataProfiles:
    """Test metadata profiles listing functionality."""

    @patch('sys.stderr')
    @patch('sys.stdout')
    def test_list_metadata_profiles(self, mock_stdout, mock_stderr, mock_client):
        """Test listing metadata profiles."""
        list_metadata_profiles(mock_client)

        mock_client.get_metadata_profiles.assert_called_once()
        assert mock_stdout.write.called


class TestListImportLists:
    """Test import lists listing functionality."""

    @patch('sys.stderr')
    @patch('sys.stdout')
    def test_list_import_lists(self, mock_stdout, mock_stderr, mock_client):
        """Test listing import lists."""
        list_import_lists(mock_client)

        mock_client.get_import_lists.assert_called_once()
        assert mock_stdout.write.called


class TestTestImportList:
    """Test import list testing functionality."""

    @patch('sys.stderr')
    def test_test_import_list_success(self, mock_stderr, mock_client):
        """Test successful import list test."""
        test_import_list(mock_client, 1)

        mock_client.test_import_list.assert_called_once_with(1)

    @patch('sys.stderr')
    def test_test_import_list_failure(self, mock_stderr, mock_client):
        """Test import list test failure."""
        mock_client.test_import_list.side_effect = Exception("Test failed")

        with pytest.raises(Exception):
            test_import_list(mock_client, 1)


class TestViewQueue:
    """Test queue viewing functionality."""

    @patch('sys.stderr')
    @patch('sys.stdout')
    def test_view_queue_table_format(self, mock_stdout, mock_stderr, mock_client):
        """Test viewing queue with table format."""
        from argparse import Namespace

        args = Namespace(format='table', page=1, page_size=20)

        view_queue(mock_client, args)

        mock_client.get_queue.assert_called_once()
        assert mock_stdout.write.called

    @patch('sys.stderr')
    @patch('sys.stdout')
    def test_view_queue_json_format(self, mock_stdout, mock_stderr, mock_client):
        """Test viewing queue with JSON format."""
        from argparse import Namespace

        args = Namespace(format='json', page=1, page_size=10)

        view_queue(mock_client, args)

        mock_client.get_queue.assert_called_once()
        assert mock_stdout.write.called


class TestRemoveQueueItem:
    """Test queue item removal functionality."""

    @patch('sys.stderr')
    @patch('builtins.input', return_value='y')
    def test_remove_queue_item_confirmed(self, mock_input, mock_stderr, mock_client):
        """Test removing queue item with confirmation."""
        from argparse import Namespace

        args = Namespace(force=False)

        remove_queue_item(mock_client, 1, args)

        mock_client.remove_from_queue.assert_called_once_with(1)

    @patch('sys.stderr')
    @patch('builtins.input', return_value='n')
    def test_remove_queue_item_cancelled(self, mock_input, mock_stderr, mock_client):
        """Test cancelling queue item removal."""
        from argparse import Namespace

        args = Namespace(force=False)

        remove_queue_item(mock_client, 1, args)

        mock_client.remove_from_queue.assert_not_called()

    @patch('sys.stderr')
    def test_remove_queue_item_force(self, mock_stderr, mock_client):
        """Test force removing queue item without confirmation."""
        from argparse import Namespace

        args = Namespace(force=True)

        remove_queue_item(mock_client, 1, args)

        mock_client.remove_from_queue.assert_called_once_with(1)
