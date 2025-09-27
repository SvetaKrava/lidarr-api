"""Tests for lidarr_api.cli module."""

import pytest
from unittest.mock import Mock, patch
from lidarr_api.cli import format_overview, prepare_artist_data


class TestFormatOverview:
    """Test text formatting function."""

    def test_format_overview_basic(self):
        """Test basic text formatting."""
        text = "This is a long text that should be wrapped to multiple lines when it exceeds the specified width limit"
        result = format_overview(text, width=30)

        lines = result.split('\n')
        assert len(lines) > 1
        assert all(len(line) <= 30 for line in lines)

    def test_format_overview_empty_text(self):
        """Test formatting empty text."""
        result = format_overview("")
        assert result == ""

    def test_format_overview_none_text(self):
        """Test formatting None text."""
        result = format_overview(None)
        assert result == ""

    def test_format_overview_short_text(self):
        """Test formatting text shorter than width."""
        text = "Short text"
        result = format_overview(text, width=50)
        assert result == text


class TestPrepareArtistData:
    """Test artist data preparation function."""

    def test_prepare_artist_data_basic(self):
        """Test preparing basic artist data."""
        search_result = {
            'artistName': 'Test Artist',
            'foreignArtistId': 'test-id',
            'images': [],
            'status': 'continuing'
        }

        root_folder = {'id': 1, 'path': '/music'}
        quality_profile = {'id': 1, 'name': 'FLAC'}
        metadata_profile = {'id': 1, 'name': 'Standard'}
        monitored = True
        album_monitor_option = 1
        tags = []

        result = prepare_artist_data(
            search_result, root_folder, quality_profile, metadata_profile,
            monitored, album_monitor_option, tags
        )

        assert result['artistName'] == 'Test Artist'
        assert result['foreignArtistId'] == 'test-id'
        assert result['rootFolderPath'] == '/music'
        assert result['qualityProfileId'] == 1
        assert result['metadataProfileId'] == 1
        assert result['monitored'] is True
        assert result['albumFolder'] is True

    def test_prepare_artist_data_with_tags(self):
        """Test preparing artist data with tags."""
        search_result = {
            'artistName': 'Test Artist',
            'foreignArtistId': 'test-id',
            'images': [],
            'status': 'continuing'
        }

        root_folder = {'id': 1, 'path': '/music'}
        quality_profile = {'id': 1, 'name': 'FLAC'}
        metadata_profile = {'id': 1, 'name': 'Standard'}
        monitored = True
        album_monitor_option = 1
        tags = [{'id': 1}, {'id': 2}, {'id': 3}]

        result = prepare_artist_data(
            search_result, root_folder, quality_profile, metadata_profile,
            monitored, album_monitor_option, tags
        )

        assert result['tags'] == [1, 2, 3]
