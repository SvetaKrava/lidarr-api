#!/usr/bin/env python3
"""
Lidarr artist search and management script.

This script provides a command-line interface for searching, adding, and managing
artists in Lidarr. It includes features like retry logic, configuration management,
and interactive artist selection.
"""

import argparse
import sys
import textwrap
import traceback
import time
import logging
import requests
from lidarr_api import LidarrClient
from lidarr_api.config import Config


def format_overview(text, width=70):
    """Format text by wrapping it to specified width."""
    if not text:
        return ""
    return "\n".join(textwrap.wrap(text, width=width))


def retry_with_backoff(func, max_retries=3, initial_wait=2.0, backoff_factor=2.0):
    """Retry a function with exponential backoff."""
    wait_time = initial_wait
    last_exception = None

    for attempt in range(max_retries):
        try:
            return func()
        except (KeyboardInterrupt, SystemExit):  # pylint: disable=try-except-raise
            raise  # Don't retry system exceptions
        except (requests.exceptions.RequestException, ConnectionError, TimeoutError) as e:
            last_exception = e
            if attempt < max_retries - 1:  # Don't sleep on the last attempt
                print(
                    f"\nAttempt {attempt + 1} failed, retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                wait_time *= backoff_factor

    raise last_exception


def get_root_folder_selection(client, defaults=None):
    """Get user selection of root folder."""
    try:
        print("\nFetching available root folders...")
        root_folders = client.get_root_folders()

        if not root_folders:
            print("No root folders configured in Lidarr!")
            return None

        # If using defaults and a default path exists, find it
        if defaults and 'root_folder_path' in defaults:
            for folder in root_folders:
                if folder['path'] == defaults['root_folder_path']:
                    print(f"\nUsing default root folder: {folder['path']}")
                    return folder

        print("\nAvailable root folders:")
        for idx, folder in enumerate(root_folders, 1):
            free_space = folder.get('freeSpace', 0) / \
                (1024*1024*1024)  # Convert to GB
            print(f"{idx}. {folder['path']} ({free_space:.2f} GB free)")

        while True:
            try:
                selection = input(
                    "\nSelect root folder number (or 'q' to quit): ")
                if selection.lower() == 'q':
                    return None

                selected_idx = int(selection)
                if 1 <= selected_idx <= len(root_folders):
                    return root_folders[selected_idx - 1]
                else:
                    print(
                        f"Please enter a number between 1 and {len(root_folders)}")
            except ValueError:
                print("Please enter a valid number or 'q' to quit")
    except (requests.exceptions.RequestException, ConnectionError, TimeoutError, KeyError) as e:
        print(f"Error fetching root folders: {str(e)}")
        return None


def get_quality_profile_selection(client, defaults=None):
    """Get user selection of quality profile."""
    try:
        print("\nFetching quality profiles...")
        profiles = client.get_quality_profiles()

        if not profiles:
            print("No quality profiles found in Lidarr!")
            return None

        # If using defaults and a default profile exists, find it
        if defaults and 'quality_profile_id' in defaults:
            for profile in profiles:
                if profile['id'] == defaults['quality_profile_id']:
                    print(
                        f"\nUsing default quality profile: {profile['name']}")
                    return profile

        print("\nAvailable quality profiles:")
        for idx, profile in enumerate(profiles, 1):
            print(f"{idx}. {profile['name']}")

        while True:
            try:
                selection = input(
                    "\nSelect quality profile number (or 'q' to quit): ")
                if selection.lower() == 'q':
                    return None

                selected_idx = int(selection)
                if 1 <= selected_idx <= len(profiles):
                    return profiles[selected_idx - 1]
                else:
                    print(
                        f"Please enter a number between 1 and {len(profiles)}")
            except ValueError:
                print("Please enter a valid number or 'q' to quit")
    except (requests.exceptions.RequestException, ConnectionError, TimeoutError, KeyError) as e:
        print(f"Error fetching quality profiles: {str(e)}")
        return None


def get_metadata_profile_selection(client, defaults=None):
    """Get user selection of metadata profile."""
    try:
        print("\nFetching metadata profiles...")
        profiles = client.get_metadata_profiles()

        if not profiles:
            print("No metadata profiles found in Lidarr!")
            return None

        # If using defaults and a default profile exists, find it
        if defaults and 'metadata_profile_id' in defaults:
            for profile in profiles:
                if profile['id'] == defaults['metadata_profile_id']:
                    print(
                        f"\nUsing default metadata profile: {profile['name']}")
                    return profile

        print("\nAvailable metadata profiles:")
        for idx, profile in enumerate(profiles, 1):
            print(f"{idx}. {profile['name']}")

        while True:
            try:
                selection = input(
                    "\nSelect metadata profile number (or 'q' to quit): ")
                if selection.lower() == 'q':
                    return None

                selected_idx = int(selection)
                if 1 <= selected_idx <= len(profiles):
                    return profiles[selected_idx - 1]
                else:
                    print(
                        f"Please enter a number between 1 and {len(profiles)}")
            except ValueError:
                print("Please enter a valid number or 'q' to quit")
    except (requests.exceptions.RequestException, ConnectionError, TimeoutError, KeyError) as e:
        print(f"Error fetching metadata profiles: {str(e)}")
        return None


def get_monitored_option(defaults=None):
    """Get user selection for monitored status."""
    if defaults and 'monitored' in defaults:
        monitored = defaults['monitored']
        print(
            f"\nUsing default monitored setting: {'Yes' if monitored else 'No'}")
        return monitored

    print("\nMonitor this artist?")
    print("1. Yes")
    print("2. No")

    while True:
        selection = input("\nEnter option (or 'q' to quit): ")
        if selection.lower() == 'q':
            return None
        try:
            option = int(selection)
            if option in [1, 2]:
                return option == 1
            print("Please enter 1 or 2")
        except ValueError:
            print("Please enter a valid number")


def get_album_monitor_option(defaults=None):
    """Get user selection for album monitoring."""
    if defaults and 'album_monitor_option' in defaults:
        option = defaults['album_monitor_option']
        monitor_text = {
            1: "All albums",
            2: "Future albums only",
            3: "None"
        }[option]
        print(f"\nUsing default album monitoring: {monitor_text}")
        return option

    print("\nSelect which albums to monitor:")
    print("1. All albums")
    print("2. Future albums only")
    print("3. None")

    while True:
        selection = input("\nEnter option (or 'q' to quit): ")
        if selection.lower() == 'q':
            return None
        try:
            option = int(selection)
            if 1 <= option <= 3:
                return option
            print("Please enter a number between 1 and 3")
        except ValueError:
            print("Please enter a valid number")


def get_tags_selection(client, defaults=None):
    """Get user selection of tags."""
    try:
        print("\nFetching available tags...")
        tags = client.get_tags()
        selected_tags = []

        # If using defaults and default tags exist, find them
        if defaults and 'tag_ids' in defaults:
            for tag in tags:
                if tag['id'] in defaults['tag_ids']:
                    selected_tags.append(tag)
            if selected_tags:
                print("\nUsing default tags:", ", ".join(
                    t['label'] for t in selected_tags))
                return selected_tags

        while True:
            print("\nCurrent tags:", ", ".join(
                [t['label'] for t in selected_tags]) or "None")
            print("\nAvailable tags:")
            print("0. Done selecting tags")
            print("N. Create new tag")
            for idx, tag in enumerate(tags, 1):
                if tag not in selected_tags:
                    print(f"{idx}. {tag['label']}")

            selection = input(
                "\nSelect tag number, 'N' for new, or 0 when done (or 'q' to quit): "
            ).strip()
            if selection.lower() == 'q':
                return None
            if selection == '0':
                return selected_tags
            if selection.lower() == 'n':
                new_tag = input("Enter new tag name: ").strip()
                if new_tag:
                    try:
                        tag = client.add_tag(new_tag)
                        tags.append(tag)
                        selected_tags.append(tag)
                    except (requests.exceptions.RequestException, ConnectionError,
                            TimeoutError, ValueError) as e:
                        print(f"Error creating tag: {str(e)}")
                continue

            try:
                idx = int(selection)
                if 1 <= idx <= len(tags):
                    tag = tags[idx - 1]
                    if tag not in selected_tags:
                        selected_tags.append(tag)
                else:
                    print(f"Please enter a number between 0 and {len(tags)}")
            except ValueError:
                print("Please enter a valid number, 'N', or 'q' to quit")
    except (requests.exceptions.RequestException, ConnectionError, TimeoutError, KeyError) as e:
        print(f"Error fetching tags: {str(e)}")
        return None


def prepare_artist_data(
    artist_info,
    root_folder,
    quality_profile,
    metadata_profile,
    monitored,
    album_monitor_option,
    tags
):
    """Prepare artist data for adding to Lidarr."""
    monitor_options = {
        1: {"monitored": True, "albumFolder": True, "monitor": "all"},
        2: {"monitored": True, "albumFolder": True, "monitor": "future"},
        3: {"monitored": False, "albumFolder": True, "monitor": "none"}
    }

    monitor_settings = monitor_options[album_monitor_option]

    artist_data = {
        "artistName": artist_info["artistName"],
        "foreignArtistId": artist_info["foreignArtistId"],
        "qualityProfileId": quality_profile["id"],
        # Now using selected metadata profile
        "metadataProfileId": metadata_profile["id"],
        "rootFolderPath": root_folder["path"],
        "monitored": monitored,
        "albumFolder": monitor_settings["albumFolder"],
        "monitor": monitor_settings["monitor"],
        "tags": [tag["id"] for tag in (tags or [])],
        "addOptions": {
            "monitor": monitor_settings["monitor"],
            "searchForMissingAlbums": monitored
        }
    }

    # Add optional fields if they exist in artist_info
    for field in ["overview", "disambiguation", "artistType"]:
        if field in artist_info:
            artist_data[field] = artist_info[field]

    return artist_data


def main():
    """Main function that handles command-line interface and artist search workflow."""
    parser = argparse.ArgumentParser(
        description='Search for an artist in Lidarr')
    parser.add_argument(
        'artist_name',
        help='Name of the artist to search for'
    )
    parser.add_argument(
        '--url',
        help='Lidarr server URL (default: from config or http://localhost:8686)'
    )
    parser.add_argument(
        '--api-key',
        help='Lidarr API key (default: from config)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=60,
        help='Timeout in seconds for API requests'
    )
    parser.add_argument(
        '--retries',
        type=int,
        default=3,
        help='Number of retries for failed requests'
    )
    parser.add_argument(
        '--force-search',
        action='store_true',
        help='Force search for albums after adding artist'
    )
    parser.add_argument(
        '--use-defaults',
        action='store_true',
        help='Use saved defaults for artist addition'
    )
    parser.add_argument(
        '--save-defaults',
        action='store_true',
        help='Save selections as defaults'
    )
    parser.add_argument(
        '--config',
        help='Path to config file (default: ~/.config/lidarr-api/defaults.json)'
    )
    parser.add_argument(
        '--save-connection',
        action='store_true',
        help='Save URL and API key to config'
    )
    args = parser.parse_args()

    # Set up logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level)

    # Load config and connection settings
    config = Config(args.config)
    connection = config.get_connection_settings() or {}

    # Get URL and API key, with priority:
    # 1. Command line arguments
    # 2. Config file
    # 3. Default URL
    base_url = args.url or connection.get(
        'base_url') or 'http://localhost:8686'
    api_key = args.api_key or connection.get('api_key')

    if not api_key:
        print(
            "Error: API key is required. Provide it via --api-key or save it in the config file.",
            file=sys.stderr
        )
        return 1

    # Save connection settings if requested
    if args.save_connection and (args.url or args.api_key):
        config.save_connection_settings(base_url, api_key)
        print("Connection settings saved to config file")

    # Initialize the client
    client = LidarrClient(
        base_url=base_url,
        api_key=api_key,
        retry_total=args.retries,
        timeout=args.timeout
    )

    # Rest of the existing code...
    defaults = config.get_artist_defaults() if args.use_defaults else None

    try:
        # Search for the artist
        print(f"\nSearching for artist: {args.artist_name}")
        print("-" * 80)
        results = client.search_artist(args.artist_name)

        if not results:
            print("No artists found")
            return 1

        # Get list of existing artists with retry logic
        print("Fetching existing artists...")
        try:
            existing_artists = retry_with_backoff(
                client.get_all_artists,
                max_retries=args.retries,
                initial_wait=2.0
            )
            existing_foreign_artist_ids = {
                a.get('foreignArtistId')
                for a in existing_artists
                if a.get('foreignArtistId')
            }
            if args.debug:
                print(f"Found {len(existing_artists)} existing artists")
                print("Existing artist IDs:", existing_foreign_artist_ids)
        except (requests.exceptions.RequestException, ConnectionError, TimeoutError, KeyError) as e:
            print(
                f"\nError fetching existing artists: {str(e)}", file=sys.stderr)
            if args.debug:
                traceback.print_exc()
            print("\nContinuing without existing artist check...", file=sys.stderr)
            existing_foreign_artist_ids = set()

        # Display results
        print(f"\nFound {len(results)} results:\n")
        for idx, artist in enumerate(results, 1):
            foreign_id = artist.get('foreignArtistId')
            already_added = foreign_id in existing_foreign_artist_ids

            if args.debug:
                print(
                    f"Debug: Artist {artist['artistName']} foreignArtistId: {foreign_id}")

            status = "\033[33m[Already added]\033[0m" if already_added else "\033[32m[Not added]\033[0m"  # noqa: E501 pylint: disable=line-too-long
            print(f"{idx}. {status} {artist['artistName']}")
            if 'disambiguation' in artist and artist['disambiguation']:
                print(f"Note: {artist['disambiguation']}")
            if 'overview' in artist and artist['overview']:
                print("\nOverview:")
                print(format_overview(artist['overview']))
            print("\n" + "-" * 80 + "\n")

        # Interactive artist selection
        while True:
            try:
                selection = input(
                    "\nEnter the number of the artist to select (or 'q' to quit): ")
                if selection.lower() == 'q':
                    print("Operation cancelled by user")
                    return 0

                selected_idx = int(selection)
                if 1 <= selected_idx <= len(results):
                    selected_artist = results[selected_idx - 1]
                    print(
                        f"\nSelected artist: {selected_artist['artistName']}")

                    # Get root folder selection
                    root_folder = get_root_folder_selection(client, defaults)
                    if not root_folder:
                        print("Root folder selection cancelled")
                        return 0
                    print(f"\nSelected root folder: {root_folder['path']}")

                    # Get quality profile selection
                    quality_profile = get_quality_profile_selection(
                        client, defaults)
                    if not quality_profile:
                        print("Quality profile selection cancelled")
                        return 0
                    print(
                        f"\nSelected quality profile: {quality_profile['name']}")

                    # Get metadata profile selection
                    metadata_profile = get_metadata_profile_selection(
                        client, defaults)
                    if not metadata_profile:
                        print("Metadata profile selection cancelled")
                        return 0
                    print(
                        f"\nSelected metadata profile: {metadata_profile['name']}")

                    # Get monitored status
                    monitored = get_monitored_option(defaults)
                    if monitored is None:
                        print("Monitored selection cancelled")
                        return 0
                    print(f"\nMonitored: {'Yes' if monitored else 'No'}")

                    # Get album monitor option
                    album_option = get_album_monitor_option(defaults)
                    if album_option is None:
                        print("Album monitor selection cancelled")
                        return 0
                    album_monitor = {
                        1: "All albums",
                        2: "Future albums only",
                        3: "None"
                    }[album_option]
                    print(f"\nMonitoring: {album_monitor}")

                    # Get tags
                    tags = get_tags_selection(client, defaults)
                    if tags is None:
                        print("Tag selection cancelled")
                        return 0
                    if tags:
                        print("\nSelected tags:", ", ".join(
                            t['label'] for t in tags))
                    else:
                        print("\nNo tags selected")

                    # Save defaults if requested
                    if args.save_defaults:
                        print("\nSaving current selections as defaults...")
                        config.save_artist_defaults(
                            root_folder,
                            quality_profile,
                            metadata_profile,
                            monitored,
                            album_option,
                            tags
                        )
                        print("Defaults saved successfully!")

                    # After collecting all information
                    print("\nPreparing to add artist...")
                    artist_data = prepare_artist_data(
                        selected_artist,
                        root_folder,
                        quality_profile,
                        metadata_profile,
                        monitored,
                        album_option,
                        tags
                    )

                    try:
                        print(
                            f"\nAdding artist {selected_artist['artistName']}...")
                        added_artist = client.add_artist(artist_data)
                        print(
                            f"\nSuccessfully added {added_artist['artistName']} to Lidarr!")

                        if args.force_search:
                            print("Triggering search for all albums...")
                            client.search_artist_albums(added_artist['id'])
                            print("Search started successfully!")
                        elif monitored:
                            print("Artist will be monitored and albums will be searched according to Lidarr's schedule.")  # noqa: E501 pylint: disable=line-too-long
                        return 0
                    except (requests.exceptions.RequestException, ConnectionError,
                            TimeoutError, ValueError) as e:
                        print(
                            f"\nError adding artist: {str(e)}", file=sys.stderr)
                        if args.debug:
                            traceback.print_exc()
                        return 1
                else:
                    print(
                        f"Please enter a number between 1 and {len(results)}")
            except ValueError:
                print("Please enter a valid number or 'q' to quit")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except (requests.exceptions.RequestException, ConnectionError, TimeoutError,
            ValueError, KeyError) as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        if args.debug:
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
