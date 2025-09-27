"""Tests for lidarr_api.data_utils module."""

import pytest
import json
import csv
import io
import sys
from unittest.mock import Mock, patch, mock_open
from lidarr_api.data_utils import (
    export_artists_json,
    export_artists_csv,
    export_configuration,
    export_wanted_albums,
    import_artists_from_json,
    import_tags_from_config,
    setup_client
)


@pytest.fixture
def mock_client():
    """Create a mock LidarrClient for testing."""
    client = Mock()
    client.get_all_artists.return_value = [
        {
            'id': 1,
            'foreignArtistId': 'test-id-1',
            'artistName': 'Test Artist 1',
            'sortName': 'Artist 1, Test',
            'disambiguation': '',
            'overview': 'Test overview',
            'artistType': 'Person',
            'status': 'continuing',
            'ended': False,
            'genres': ['Rock', 'Pop'],
            'tags': [1, 2],
            'monitored': True,
            'qualityProfileId': 1,
            'metadataProfileId': 1,
            'path': '/music/test-artist-1',
            'rootFolderPath': '/music'
        },
        {
            'id': 2,
            'foreignArtistId': 'test-id-2',
            'artistName': 'Test Artist 2',
            'sortName': 'Artist 2, Test',
            'disambiguation': 'test',
            'overview': '',
            'artistType': 'Group',
            'status': 'ended',
            'ended': True,
            'genres': ['Jazz'],
            'tags': [],
            'monitored': False,
            'qualityProfileId': 2,
            'metadataProfileId': 1,
            'path': '/music/test-artist-2',
            'rootFolderPath': '/music'
        }
    ]

    client.get_albums_by_artist.return_value = [
        {
            'title': 'Test Album',
            'releaseDate': '2023-01-01',
            'monitored': True,
            'albumType': 'Album',
            'disambiguation': '',
            'foreignAlbumId': 'test-album-id'
        }
    ]

    client.get_system_status.return_value = {'startTime': '2023-01-01T00:00:00Z'}
    client.get_quality_profiles.return_value = [{'id': 1, 'name': 'FLAC'}]
    client.get_metadata_profiles.return_value = [{'id': 1, 'name': 'Standard'}]
    client.get_tags.return_value = [{'id': 1, 'label': 'rock'}, {'id': 2, 'label': 'pop'}]
    client.get_root_folders.return_value = [{'path': '/music'}]
    client.get_import_lists.return_value = [{'id': 1, 'name': 'Test List'}]
    client.get_wanted.return_value = {
        'records': [
            {
                'id': 1,
                'title': 'Wanted Album',
                'releaseDate': '2023-06-01',
                'albumType': 'Album',
                'monitored': True,
                'foreignAlbumId': 'wanted-album-id',
                'artist': {'artistName': 'Test Artist'}
            }
        ]
    }

    return client


class TestDataUtilsExport:
    """Test export functions."""

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_export_artists_json_to_stdout(self, mock_stderr, mock_client):
        """Test exporting artists to stdout in JSON format."""
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            export_artists_json(mock_client)

            # Check that data was written to stdout
            output = mock_stdout.getvalue()
            data = json.loads(output)

            assert len(data) == 2
            assert data[0]['artistName'] == 'Test Artist 1'
            assert data[1]['artistName'] == 'Test Artist 2'

            # Check that status message went to stderr
            stderr_output = mock_stderr.getvalue()
            assert 'Fetching artists...' in stderr_output
            assert 'Exported 2 artists to stdout' in stderr_output

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_export_artists_json_to_file(self, mock_stderr, mock_client):
        """Test exporting artists to file in JSON format."""
        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            export_artists_json(mock_client, 'test.json')

            # Check that file was opened for writing
            mock_file.assert_called_once_with('test.json', 'w', encoding='utf-8')

            # Check stderr message
            stderr_output = mock_stderr.getvalue()
            assert 'Exported 2 artists to test.json' in stderr_output

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_export_artists_json_with_albums(self, mock_stderr, mock_client):
        """Test exporting artists with albums included."""
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            export_artists_json(mock_client, include_albums=True)

            output = mock_stdout.getvalue()
            data = json.loads(output)

            # Check that albums were included
            assert 'albums' in data[0]
            assert len(data[0]['albums']) == 1
            assert data[0]['albums'][0]['title'] == 'Test Album'

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_export_artists_csv_to_stdout(self, mock_stderr, mock_client):
        """Test exporting artists to stdout in CSV format."""
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            export_artists_csv(mock_client)

            output = mock_stdout.getvalue()
            lines = output.strip().split('\n')

            # Check CSV header
            header = lines[0]
            assert 'foreignArtistId' in header
            assert 'artistName' in header

            # Check data rows
            assert len(lines) == 3  # Header + 2 data rows
            assert 'Test Artist 1' in lines[1]
            assert 'Test Artist 2' in lines[2]

            # Check stderr message
            stderr_output = mock_stderr.getvalue()
            assert 'Exported 2 artists to stdout' in stderr_output

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_export_configuration_to_stdout(self, mock_stderr, mock_client):
        """Test exporting configuration to stdout."""
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            export_configuration(mock_client)

            output = mock_stdout.getvalue()
            data = json.loads(output)

            # Check configuration structure
            assert 'quality_profiles' in data
            assert 'metadata_profiles' in data
            assert 'tags' in data
            assert 'root_folders' in data
            assert 'import_lists' in data

            # Check stderr messages
            stderr_output = mock_stderr.getvalue()
            assert 'Exporting configuration...' in stderr_output
            assert 'Exported 1 quality profiles' in stderr_output

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_export_wanted_albums_csv_to_stdout(self, mock_stderr, mock_client):
        """Test exporting wanted albums in CSV format to stdout."""
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            export_wanted_albums(mock_client, format_type='csv')

            output = mock_stdout.getvalue()
            lines = output.strip().split('\n')

            # Check CSV structure
            assert len(lines) == 2  # Header + 1 data row
            assert 'artistName' in lines[0]
            assert 'albumTitle' in lines[0]
            assert 'Test Artist' in lines[1]
            assert 'Wanted Album' in lines[1]


class TestDataUtilsImport:
    """Test import functions."""

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_import_artists_from_stdin(self, mock_stderr, mock_client):
        """Test importing artists from stdin."""
        test_data = [
            {
                'foreignArtistId': 'new-artist-1',
                'artistName': 'New Artist 1',
                'monitored': True
            }
        ]

        mock_client.get_all_artists.return_value = []  # No existing artists
        mock_client.get_quality_profiles.return_value = [{'id': 1}]
        mock_client.get_metadata_profiles.return_value = [{'id': 1}]
        mock_client.get_root_folders.return_value = [{'path': '/music'}]

        with patch('sys.stdin', io.StringIO(json.dumps(test_data))):
            import_artists_from_json(mock_client, dry_run=True)

            # Check stderr output
            stderr_output = mock_stderr.getvalue()
            assert 'Reading artists from stdin...' in stderr_output
            assert 'Would add: New Artist 1' in stderr_output

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_import_artists_from_file(self, mock_stderr, mock_client):
        """Test importing artists from file."""
        test_data = [
            {
                'foreignArtistId': 'new-artist-1',
                'artistName': 'New Artist 1',
                'monitored': True
            }
        ]

        mock_client.get_all_artists.return_value = []
        mock_client.get_quality_profiles.return_value = [{'id': 1}]
        mock_client.get_metadata_profiles.return_value = [{'id': 1}]
        mock_client.get_root_folders.return_value = [{'path': '/music'}]

        mock_file = mock_open(read_data=json.dumps(test_data))
        with patch('builtins.open', mock_file):
            import_artists_from_json(mock_client, 'test.json', dry_run=True)

            # Check file was opened
            mock_file.assert_called_once_with('test.json', 'r', encoding='utf-8')

            # Check stderr output
            stderr_output = mock_stderr.getvalue()
            assert 'Reading artists from test.json...' in stderr_output

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_import_tags_from_stdin(self, mock_stderr, mock_client):
        """Test importing tags from stdin."""
        test_config = {
            'tags': [
                {'label': 'newtag1'},
                {'label': 'newtag2'}
            ]
        }

        mock_client.get_tags.return_value = []  # No existing tags

        with patch('sys.stdin', io.StringIO(json.dumps(test_config))):
            import_tags_from_config(mock_client, dry_run=True)

            stderr_output = mock_stderr.getvalue()
            assert 'Reading configuration from stdin...' in stderr_output
            assert 'Would create tag: newtag1' in stderr_output
            assert 'Would create tag: newtag2' in stderr_output


class TestSetupClient:
    """Test client setup function."""

    @patch('lidarr_api.data_utils.LidarrClient')
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

    @patch('lidarr_api.data_utils.Config')
    @patch('lidarr_api.data_utils.LidarrClient')
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
