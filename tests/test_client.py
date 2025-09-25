# flake8: noqa pylint: disable=W,C,R

import pytest
import requests
import responses
import time
import logging
from datetime import datetime
from lidarr_api import LidarrClient
from tests.config import LIDARR_URL, LIDARR_API_KEY


# Fixtures for both test suites
@pytest.fixture
def client():
    return LidarrClient(base_url=LIDARR_URL, api_key=LIDARR_API_KEY)


@pytest.fixture
def mock_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


class TestLidarrClientUnit:
    """Unit tests using mocked responses"""

    def test_client_initialization(self, client):
        assert client.base_url == LIDARR_URL
        assert client.api_key == LIDARR_API_KEY
        assert client.session.headers['X-Api-Key'] == LIDARR_API_KEY
        assert client.session.headers['Content-Type'] == 'application/json'

    def test_get_system_status(self, client, mock_responses):
        expected_response = {
            "version": "1.0.2.2587",
            "buildTime": "2023-09-18T10:00:00Z",
            "isDebug": False,
            "isProduction": True,
            "isAdmin": True,
            "isUserInteractive": True,
            "startupPath": "/app/lidarr",
            "appData": "/config",
            "osVersion": "debian 11.0",
            "isNetCore": True,
            "isMono": False,
            "isLinux": True,
            "isOsx": False,
            "isWindows": False,
            "mode": "console",
            "branch": "master",
            "authentication": "none",
            "sqliteVersion": "3.35.5",
            "migrationVersion": 189
        }

        mock_responses.add(
            responses.GET,
            f'{LIDARR_URL}/api/v1/system/status',
            json=expected_response,
            status=200
        )

        response = client.get_system_status()
        assert response == expected_response

    def test_search_artist(self, client, mock_responses):
        expected_response = [{
            "id": 123,
            "artistName": "The Beatles",
            "overview": "The Beatles were an English rock band...",
            "status": "ended"
        }]

        mock_responses.add(
            responses.GET,
            f'{LIDARR_URL}/api/v1/artist/lookup',
            json=expected_response,
            status=200
        )

        response = client.search_artist('The Beatles')
        assert response == expected_response

    def test_get_quality_profiles(self, client, mock_responses):
        expected_response = [{
            "id": 1,
            "name": "FLAC",
            "cutoff": {"id": 1, "name": "FLAC"},
            "items": []
        }]

        mock_responses.add(
            responses.GET,
            f'{LIDARR_URL}/api/v1/qualityprofile',
            json=expected_response,
            status=200
        )

        response = client.get_quality_profiles()
        assert response == expected_response

    def test_get_wanted(self, client, mock_responses):
        expected_response = {
            "page": 1,
            "pageSize": 10,
            "sortKey": "releaseDate",
            "sortDirection": "descending",
            "totalRecords": 1,
            "records": [{
                "id": 123,
                "title": "Some Album",
                "artistId": 456,
                "releaseDate": "2025-09-18"
            }]
        }

        mock_responses.add(
            responses.GET,
            f'{LIDARR_URL}/api/v1/wanted/missing',
            json=expected_response,
            status=200
        )

        response = client.get_wanted()
        assert response == expected_response
        assert response["page"] == 1
        assert response["pageSize"] == 10

    def test_get_metadata(self, client, mock_responses):
        expected_response = {
            "id": 123,
            "lastInfoSync": "2023-09-18T10:00:00Z",
            "foreignArtistId": "abc123",
            "sizeOnDisk": 1234567,
            "path": "/music/TheArtist"
        }

        mock_responses.add(
            responses.GET,
            f'{LIDARR_URL}/api/v1/artistmetadata/123',
            json=expected_response,
            status=200
        )

        response = client.get_metadata(123)
        assert response == expected_response

    def test_search_album(self, client, mock_responses):
        expected_response = {
            "id": 789,
            "name": "AlbumSearch",
            "status": "queued"
        }

        mock_responses.add(
            responses.POST,
            f'{LIDARR_URL}/api/v1/command',
            json=expected_response,
            status=200
        )

        response = client.search_album(456)
        assert response == expected_response

    def test_get_root_folders(self, client, mock_responses):
        expected_response = [{
            "id": 1,
            "path": "/music",
            "accessible": True,
            "freeSpace": 1234567890
        }]

        mock_responses.add(
            responses.GET,
            f'{LIDARR_URL}/api/v1/rootfolder',
            json=expected_response,
            status=200
        )

        response = client.get_root_folders()
        assert response == expected_response

    def test_get_queue(self, client, mock_responses):
        expected_response = {
            "page": 1,
            "pageSize": 10,
            "totalRecords": 1,
            "records": [{
                "id": 123,
                "albumId": 456,
                "status": "downloading",
                "title": "Album Title"
            }]
        }

        mock_responses.add(
            responses.GET,
            f'{LIDARR_URL}/api/v1/queue',
            json=expected_response,
            status=200
        )

        response = client.get_queue()
        assert response == expected_response

    def test_get_album_releases(self, client, mock_responses):
        expected_response = [{
            "id": 1,
            "guid": "123-456",
            "quality": {"quality": {"id": 1, "name": "FLAC"}},
            "qualityWeight": 1,
            "age": 0,
            "seeders": 0,
            "indexer": "Test Indexer",
            "title": "Test Album Release"
        }]

        mock_responses.add(
            responses.GET,
            f'{LIDARR_URL}/api/v1/album/1/releases',
            json=expected_response,
            status=200
        )

        response = client.get_album_releases(1)
        assert response == expected_response

    def test_update_artist_monitor(self, client, mock_responses):
        artist_data = {
            "id": 1,
            "artistName": "Test Artist",
            "monitored": False
        }

        # Mock get artist request
        mock_responses.add(
            responses.GET,
            f'{LIDARR_URL}/api/v1/artist/1',
            json=artist_data,
            status=200
        )

        # Mock update request
        mock_responses.add(
            responses.PUT,
            f'{LIDARR_URL}/api/v1/artist/1',
            json={**artist_data, "monitored": True},
            status=200
        )

        response = client.update_artist_monitor(1, True)
        assert response["monitored"] is True

    def test_get_tags(self, client, mock_responses):
        expected_response = [
            {"id": 1, "label": "test-tag"},
            {"id": 2, "label": "another-tag"}
        ]

        mock_responses.add(
            responses.GET,
            f'{LIDARR_URL}/api/v1/tag',
            json=expected_response,
            status=200
        )

        response = client.get_tags()
        assert response == expected_response

    def test_add_tag(self, client, mock_responses):
        expected_response = {"id": 1, "label": "new-tag"}

        mock_responses.add(
            responses.POST,
            f'{LIDARR_URL}/api/v1/tag',
            json=expected_response,
            status=200
        )

        response = client.add_tag("new-tag")
        assert response == expected_response

    def test_get_blocklist(self, client, mock_responses):
        expected_response = {
            "page": 1,
            "pageSize": 10,
            "total": 1,
            "records": [{
                "id": 1,
                "sourceTitle": "Test Release",
                "quality": {"quality": {"id": 1, "name": "FLAC"}},
                "date": "2025-09-18T00:00:00Z"
            }]
        }

        mock_responses.add(
            responses.GET,
            f'{LIDARR_URL}/api/v1/blocklist',
            json=expected_response,
            status=200
        )

        response = client.get_blocklist()
        assert response == expected_response

    def test_rate_limiting(self, client, mock_responses):
        """Test that rate limiting is working"""
        expected_response = {"status": "ok"}

        # Configure client with 2 requests per second
        client = LidarrClient(LIDARR_URL, LIDARR_API_KEY, rate_limit_per_second=2.0)

        mock_responses.add(
            responses.GET,
            f'{LIDARR_URL}/api/v1/system/status',
            json=expected_response,
            status=200
        )

        # Make three quick requests
        start_time = time.time()
        client.get_system_status()
        client.get_system_status()
        client.get_system_status()
        end_time = time.time()

        # Should take at least 1 second for 3 requests at 2 req/sec
        assert end_time - start_time >= 1.0

    def test_retry_mechanism(self, client, mock_responses):
        """Test that retry mechanism works for failed requests"""
        expected_response = {"status": "ok"}

        # Configure client with retries
        client = LidarrClient(LIDARR_URL, LIDARR_API_KEY, retry_total=2)

        # Add a failed response followed by a successful one
        mock_responses.add(
            responses.GET,
            f'{LIDARR_URL}/api/v1/system/status',
            json={"error": "Server Error"},
            status=500
        )

        mock_responses.add(
            responses.GET,
            f'{LIDARR_URL}/api/v1/system/status',
            json=expected_response,
            status=200
        )

        response = client.get_system_status()
        assert response == expected_response

    def test_timeout_setting(self, client, mock_responses):
        """Test that timeout is properly set"""
        client = LidarrClient(LIDARR_URL, LIDARR_API_KEY, timeout=1)

        mock_responses.add(
            responses.GET,
            f'{LIDARR_URL}/api/v1/system/status',
            body=requests.exceptions.Timeout()
        )

        with pytest.raises(requests.exceptions.Timeout):
            client.get_system_status()

    def test_logging(self, client, caplog):
        """Test that logging is working"""
        client.logger.setLevel(logging.DEBUG)

        with caplog.at_level(logging.DEBUG):
            try:
                # Make a request that will fail
                client.get_system_status()
            except:
                pass

            # Check that debug logs were created
            assert any("Making GET request to" in record.message
                       for record in caplog.records)


class TestLidarrClientIntegration:
    """Integration tests using actual Lidarr server"""

    @pytest.mark.integration
    def test_system_status_integration(self, client):
        """Test that we can connect to the actual Lidarr server and get system status"""
        response = client.get_system_status()
        assert isinstance(response, dict)
        assert 'version' in response
        assert 'buildTime' in response

    @pytest.mark.integration
    def test_artist_search_integration(self, client):
        """Test artist search against the actual Lidarr server"""
        response = client.search_artist('The Beatles')
        assert isinstance(response, list)
        if response:  # Some results were found
            assert 'artistName' in response[0]
            assert 'id' in response[0]

    @pytest.mark.integration
    def test_get_calendar_integration(self, client):
        """Test calendar retrieval from the actual Lidarr server"""
        response = client.get_calendar()
        assert isinstance(response, list)
        # Calendar might be empty, but should still return a list
        if response:
            assert 'title' in response[0] or 'artistName' in response[0]

    @pytest.mark.integration
    def test_quality_profiles_integration(self, client):
        """Test retrieving quality profiles from the actual server"""
        response = client.get_quality_profiles()
        assert isinstance(response, list)
        if response:
            assert "name" in response[0]
            assert "id" in response[0]

    @pytest.mark.integration
    def test_wanted_integration(self, client):
        """Test retrieving wanted/missing albums from the actual server"""
        try:
            response = client.get_wanted()
            assert isinstance(response, dict)
            assert 'records' in response
            assert isinstance(response['records'], list)
        except requests.exceptions.Timeout:
            pytest.skip("Wanted/missing endpoint timed out - server may be busy")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 500:
                pytest.skip("Wanted/missing endpoint not available or requires configuration")
            raise

    @pytest.mark.integration
    def test_import_lists_integration(self, client):
        """Test retrieving import lists from the actual server"""
        response = client.get_import_lists()
        assert isinstance(response, list)

    @pytest.mark.integration
    def test_metadata_integration(self, client):
        """Test getting metadata for the first available artist"""
        # First get an artist to test with
        artists = client.search_artist('The Beatles')
        if artists:
            # Get the first artist ID
            artist_id = artists[0]['id']
            # Get the full artist details to get the metadata ID
            artist = client.get_artist(artist_id)
            if artist and 'artistMetadataId' in artist:
                metadata_id = artist['artistMetadataId']
                response = client.get_metadata(metadata_id)
                assert isinstance(response, dict)
                assert 'id' in response
            else:
                pytest.skip("No artist metadata ID available")

    @pytest.mark.integration
    def test_root_folders_integration(self, client):
        """Test retrieving root folders"""
        response = client.get_root_folders()
        assert isinstance(response, list)
        if response:
            assert 'path' in response[0]
            assert 'accessible' in response[0]

    @pytest.mark.integration
    def test_queue_integration(self, client):
        """Test retrieving download queue"""
        response = client.get_queue()
        assert isinstance(response, dict)
        assert 'records' in response
        assert isinstance(response['records'], list)

    @pytest.mark.integration
    def test_disk_space_integration(self, client):
        """Test retrieving disk space information"""
        response = client.get_disk_space()
        assert isinstance(response, list)
        if response:
            assert 'path' in response[0]
            assert 'freeSpace' in response[0]

    @pytest.mark.integration
    def test_history_integration(self, client):
        """Test retrieving download history"""
        response = client.get_history()
        assert isinstance(response, dict)
        assert 'records' in response

    @pytest.mark.integration
    def test_album_releases_integration(self, client):
        """Test getting album releases from the actual server"""
        # First get an artist to test with
        artists = client.search_artist('The Beatles')
        if not artists:
            pytest.skip("No artists found for release test")

        artist_id = artists[0]['id']
        albums = client.get_albums_by_artist(artist_id)
        if not albums:
            pytest.skip("No albums found for release test")

        album_id = albums[0]['id']
        try:
            response = client.get_album_releases(album_id)
            assert isinstance(response, list)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                pytest.skip("No releases available for the album")
            raise

    @pytest.mark.integration
    def test_tags_integration(self, client):
        """Test tag management"""
        # Create a new tag
        tag_name = "test-tag-" + datetime.now().strftime("%Y%m%d%H%M%S")
        new_tag = client.add_tag(tag_name)
        assert new_tag['label'] == tag_name

        # Get tag details
        tag_details = client.get_tag_details(new_tag['id'])
        assert isinstance(tag_details, dict)

        # Clean up - delete the tag
        client.delete_tag(new_tag['id'])

        # Verify tag list
        tags = client.get_tags()
        assert all(tag['label'] != tag_name for tag in tags)

    @pytest.mark.integration
    def test_blocklist_integration(self, client):
        """Test blocklist functionality"""
        try:
            response = client.get_blocklist()
            assert isinstance(response, dict)
            assert 'records' in response
            assert isinstance(response['records'], list)
        except requests.exceptions.Timeout:
            pytest.skip("Blocklist endpoint timed out - server may be busy")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in (404, 500):
                pytest.skip("Blocklist feature not available or requires configuration")
            raise
        except requests.exceptions.RetryError as e:
            if 'too many 500 error responses' in str(e):
                pytest.skip("Blocklist endpoint is returning server errors")
            raise
