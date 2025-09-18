#!/usr/bin/env python3

import argparse
import sys
import textwrap
import traceback
import time
import logging
from lidarr_api import LidarrClient

def format_overview(text, width=70):
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
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:  # Don't sleep on the last attempt
                print(f"\nAttempt {attempt + 1} failed, retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                wait_time *= backoff_factor

    raise last_exception

def main():
    parser = argparse.ArgumentParser(description='Search for an artist in Lidarr')
    parser.add_argument('artist_name', help='Name of the artist to search for')
    parser.add_argument('--url', default='http://localhost:8686', help='Lidarr server URL')
    parser.add_argument('--api-key', required=True, help='Lidarr API key')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--timeout', type=int, default=60, help='Timeout in seconds for API requests')
    parser.add_argument('--retries', type=int, default=3, help='Number of retries for failed requests')
    args = parser.parse_args()

    # Set up logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level)

    # Initialize the client with custom settings
    client = LidarrClient(
        base_url=args.url,
        api_key=args.api_key,
        retry_total=args.retries,
        timeout=args.timeout
    )

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
                lambda: client.get_all_artists(),
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
        except Exception as e:
            print(f"\nError fetching existing artists: {str(e)}", file=sys.stderr)
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
                print(f"Debug: Artist {artist['artistName']} foreignArtistId: {foreign_id}")

            status = "\033[33m[Already added]\033[0m" if already_added else "\033[32m[Not added]\033[0m"
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
                selection = input("\nEnter the number of the artist to select (or 'q' to quit): ")
                if selection.lower() == 'q':
                    print("Operation cancelled by user")
                    return 0

                selected_idx = int(selection)
                if 1 <= selected_idx <= len(results):
                    selected_artist = results[selected_idx - 1]
                    print(f"\nSelected artist: {selected_artist['artistName']}")
                    return 0
                else:
                    print(f"Please enter a number between 1 and {len(results)}")
            except ValueError:
                print("Please enter a valid number or 'q' to quit")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        if args.debug:
            traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
