#!/usr/bin/env python3
"""
Lidarr Data Import/Export Utilities

This module provides data import/export functionality for Lidarr:
- Export artist libraries to various formats (JSON, CSV, TSV)
- Import artist lists from files
- Backup and restore configurations
- Export quality profiles, metadata profiles, and tags
- Migration utilities between Lidarr instances
"""

import argparse
import csv
import json
import sys
from .client import LidarrClient
from .config import Config


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


def export_artists_json(
    client: LidarrClient,
    output_file: str = None,
    include_albums: bool = False,
) -> None:
    """Export artists to JSON format."""
    try:
        print("Fetching artists...", file=sys.stderr)
        artists = client.get_all_artists()

        export_data = []
        for artist in artists:
            artist_data = {
                'foreignArtistId': artist.get('foreignArtistId'),
                'artistName': artist.get('artistName'),
                'sortName': artist.get('sortName'),
                'disambiguation': artist.get('disambiguation', ''),
                'overview': artist.get('overview', ''),
                'artistType': artist.get('artistType'),
                'status': artist.get('status'),
                'ended': artist.get('ended'),
                'genres': artist.get('genres', []),
                'tags': artist.get('tags', []),
                'monitored': artist.get('monitored'),
                'qualityProfileId': artist.get('qualityProfileId'),
                'metadataProfileId': artist.get('metadataProfileId'),
                'path': artist.get('path'),
                'rootFolderPath': artist.get('rootFolderPath')
            }

            if include_albums:
                try:
                    albums = client.get_albums_by_artist(artist['id'])
                    artist_data['albums'] = [{
                        'title': album.get('title'),
                        'releaseDate': album.get('releaseDate'),
                        'monitored': album.get('monitored'),
                        'albumType': album.get('albumType'),
                        'disambiguation': album.get('disambiguation', ''),
                        'foreignAlbumId': album.get('foreignAlbumId')
                    } for album in albums]
                except (KeyError, AttributeError, RuntimeError) as e:
                    artist_name = artist.get('artistName', 'Unknown')
                    print(f"Warning: Failed to get albums for {artist_name}: {e}", file=sys.stderr)
                    artist_data['albums'] = []

            export_data.append(artist_data)

        # Write to file or stdout
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            print(f"Exported {len(export_data)} artists to {output_file}", file=sys.stderr)
        else:
            json.dump(export_data, sys.stdout, indent=2, ensure_ascii=False)
            print(f"Exported {len(export_data)} artists to stdout", file=sys.stderr)

    except (OSError, json.JSONDecodeError) as e:
        print(f"Error exporting artists to JSON: {e}", file=sys.stderr)


def export_artists_csv(client: LidarrClient, output_file: str = None) -> None:
    """Export artists to CSV format."""
    try:
        print("Fetching artists...", file=sys.stderr)
        artists = client.get_all_artists()

        # Determine output destination
        if output_file:
            f = open(output_file, 'w', newline='', encoding='utf-8')
        else:
            f = sys.stdout

        try:
            fieldnames = [
                'foreignArtistId', 'artistName', 'sortName', 'disambiguation',
                'artistType', 'status', 'ended', 'genres', 'monitored',
                'qualityProfileId', 'metadataProfileId', 'path', 'tags'
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for artist in artists:
                # Convert lists to comma-separated strings for CSV
                genres = ', '.join(artist.get('genres', []))
                tags_list = []
                if artist.get('tags'):
                    # We'd need to resolve tag IDs to names, but for now just use IDs
                    tags_list = [str(tag) for tag in artist.get('tags', [])]
                tags = ', '.join(tags_list)

                writer.writerow({
                    'foreignArtistId': artist.get('foreignArtistId', ''),
                    'artistName': artist.get('artistName', ''),
                    'sortName': artist.get('sortName', ''),
                    'disambiguation': artist.get('disambiguation', ''),
                    'artistType': artist.get('artistType', ''),
                    'status': artist.get('status', ''),
                    'ended': artist.get('ended', ''),
                    'genres': genres,
                    'monitored': artist.get('monitored', ''),
                    'qualityProfileId': artist.get('qualityProfileId', ''),
                    'metadataProfileId': artist.get('metadataProfileId', ''),
                    'path': artist.get('path', ''),
                    'tags': tags
                })

            if output_file:
                print(f"Exported {len(artists)} artists to {output_file}", file=sys.stderr)
            else:
                print(f"Exported {len(artists)} artists to stdout", file=sys.stderr)

        finally:
            if output_file:
                f.close()

    except (OSError, csv.Error) as e:
        print(f"Error exporting artists to CSV: {e}", file=sys.stderr)


def import_artists_from_json(
    client: LidarrClient, input_file: str = None, dry_run: bool = False
) -> None:
    """Import artists from JSON file or stdin."""
    try:
        if input_file:
            print(f"Reading artists from {input_file}...", file=sys.stderr)
            with open(input_file, 'r', encoding='utf-8') as f:
                artists_data = json.load(f)
        else:
            print("Reading artists from stdin...", file=sys.stderr)
            artists_data = json.load(sys.stdin)

        if not isinstance(artists_data, list):
            print("Error: JSON file should contain a list of artists")
            return

        # Get existing artists to avoid duplicates
        print("Checking existing artists...")
        existing_artists = client.get_all_artists()
        existing_ids = {
            artist.get('foreignArtistId')
            for artist in existing_artists
            if artist.get('foreignArtistId')
        }

        # Get available profiles
        quality_profiles = {p['id']: p for p in client.get_quality_profiles()}
        metadata_profiles = {p['id']: p for p in client.get_metadata_profiles()}
        root_folders = client.get_root_folders()

        if not quality_profiles:
            print("Error: No quality profiles found. Please create at least one quality profile.")
            return

        if not root_folders:
            print("Error: No root folders found. Please create at least one root folder.")
            return

        default_quality_profile = list(quality_profiles.keys())[0]
        default_metadata_profile = list(metadata_profiles.keys())[0] if metadata_profiles else 1
        default_root_folder = root_folders[0]['path']

        added_count = 0
        skipped_count = 0
        error_count = 0

        for artist_data in artists_data:
            foreign_id = artist_data.get('foreignArtistId')
            artist_name = artist_data.get('artistName', 'Unknown')

            if not foreign_id:
                print(f"Skipping {artist_name}: no foreignArtistId")
                skipped_count += 1
                continue

            if foreign_id in existing_ids:
                print(f"Skipping {artist_name}: already exists")
                skipped_count += 1
                continue

            # Prepare artist data for addition
            add_data = {
                'foreignArtistId': foreign_id,
                'artistName': artist_name,
                'monitored': artist_data.get('monitored', True),
                'qualityProfileId': artist_data.get('qualityProfileId', default_quality_profile),
                'metadataProfileId': artist_data.get('metadataProfileId', default_metadata_profile),
                'rootFolderPath': artist_data.get('rootFolderPath', default_root_folder),
                'addOptions': {
                    'searchForMissingAlbums': True
                }
            }

            # Include optional fields if present
            for field in ['sortName', 'disambiguation', 'overview', 'artistType', 'genres', 'tags']:
                if field in artist_data:
                    add_data[field] = artist_data[field]

            if dry_run:
                print(f"Would add: {artist_name} (ID: {foreign_id})")
                added_count += 1
            else:
                try:
                    client.add_artist(add_data)
                    print(f"Added: {artist_name}")
                    added_count += 1
                except (RuntimeError, KeyError, TypeError) as e:
                    print(f"Error adding {artist_name}: {e}")
                    error_count += 1

        action = "Would add" if dry_run else "Added"
        print("\nSummary:")
        print(f"  {action}: {added_count} artists")
        print(f"  Skipped: {skipped_count} artists")
        if error_count > 0:
            print(f"  Errors: {error_count} artists")

        if dry_run:
            print("\nThis was a dry run. Use --execute to actually import the artists.")

    except (OSError, json.JSONDecodeError) as e:
        print(f"Error importing artists from JSON: {e}")


def export_configuration(client: LidarrClient, output_file: str = None) -> None:
    """Export Lidarr configuration (profiles, tags, etc.) to JSON."""
    try:
        print("Exporting configuration...", file=sys.stderr)

        config_data = {
            'export_timestamp': client.get_system_status().get('startTime'),
            'quality_profiles': [],
            'metadata_profiles': [],
            'tags': [],
            'root_folders': [],
            'import_lists': []
        }

        # Export quality profiles
        try:
            config_data['quality_profiles'] = client.get_quality_profiles()
            profile_count = len(config_data['quality_profiles'])
            print(f"  Exported {profile_count} quality profiles", file=sys.stderr)
        except (OSError, RuntimeError, KeyError) as e:
            print(f"  Warning: Failed to export quality profiles: {e}", file=sys.stderr)

        # Export metadata profiles
        try:
            config_data['metadata_profiles'] = client.get_metadata_profiles()
            metadata_count = len(config_data['metadata_profiles'])
            print(f"  Exported {metadata_count} metadata profiles", file=sys.stderr)
        except (OSError, RuntimeError, KeyError) as e:
            print(f"  Warning: Failed to export metadata profiles: {e}", file=sys.stderr)

        # Export tags
        try:
            config_data['tags'] = client.get_tags()
            print(f"  Exported {len(config_data['tags'])} tags", file=sys.stderr)
        except (OSError, RuntimeError, KeyError) as e:
            print(f"  Warning: Failed to export tags: {e}", file=sys.stderr)

        # Export root folders
        try:
            config_data['root_folders'] = client.get_root_folders()
            root_count = len(config_data['root_folders'])
            print(f"  Exported {root_count} root folders", file=sys.stderr)
        except (OSError, RuntimeError, KeyError) as e:
            print(f"  Warning: Failed to export root folders: {e}", file=sys.stderr)

        # Export import lists
        try:
            config_data['import_lists'] = client.get_import_lists()
            import_count = len(config_data['import_lists'])
            print(f"  Exported {import_count} import lists", file=sys.stderr)
        except (OSError, RuntimeError, KeyError) as e:
            print(f"  Warning: Failed to export import lists: {e}", file=sys.stderr)

        # Write to file or stdout
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            print(f"\nConfiguration exported to {output_file}", file=sys.stderr)
        else:
            json.dump(config_data, sys.stdout, indent=2, ensure_ascii=False)
            print("\nConfiguration exported to stdout", file=sys.stderr)

    except (OSError, json.JSONDecodeError, RuntimeError, KeyError) as e:
        print(f"Error exporting configuration: {e}", file=sys.stderr)


def import_tags_from_config(
    client: LidarrClient, config_file: str = None, dry_run: bool = False
) -> None:
    """Import tags from a configuration file or stdin."""
    try:
        if config_file:
            print(f"Reading configuration from {config_file}...", file=sys.stderr)
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        else:
            print("Reading configuration from stdin...", file=sys.stderr)
            config_data = json.load(sys.stdin)

        tags_to_import = config_data.get('tags', [])
        if not tags_to_import:
            print("No tags found in configuration file")
            return

        # Get existing tags
        existing_tags = client.get_tags()
        existing_labels = {tag['label'].lower() for tag in existing_tags}

        added_count = 0
        skipped_count = 0

        for tag in tags_to_import:
            label = tag.get('label', '')
            if not label:
                continue

            if label.lower() in existing_labels:
                print(f"Skipping tag '{label}': already exists")
                skipped_count += 1
                continue

            if dry_run:
                print(f"Would create tag: {label}")
                added_count += 1
            else:
                try:
                    client.add_tag(label)
                    print(f"Created tag: {label}")
                    added_count += 1
                except (RuntimeError, KeyError) as e:
                    print(f"Error creating tag '{label}': {e}")

        action = "Would create" if dry_run else "Created"
        print("\nSummary:")
        print(f"  {action}: {added_count} tags")
        print(f"  Skipped: {skipped_count} tags")

        if dry_run:
            print("\nThis was a dry run. Use --execute to actually import the tags.")

    except (OSError, json.JSONDecodeError, RuntimeError, KeyError) as e:
        print(f"Error importing tags: {e}")


def export_wanted_albums(
    client: LidarrClient, output_file: str = None, format_type: str = 'json'
) -> None:
    """Export wanted albums list."""
    try:
        print("Fetching wanted albums...", file=sys.stderr)

        all_wanted = []
        page = 1
        page_size = 100

        while True:
            result = client.get_wanted(page=page, page_size=page_size)
            records = result.get('records', [])

            if not records:
                break

            all_wanted.extend(records)

            if len(records) < page_size:
                break

            page += 1

        if format_type.lower() == 'json':
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_wanted, f, indent=2, ensure_ascii=False)
            else:
                json.dump(all_wanted, sys.stdout, indent=2, ensure_ascii=False)

        elif format_type.lower() == 'csv':
            # Determine output destination
            if output_file:
                f = open(output_file, 'w', newline='', encoding='utf-8')
            else:
                f = sys.stdout

            try:
                if all_wanted:
                    fieldnames = [
                        'artistName',
                        'albumTitle',
                        'releaseDate',
                        'albumType',
                        'monitored',
                        'foreignAlbumId'
                    ]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    for album in all_wanted:
                        artist = album.get('artist')
                        if artist:
                            artist_name = artist.get('artistName', 'Unknown')
                        else:
                            artist_name = 'Unknown'
                        writer.writerow({
                            'artistName': artist_name,
                            'albumTitle': album.get('title', ''),
                            'releaseDate': album.get('releaseDate', ''),
                            'albumType': album.get('albumType', ''),
                            'monitored': album.get('monitored', ''),
                            'foreignAlbumId': album.get('foreignAlbumId', '')
                        })
            finally:
                if output_file:
                    f.close()

        if output_file:
            print(f"Exported {len(all_wanted)} wanted albums to {output_file}", file=sys.stderr)
        else:
            print(f"Exported {len(all_wanted)} wanted albums to stdout", file=sys.stderr)

    except (OSError, json.JSONDecodeError, csv.Error, RuntimeError, KeyError) as e:
        print(f"Error exporting wanted albums: {e}", file=sys.stderr)


def main() -> int:
    """Main entry point for the data import/export script."""
    parser = argparse.ArgumentParser(
        description="Lidarr data import/export utilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export artists to JSON file
  %(prog)s export artists --output artists.json --format json

  # Export artists to stdout (pipe-friendly)
  %(prog)s export artists --format json

  # Export artists with albums to file
  %(prog)s export artists --output artists.json --format json --include-albums

  # Export to CSV and pipe to another command
  %(prog)s export artists --format csv | head -10

  # Import artists from file (dry run first)
  %(prog)s import artists --input artists.json --dry-run
  %(prog)s import artists --input artists.json --execute

  # Import artists from stdin via pipe
  cat artists.json | %(prog)s import artists --execute

  # Export configuration to stdout
  %(prog)s export config

  # Export configuration to file
  %(prog)s export config --output config.json

  # Import tags from config file
  %(prog)s import tags --input config.json --dry-run

  # Import tags from stdin
  cat config.json | %(prog)s import tags --execute

  # Export wanted albums and pipe to grep
  %(prog)s export wanted --format csv | grep "Rock"

  # Chain operations: export from one instance, import to another
  lidarr-data export artists | lidarr-data import artists --execute
        """
    )

    parser.add_argument('--url', help='Lidarr server URL')
    parser.add_argument('--api-key', help='Lidarr API key')
    parser.add_argument('--config', help='Config file path')
    parser.add_argument('--timeout', type=int, default=60, help='Request timeout (default: 60)')
    parser.add_argument('--retries', type=int, default=3, help='Number of retries (default: 3)')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Export commands
    export_parser = subparsers.add_parser('export', help='Export data')
    export_subparsers = export_parser.add_subparsers(dest='export_type', help='Export types')

    # Export artists
    export_artists_parser = export_subparsers.add_parser('artists', help='Export artists')
    export_artists_parser.add_argument(
        '--output', help='Output file path (default: stdout)'
    )
    export_artists_parser.add_argument(
        '--format',
        choices=['json', 'csv'],
        default='json',
        help='Output format'
    )
    export_artists_parser.add_argument(
        '--include-albums',
        action='store_true',
        help='Include album data (JSON only)'
    )

    # Export configuration
    export_config_parser = export_subparsers.add_parser('config', help='Export configuration')
    export_config_parser.add_argument(
        '--output', help='Output file path (default: stdout)'
    )

    # Export wanted
    export_wanted_parser = export_subparsers.add_parser('wanted', help='Export wanted albums')
    export_wanted_parser.add_argument(
        '--output', help='Output file path (default: stdout)'
    )
    export_wanted_parser.add_argument(
        '--format',
        choices=['json', 'csv'],
        default='json',
        help='Output format'
    )

    # Import commands
    import_parser = subparsers.add_parser('import', help='Import data')
    import_subparsers = import_parser.add_subparsers(dest='import_type', help='Import types')

    # Import artists
    import_artists_parser = import_subparsers.add_parser('artists', help='Import artists')
    import_artists_parser.add_argument(
        '--input', help='Input JSON file path (default: stdin)'
    )
    import_group = import_artists_parser.add_mutually_exclusive_group(required=True)
    import_group.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be imported without making changes'
    )
    import_group.add_argument('--execute', action='store_true', help='Actually perform the import')

    # Import tags
    import_tags_parser = import_subparsers.add_parser('tags', help='Import tags from config')
    import_tags_parser.add_argument(
        '--input', help='Input config JSON file path (default: stdin)'
    )
    import_tags_group = import_tags_parser.add_mutually_exclusive_group(required=True)
    import_tags_group.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be imported without making changes'
    )
    import_tags_group.add_argument(
        '--execute', action='store_true', help='Actually perform the import'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        client = setup_client(args)

        if args.command == 'export':
            if args.export_type == 'artists':
                if args.format == 'json':
                    export_artists_json(client, args.output, args.include_albums)
                else:
                    export_artists_csv(client, args.output)
            elif args.export_type == 'config':
                export_configuration(client, args.output)
            elif args.export_type == 'wanted':
                export_wanted_albums(client, args.output, args.format)
            else:
                export_parser.print_help()
                return 1

        elif args.command == 'import':
            if args.import_type == 'artists':
                import_artists_from_json(client, args.input, args.dry_run)
            elif args.import_type == 'tags':
                import_tags_from_config(client, args.input, args.dry_run)
            else:
                import_parser.print_help()
                return 1

        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except (OSError, RuntimeError, KeyError, ValueError) as e:
        print(f"Error: {e}")
        return 1


def cli_main() -> None:
    """Entry point for the CLI command."""
    sys.exit(main())


if __name__ == '__main__':
    cli_main()
