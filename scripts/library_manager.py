#!/usr/bin/env python3
"""
Lidarr Library Management Script

This script provides library management functionality for Lidarr:
- Wanted/missing albums management
- Quality and metadata profile management
- Import list management
- Queue management and monitoring
"""

import argparse
import sys
from datetime import datetime

from lidarr_api import LidarrClient
from lidarr_api.config import Config


def setup_client(args: argparse.Namespace) -> LidarrClient:
    """Set up the Lidarr client from arguments or config."""
    if args.url and args.api_key:
        client = LidarrClient(
            base_url=args.url,
            api_key=args.api_key,
            timeout=args.timeout,
            retry_total=args.retries,
        )
    else:
        config = Config(args.config)
        settings = config.get_connection_settings()
        if not settings:
            print(
                "No connection settings found. Please provide --url and --api-key "
                "or save settings first."
            )
            sys.exit(1)
        client = LidarrClient(**settings, timeout=args.timeout, retry_total=args.retries)

    return client


def list_wanted_albums(
    client: LidarrClient,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = 'airDateUtc'
) -> None:
    """List wanted/missing albums."""
    try:
        result = client.get_wanted(
            page=page,
            page_size=page_size,
            sort_key=sort_by,
            sort_dir='desc'
        )

        records = result.get('records', [])
        total_records = result.get('totalRecords', 0)

        if not records:
            print("No wanted albums found")
            return

        print(f"Wanted Albums (Page {page}, showing {len(records)} of {total_records} total):")
        print(f"{'Artist':<30} {'Album':<40} {'Release Date':<12} {'Status':<15}")
        print("-" * 100)

        for album in records:
            artist_name = (
                album.get('artist', {}).get('artistName', 'Unknown')
                if album.get('artist') else 'Unknown'
            )
            album_title = album.get('title', 'Unknown')
            release_date = album.get('releaseDate', 'Unknown')
            monitored = album.get('monitored', False)
            status = "Monitored" if monitored else "Unmonitored"

            # Truncate long names
            if len(artist_name) > 28:
                artist_name = artist_name[:25] + "..."
            if len(album_title) > 38:
                album_title = album_title[:35] + "..."

            # Format date
            if release_date != 'Unknown':
                try:
                    date_obj = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
                    release_date = date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    pass

            print(f"{artist_name:<30} {album_title:<40} {release_date:<12} {status:<15}")

        # Show pagination info
        total_pages = (total_records + page_size - 1) // page_size
        print(f"\nPage {page} of {total_pages} (Total wanted: {total_records})")

        if page < total_pages:
            print(f"Use --page {page + 1} to see next page")

    except (KeyError, ValueError) as e:
        print(f"Data error listing wanted albums: {e}")
    except ImportError as e:
        print(f"Import error listing wanted albums: {e}")


def search_wanted_albums(client: LidarrClient, limit: int = 10) -> None:
    """Search for a limited number of wanted albums."""
    try:
        result = client.get_wanted(page=1, page_size=limit)
        records = result.get('records', [])

        if not records:
            print("No wanted albums to search for")
            return

        print(f"Triggering search for {len(records)} wanted albums...")

        for album in records:
            try:
                client.search_album(album['id'])
                artist_name = (
                    album.get('artist', {}).get('artistName', 'Unknown')
                    if album.get('artist') else 'Unknown'
                )
                album_title = album.get('title', 'Unknown')
                print(f"  ✓ {artist_name} - {album_title}")
            except (KeyError, ValueError) as e:
                print(f"  ✗ Failed to search for album {album.get('id')}: {e}")

        print(f"Search initiated for {len(records)} albums")

    except (KeyError, ValueError) as e:
        print(f"Data error searching wanted albums: {e}")
    except ImportError as e:
        print(f"Import error searching wanted albums: {e}")


def list_quality_profiles(client: LidarrClient) -> None:
    """List all quality profiles."""
    try:
        profiles = client.get_quality_profiles()

        if not profiles:
            print("No quality profiles found")
            return

        print("Quality Profiles:")
        print(f"{'ID':<5} {'Name':<30} {'Cutoff':<20} {'Items':<10}")
        print("-" * 70)

        for profile in profiles:
            profile_id = profile.get('id', 'N/A')
            name = profile.get('name', 'Unknown')
            cutoff = (
                profile.get('cutoff', {}).get('name', 'Unknown')
                if profile.get('cutoff') else 'Unknown'
            )
            items_count = len(profile.get('items', []))

            print(f"{profile_id:<5} {name:<30} {cutoff:<20} {items_count:<10}")

        print(f"\nTotal: {len(profiles)} profiles")

    except (KeyError, ValueError) as e:
        print(f"Data error listing quality profiles: {e}")
    except ImportError as e:
        print(f"Import error listing quality profiles: {e}")


def list_metadata_profiles(client: LidarrClient) -> None:
    """List all metadata profiles."""
    try:
        profiles = client.get_metadata_profiles()

        if not profiles:
            print("No metadata profiles found")
            return

        print("Metadata Profiles:")
        print(f"{'ID':<5} {'Name':<30}")
        print("-" * 40)

        for profile in profiles:
            profile_id = profile.get('id', 'N/A')
            name = profile.get('name', 'Unknown')

            print(f"{profile_id:<5} {name:<30}")

        print(f"\nTotal: {len(profiles)} profiles")

    except (KeyError, ValueError) as e:
        print(f"Data error listing metadata profiles: {e}")
    except ImportError as e:
        print(f"Import error listing metadata profiles: {e}")


def list_import_lists(client: LidarrClient) -> None:
    """List all import lists."""
    try:
        lists = client.get_import_lists()

        if not lists:
            print("No import lists configured")
            return

        print("Import Lists:")
        print(f"{'ID':<5} {'Name':<30} {'Type':<20} {'Enabled':<10}")
        print("-" * 70)

        for import_list in lists:
            list_id = import_list.get('id', 'N/A')
            name = import_list.get('name', 'Unknown')
            implementation = import_list.get('implementation', 'Unknown')
            enabled = "Yes" if import_list.get('enabled', False) else "No"

            print(f"{list_id:<5} {name:<30} {implementation:<20} {enabled:<10}")

        print(f"\nTotal: {len(lists)} import lists")

    except (KeyError, ValueError, ImportError) as e:
        print(f"Error listing import lists: {e}")


def test_import_list(client: LidarrClient, list_id: int) -> None:
    """Test a specific import list."""
    try:
        print(f"Testing import list {list_id}...")
        result = client.test_import_list(list_id)

        if result.get('isValid', False):
            print("✓ Import list test successful")
        else:
            print("✗ Import list test failed")
            if 'validationFailures' in result:
                for failure in result['validationFailures']:
                    print(f"  Error: {failure.get('errorMessage', 'Unknown error')}")

    except (KeyError, ValueError, ImportError) as e:
        print(f"Error testing import list: {e}")


def view_queue(
    client: LidarrClient,
    page: int = 1,
    page_size: int = 20,
    include_unknown_artist_items: bool = False
) -> None:
    """View the download queue."""
    try:
        result = client.get_queue(
            page=page,
            page_size=page_size,
            include_unknown_artist_items=include_unknown_artist_items
        )

        records = result.get('records', [])
        total_records = result.get('totalRecords', 0)

        if not records:
            print("Queue is empty")
            return

        print(
            f"Download Queue (Page {page}, showing {len(records)} of {total_records} total items):"
        )
        print(f"{'Artist':<25} {'Album':<35} {'Status':<15} {'Progress':<10} {'Time Left':<12}")
        print("-" * 110)

        for item in records:
            artist_name = (
                item.get('artist', {}).get('artistName', 'Unknown')
                if item.get('artist') else 'Unknown'
            )
            album_title = (
                item.get('album', {}).get('title', 'Unknown')
                if item.get('album') else 'Unknown'
            )
            status = item.get('status', 'Unknown')
            progress = item.get('sizeleft', 0)
            size = item.get('size', 0)
            time_left = item.get('timeleft', 'Unknown')

            # Truncate long names
            if len(artist_name) > 23:
                artist_name = artist_name[:20] + "..."
            if len(album_title) > 33:
                album_title = album_title[:30] + "..."

            # Calculate progress percentage
            if size > 0 and progress >= 0:
                progress_pct = ((size - progress) / size) * 100
                progress_str = f"{progress_pct:.1f}%"
            else:
                progress_str = "N/A"

            # Format time left
            if isinstance(time_left, str) and time_left != 'Unknown':
                # Time left might be in different formats, try to handle common ones
                try:
                    if ':' in time_left:
                        time_left = time_left[:10]  # Truncate if too long
                except (TypeError, ValueError):
                    pass

            print(
                f"{artist_name:<25} {album_title:<35} {status:<15} "
                f"{progress_str:<10} {str(time_left):<12}"
            )

        # Show pagination info
        total_pages = (total_records + page_size - 1) // page_size
        print(f"\nPage {page} of {total_pages} (Total items: {total_records})")

        if page < total_pages:
            print(f"Use --page {page + 1} to see next page")

    except (KeyError, ValueError, ImportError) as e:
        print(f"Error viewing queue: {e}")


def remove_queue_item(
    client: LidarrClient,
    queue_id: int,
    remove_from_client: bool = True,
    blocklist: bool = False
) -> None:
    """Remove an item from the download queue."""
    try:
        client.delete_queue_item(queue_id, remove_from_client, blocklist)
        action_msg = "Removed from queue"
        if remove_from_client:
            action_msg += " and download client"
        if blocklist:
            action_msg += " and added to blocklist"

        print(f"{action_msg}: item {queue_id}")

    except (KeyError, ValueError, ImportError) as e:
        print(f"Error removing queue item: {e}")


def main() -> int:
    """Main entry point for the library management script."""
    parser = argparse.ArgumentParser(
        description="Lidarr library management utilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List wanted albums
  %(prog)s wanted list

  # Search for first 5 wanted albums
  %(prog)s wanted search --limit 5

  # List quality profiles
  %(prog)s profiles quality

  # List metadata profiles
  %(prog)s profiles metadata

  # List import lists
  %(prog)s imports list

  # Test import list
  %(prog)s imports test --id 1

  # View download queue
  %(prog)s queue view

  # Remove item from queue
  %(prog)s queue remove --id 123 --remove-from-client --blocklist
        """
    )

    parser.add_argument('--url', help='Lidarr server URL')
    parser.add_argument('--api-key', help='Lidarr API key')
    parser.add_argument('--config', help='Config file path')
    parser.add_argument('--timeout', type=int, default=60, help='Request timeout (default: 60)')
    parser.add_argument('--retries', type=int, default=3, help='Number of retries (default: 3)')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Wanted albums commands
    wanted_parser = subparsers.add_parser('wanted', help='Wanted albums management')
    wanted_subparsers = wanted_parser.add_subparsers(dest='wanted_command', help='Wanted commands')

    list_wanted_parser = wanted_subparsers.add_parser('list', help='List wanted albums')
    list_wanted_parser.add_argument('--page', type=int, default=1, help='Page number (default: 1)')
    list_wanted_parser.add_argument(
        '--page-size', type=int, default=20, help='Items per page (default: 20)'
    )
    list_wanted_parser.add_argument(
        '--sort-by', default='airDateUtc', help='Sort field (default: airDateUtc)'
    )

    search_wanted_parser = wanted_subparsers.add_parser('search', help='Search wanted albums')
    search_wanted_parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Number of albums to search (default: 10)'
    )

    # Profiles commands
    profiles_parser = subparsers.add_parser('profiles', help='Profile management')
    profiles_subparsers = profiles_parser.add_subparsers(
        dest='profiles_command', help='Profile commands'
    )

    profiles_subparsers.add_parser('quality', help='List quality profiles')
    profiles_subparsers.add_parser('metadata', help='List metadata profiles')

    # Import lists commands
    imports_parser = subparsers.add_parser('imports', help='Import lists management')
    imports_subparsers = imports_parser.add_subparsers(
        dest='imports_command', help='Import commands'
    )

    imports_subparsers.add_parser('list', help='List import lists')

    test_imports_parser = imports_subparsers.add_parser('test', help='Test import list')
    test_imports_parser.add_argument('--id', type=int, required=True, help='Import list ID')

    # Queue commands
    queue_parser = subparsers.add_parser('queue', help='Download queue management')
    queue_subparsers = queue_parser.add_subparsers(dest='queue_command', help='Queue commands')

    view_queue_parser = queue_subparsers.add_parser('view', help='View download queue')
    view_queue_parser.add_argument('--page', type=int, default=1, help='Page number (default: 1)')
    view_queue_parser.add_argument(
        '--page-size', type=int, default=20, help='Items per page (default: 20)'
    )
    view_queue_parser.add_argument(
        '--include-unknown', action='store_true', help='Include unknown artist items'
    )

    remove_queue_parser = queue_subparsers.add_parser('remove', help='Remove queue item')
    remove_queue_parser.add_argument('--id', type=int, required=True, help='Queue item ID')
    remove_queue_parser.add_argument(
        '--remove-from-client',
        action='store_true',
        help='Remove from download client'
    )
    remove_queue_parser.add_argument('--blocklist', action='store_true', help='Add to blocklist')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        client = setup_client(args)

        if args.command == 'wanted':
            if args.wanted_command == 'list':
                list_wanted_albums(client, args.page, args.page_size, args.sort_by)
            elif args.wanted_command == 'search':
                search_wanted_albums(client, args.limit)
            else:
                wanted_parser.print_help()
                return 1

        elif args.command == 'profiles':
            if args.profiles_command == 'quality':
                list_quality_profiles(client)
            elif args.profiles_command == 'metadata':
                list_metadata_profiles(client)
            else:
                profiles_parser.print_help()
                return 1

        elif args.command == 'imports':
            if args.imports_command == 'list':
                list_import_lists(client)
            elif args.imports_command == 'test':
                test_import_list(client, args.id)
            else:
                imports_parser.print_help()
                return 1

        elif args.command == 'queue':
            if args.queue_command == 'view':
                view_queue(client, args.page, args.page_size, args.include_unknown)
            elif args.queue_command == 'remove':
                remove_queue_item(client, args.id, args.remove_from_client, args.blocklist)
            else:
                queue_parser.print_help()
                return 1

        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except (ValueError, KeyError, ImportError, argparse.ArgumentError) as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:  # pylint: disable=broad-except
        # Unexpected error
        print(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
