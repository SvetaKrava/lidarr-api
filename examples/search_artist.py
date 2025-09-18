#!/usr/bin/env python3

import argparse
import sys
import textwrap
import traceback
from lidarr_api import LidarrClient

def format_overview(text, width=70):
    if not text:
        return ""
    return "\n".join(textwrap.wrap(text, width=width))

def main():
    parser = argparse.ArgumentParser(description='Search for an artist in Lidarr')
    parser.add_argument('artist_name', help='Name of the artist to search for')
    parser.add_argument('--url', default='http://localhost:8686', help='Lidarr server URL')
    parser.add_argument('--api-key', required=True, help='Lidarr API key')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()

    # Initialize the client
    client = LidarrClient(
        base_url=args.url,
        api_key=args.api_key,
        retry_total=2,
        timeout=30
    )

    try:
        # Search for the artist
        print(f"\nSearching for artist: {args.artist_name}")
        print("-" * 80)
        results = client.search_artist(args.artist_name)

        if not results:
            print("No artists found")
            return 1

        # Get list of existing artists
        try:
            print("Fetching existing artists...")
            existing_artists = client.get_all_artists()
            if args.debug:
                print(f"Found {len(existing_artists)} existing artists")
            existing_foreign_artist_ids = {a.get('foreignArtistId') for a in existing_artists if a.get('foreignArtistId')}

            if args.debug:
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

        return 0

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
