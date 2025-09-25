#!/usr/bin/env python3
"""
Bulk Artist Management Script for Lidarr

This script provides functionality to perform bulk operations on artists in Lidarr:
- Bulk monitor/unmonitor artists
- Bulk tag management
- Search for all albums by multiple artists
- Export artist lists
"""

import argparse
import csv
import json
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path

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
            print("No connection settings found. Please provide --url and --api-key or save settings first.")
            sys.exit(1)
        client = LidarrClient(**settings, timeout=args.timeout, retry_total=args.retries)
    
    return client


def bulk_monitor_artists(client: LidarrClient, artist_ids: List[int], monitored: bool) -> None:
    """Monitor or unmonitor multiple artists."""
    try:
        result = client.update_artists_monitor(artist_ids, monitored)
        action = "monitored" if monitored else "unmonitored"
        print(f"Successfully {action} {len(artist_ids)} artists")
        if 'updated' in result:
            print(f"Updated: {result['updated']} artists")
    except Exception as e:
        print(f"Error updating artist monitoring: {e}")


def bulk_tag_artists(client: LidarrClient, artist_ids: List[int], tag_ids: List[int], add: bool = True) -> None:
    """Add or remove tags from multiple artists."""
    try:
        artists = []
        for artist_id in artist_ids:
            artist = client.get_artist(artist_id)
            current_tags = set(artist.get('tags', []))
            
            if add:
                current_tags.update(tag_ids)
            else:
                current_tags.difference_update(tag_ids)
            
            artist['tags'] = list(current_tags)
            artists.append(artist)
        
        # Update each artist individually since there's no bulk tag update endpoint
        for artist in artists:
            client._request('PUT', f'artist/{artist["id"]}', json=artist)
        
        action = "added to" if add else "removed from"
        print(f"Successfully {action} {len(artist_ids)} artists")
    except Exception as e:
        print(f"Error updating artist tags: {e}")


def search_all_albums(client: LidarrClient, artist_ids: List[int]) -> None:
    """Trigger album search for multiple artists."""
    try:
        for artist_id in artist_ids:
            result = client.search_artist_albums(artist_id)
            artist = client.get_artist(artist_id)
            print(f"Triggered album search for {artist['artistName']} (ID: {artist_id})")
        
        print(f"Album search triggered for {len(artist_ids)} artists")
    except Exception as e:
        print(f"Error triggering album searches: {e}")


def export_artists(client: LidarrClient, output_file: str, format_type: str = 'json') -> None:
    """Export all artists to a file."""
    try:
        artists = client.get_all_artists()
        
        if format_type.lower() == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(artists, f, indent=2, ensure_ascii=False)
        elif format_type.lower() == 'csv':
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                if not artists:
                    print("No artists found to export")
                    return
                
                writer = csv.DictWriter(f, fieldnames=['id', 'artistName', 'foreignArtistId', 'monitored', 'status', 'path'])
                writer.writeheader()
                for artist in artists:
                    writer.writerow({
                        'id': artist.get('id'),
                        'artistName': artist.get('artistName'),
                        'foreignArtistId': artist.get('foreignArtistId'),
                        'monitored': artist.get('monitored'),
                        'status': artist.get('status'),
                        'path': artist.get('path')
                    })
        
        print(f"Exported {len(artists)} artists to {output_file}")
    except Exception as e:
        print(f"Error exporting artists: {e}")


def list_artists_by_tag(client: LidarrClient, tag_name: str) -> None:
    """List all artists with a specific tag."""
    try:
        # Get all tags to find the tag ID
        tags = client.get_tags()
        tag_id = None
        for tag in tags:
            if tag['label'].lower() == tag_name.lower():
                tag_id = tag['id']
                break
        
        if tag_id is None:
            print(f"Tag '{tag_name}' not found")
            return
        
        # Get all artists and filter by tag
        artists = client.get_all_artists()
        tagged_artists = [a for a in artists if tag_id in a.get('tags', [])]
        
        print(f"Artists with tag '{tag_name}':")
        for artist in tagged_artists:
            status = "✓" if artist.get('monitored') else "✗"
            print(f"  {status} {artist['artistName']} (ID: {artist['id']})")
        
        print(f"\nTotal: {len(tagged_artists)} artists")
    except Exception as e:
        print(f"Error listing artists by tag: {e}")


def main() -> int:
    """Main entry point for the bulk artist manager."""
    parser = argparse.ArgumentParser(
        description="Bulk operations for Lidarr artists",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor multiple artists
  %(prog)s monitor --artists 1,2,3,4
  
  # Unmonitor artists
  %(prog)s unmonitor --artists 1,2,3
  
  # Add tags to artists
  %(prog)s tag --artists 1,2,3 --tag-ids 5,6 --add
  
  # Remove tags from artists
  %(prog)s tag --artists 1,2,3 --tag-ids 5,6 --remove
  
  # Search albums for multiple artists
  %(prog)s search --artists 1,2,3,4,5
  
  # Export all artists to JSON
  %(prog)s export --output artists.json --format json
  
  # Export to CSV
  %(prog)s export --output artists.csv --format csv
  
  # List artists with specific tag
  %(prog)s list-by-tag --tag-name rock
        """
    )
    
    parser.add_argument('--url', help='Lidarr server URL')
    parser.add_argument('--api-key', help='Lidarr API key')
    parser.add_argument('--config', help='Config file path')
    parser.add_argument('--timeout', type=int, default=60, help='Request timeout (default: 60)')
    parser.add_argument('--retries', type=int, default=3, help='Number of retries (default: 3)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor artists')
    monitor_parser.add_argument('--artists', required=True, help='Comma-separated artist IDs')
    
    # Unmonitor command
    unmonitor_parser = subparsers.add_parser('unmonitor', help='Unmonitor artists')
    unmonitor_parser.add_argument('--artists', required=True, help='Comma-separated artist IDs')
    
    # Tag command
    tag_parser = subparsers.add_parser('tag', help='Manage artist tags')
    tag_parser.add_argument('--artists', required=True, help='Comma-separated artist IDs')
    tag_parser.add_argument('--tag-ids', required=True, help='Comma-separated tag IDs')
    tag_group = tag_parser.add_mutually_exclusive_group(required=True)
    tag_group.add_argument('--add', action='store_true', help='Add tags')
    tag_group.add_argument('--remove', action='store_true', help='Remove tags')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search albums for artists')
    search_parser.add_argument('--artists', required=True, help='Comma-separated artist IDs')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export artists')
    export_parser.add_argument('--output', required=True, help='Output file path')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Output format (default: json)')
    
    # List by tag command
    list_parser = subparsers.add_parser('list-by-tag', help='List artists by tag')
    list_parser.add_argument('--tag-name', required=True, help='Tag name to filter by')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        client = setup_client(args)
        
        if args.command in ['monitor', 'unmonitor', 'tag', 'search']:
            artist_ids = [int(id.strip()) for id in args.artists.split(',')]
        
        if args.command == 'monitor':
            bulk_monitor_artists(client, artist_ids, True)
        elif args.command == 'unmonitor':
            bulk_monitor_artists(client, artist_ids, False)
        elif args.command == 'tag':
            tag_ids = [int(id.strip()) for id in args.tag_ids.split(',')]
            bulk_tag_artists(client, artist_ids, tag_ids, args.add)
        elif args.command == 'search':
            search_all_albums(client, artist_ids)
        elif args.command == 'export':
            export_artists(client, args.output, args.format)
        elif args.command == 'list-by-tag':
            list_artists_by_tag(client, args.tag_name)
        
        return 0
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())