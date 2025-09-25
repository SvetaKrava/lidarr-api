#!/usr/bin/env python3
"""
Lidarr System Maintenance Module

This module provides system maintenance functionality for Lidarr:
- Backup management (create, list, restore)
- Blocklist management (view, clean, remove specific items)
- System health monitoring
- Log management helpers
"""

import argparse
import sys
from datetime import datetime

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
        client = LidarrClient(
            **settings, timeout=args.timeout, retry_total=args.retries
        )

    return client


def create_backup(client: LidarrClient) -> None:
    """Create a manual backup."""
    try:
        print("Creating backup...")
        client.start_backup()
        print("Backup creation initiated successfully")
        print(
            "Note: The backup process runs asynchronously. Check the backups list "
            "to see when it completes."
        )
    except (ConnectionError, ValueError, KeyError) as e:
        print(f"Error creating backup: {e}")


def list_backups(client: LidarrClient) -> None:
    """List available backups."""
    try:
        backups = client.get_system_backup()

        if not backups:
            print("No backups found")
            return

        print("Available backups:")
        print(f"{'Name':<40} {'Type':<12} {'Time':<20} {'Size':<10}")
        print("-" * 85)

        for backup in backups:
            name = backup.get("name", "Unknown")
            backup_type = backup.get("type", "Unknown")
            time = backup.get("time", "Unknown")
            size = backup.get("size", 0)

            # Format size in human readable format
            if isinstance(size, (int, float)):
                if size > 1024 * 1024:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                elif size > 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size} B"
            else:
                size_str = str(size)

            print(f"{name:<40} {backup_type:<12} {time:<20} {size_str:<10}")

        print(f"\nTotal: {len(backups)} backups")
    except (ConnectionError, ValueError, KeyError) as e:
        print(f"Error listing backups: {e}")


def restore_backup(client: LidarrClient, backup_name: str) -> None:
    """Restore from a specific backup."""
    try:
        print(f"Restoring from backup: {backup_name}")
        print(
            "WARNING: This will restore Lidarr to the state when the backup was created."
        )

        confirm = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print("Restore cancelled")
            return

        client.restore_system(backup_name)
        print("Restore initiated successfully")
        print("Note: Lidarr will restart after the restore completes.")
    except (ConnectionError, ValueError, KeyError) as e:
        print(f"Error restoring backup: {e}")


def view_blocklist(client: LidarrClient, page: int = 1, page_size: int = 20) -> None:
    """View the blocklist with pagination."""
    try:
        result = client.get_blocklist(
            page=page, page_size=page_size, include_artist=True
        )

        records = result.get("records", [])
        total_records = result.get("totalRecords", 0)

        if not records:
            print("Blocklist is empty")
            return

        print(
            f"Blocklist (Page {page}, showing {len(records)} of {total_records} total items):"
        )
        print(f"{'ID':<8} {'Artist':<30} {'Album':<40} {'Date':<12}")
        print("-" * 95)

        for item in records:
            item_id = item.get("id", "N/A")
            artist_name = (
                item.get("artist", {}).get("artistName", "Unknown")
                if item.get("artist")
                else "Unknown"
            )
            title = item.get("title", "Unknown")
            date = item.get("date", "Unknown")

            # Truncate long names
            if len(artist_name) > 28:
                artist_name = artist_name[:25] + "..."
            if len(title) > 38:
                title = title[:35] + "..."

            # Format date
            if date != "Unknown":
                try:
                    date_obj = datetime.fromisoformat(date.replace("Z", "+00:00"))
                    date = date_obj.strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    pass

            print(f"{item_id:<8} {artist_name:<30} {title:<40} {date:<12}")

        # Show pagination info
        total_pages = (total_records + page_size - 1) // page_size
        print(f"\nPage {page} of {total_pages} (Total items: {total_records})")

        if page < total_pages:
            print(f"Use --page {page + 1} to see next page")

    except (ConnectionError, ValueError, KeyError) as e:
        print(f"Error viewing blocklist: {e}")


def clear_blocklist(client: LidarrClient) -> None:
    """Clear the entire blocklist."""
    try:
        print("WARNING: This will remove ALL items from the blocklist.")
        confirm = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print("Clear cancelled")
            return

        client.clear_blocklist()
        print("Blocklist cleared successfully")
    except (ConnectionError, ValueError, KeyError) as e:
        print(f"Error clearing blocklist: {e}")


def remove_blocklist_item(client: LidarrClient, item_id: int) -> None:
    """Remove a specific item from the blocklist."""
    try:
        client.delete_blocklist(item_id)
        print(f"Removed item {item_id} from blocklist")
    except (ConnectionError, ValueError, KeyError) as e:
        print(f"Error removing blocklist item: {e}")


def system_health(client: LidarrClient) -> None:
    """Check system health and status."""
    try:
        status = client.get_system_status()

        print("System Status:")
        print(f"  Version: {status.get('version', 'Unknown')}")
        print(f"  Build Time: {status.get('buildTime', 'Unknown')}")
        print(f"  Start Time: {status.get('startTime', 'Unknown')}")
        print(
            f"  Runtime: {status.get('runtimeName', 'Unknown')} {status.get('runtimeVersion', '')}"
        )
        print(f"  OS: {status.get('osName', 'Unknown')} {status.get('osVersion', '')}")

        # Check disk space
        try:
            disk_space = client.get_disk_space()
            print("\nDisk Space:")
            for disk in disk_space:
                path = disk.get("path", "Unknown")
                free = disk.get("freeSpace", 0)
                total = disk.get("totalSpace", 0)

                if total > 0:
                    free_gb = free / (1024**3)
                    total_gb = total / (1024**3)
                    used_percent = ((total - free) / total) * 100
                    print(
                        f"  {path}: {free_gb:.1f} GB free of {total_gb:.1f} GB "
                        f"({used_percent:.1f}% used)"
                    )
                else:
                    print(f"  {path}: Unable to determine disk space")
        except (ConnectionError, ValueError, KeyError, OSError) as e:
            print(f"\nDisk Space: Unable to retrieve disk space information - {e}")

        print("\nSystem appears to be running normally")

    except (ConnectionError, ValueError, KeyError) as e:
        print(f"Error checking system health: {e}")


def main() -> int:
    """Main entry point for the system maintenance script."""
    parser = argparse.ArgumentParser(
        description="Lidarr system maintenance utilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a manual backup
  %(prog)s backup create

  # List available backups
  %(prog)s backup list

  # Restore from a backup
  %(prog)s backup restore --name backup_20231225_120000.zip

  # View blocklist
  %(prog)s blocklist view

  # View specific page of blocklist
  %(prog)s blocklist view --page 2

  # Remove specific blocklist item
  %(prog)s blocklist remove --id 123

  # Clear entire blocklist
  %(prog)s blocklist clear

  # Check system health
  %(prog)s health
        """,
    )

    parser.add_argument("--url", help="Lidarr server URL")
    parser.add_argument("--api-key", help="Lidarr API key")
    parser.add_argument("--config", help="Config file path")
    parser.add_argument(
        "--timeout", type=int, default=60, help="Request timeout (default: 60)"
    )
    parser.add_argument(
        "--retries", type=int, default=3, help="Number of retries (default: 3)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Backup commands
    backup_parser = subparsers.add_parser("backup", help="Backup management")
    backup_subparsers = backup_parser.add_subparsers(
        dest="backup_command", help="Backup commands"
    )

    backup_subparsers.add_parser("create", help="Create a new backup")
    backup_subparsers.add_parser("list", help="List available backups")

    restore_parser = backup_subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("--name", required=True, help="Backup file name")

    # Blocklist commands
    blocklist_parser = subparsers.add_parser("blocklist", help="Blocklist management")
    blocklist_subparsers = blocklist_parser.add_subparsers(
        dest="blocklist_command", help="Blocklist commands"
    )

    view_parser = blocklist_subparsers.add_parser("view", help="View blocklist")
    view_parser.add_argument(
        "--page", type=int, default=1, help="Page number (default: 1)"
    )
    view_parser.add_argument(
        "--page-size", type=int, default=20, help="Items per page (default: 20)"
    )

    remove_parser = blocklist_subparsers.add_parser(
        "remove", help="Remove blocklist item"
    )
    remove_parser.add_argument(
        "--id", type=int, required=True, help="Blocklist item ID"
    )

    blocklist_subparsers.add_parser("clear", help="Clear entire blocklist")

    # Health command
    subparsers.add_parser("health", help="Check system health")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        client = setup_client(args)

        if args.command == "backup":
            if args.backup_command == "create":
                create_backup(client)
            elif args.backup_command == "list":
                list_backups(client)
            elif args.backup_command == "restore":
                restore_backup(client, args.name)
            else:
                backup_parser.print_help()
                return 1

        elif args.command == "blocklist":
            if args.blocklist_command == "view":
                view_blocklist(client, args.page, args.page_size)
            elif args.blocklist_command == "remove":
                remove_blocklist_item(client, args.id)
            elif args.blocklist_command == "clear":
                clear_blocklist(client)
            else:
                blocklist_parser.print_help()
                return 1

        elif args.command == "health":
            system_health(client)

        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except (ConnectionError, ValueError, KeyError, TypeError) as e:
        print(f"Error: {e}")
        return 1


def cli_main() -> None:
    """Entry point for the CLI command."""
    sys.exit(main())


if __name__ == "__main__":
    cli_main()