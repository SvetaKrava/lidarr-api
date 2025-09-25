#!/usr/bin/env python3
"""
Lidarr Monitoring and Health Check Script

This script provides monitoring and health check functionality for Lidarr:
- System status monitoring
- Queue monitoring with alerts
- Disk space monitoring
- Failed download monitoring
- Performance metrics collection
- Health check with configurable alerts
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

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


def format_bytes(bytes_val: float) -> str:
    """Format bytes into human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} PB"


def format_duration(seconds: int) -> str:
    """Format seconds into human readable duration."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"


def system_status_check(client: LidarrClient, verbose: bool = False) -> Dict[str, Any]:
    """Perform comprehensive system status check."""
    results = {
        'timestamp': datetime.now().isoformat(),
        'status': 'healthy',
        'checks': {},
        'warnings': [],
        'errors': []
    }
    
    try:
        # Basic system status
        status = client.get_system_status()
        results['checks']['system_info'] = {
            'version': status.get('version'),
            'build_time': status.get('buildTime'),
            'start_time': status.get('startTime'),
            'runtime': f"{status.get('runtimeName')} {status.get('runtimeVersion')}",
            'os': f"{status.get('osName')} {status.get('osVersion')}"
        }
        
        # Calculate uptime
        if status.get('startTime'):
            try:
                start_time = datetime.fromisoformat(status['startTime'].replace('Z', '+00:00'))
                uptime_seconds = (datetime.now().replace(tzinfo=start_time.tzinfo) - start_time).total_seconds()
                results['checks']['uptime'] = format_duration(int(uptime_seconds))
            except:
                results['checks']['uptime'] = 'Unknown'
        
        if verbose:
            print(f"✓ Lidarr {status.get('version')} is running")
            print(f"  Uptime: {results['checks'].get('uptime', 'Unknown')}")
        
    except Exception as e:
        results['errors'].append(f"Failed to get system status: {e}")
        results['status'] = 'error'
        if verbose:
            print(f"✗ Failed to get system status: {e}")
    
    try:
        # Disk space check
        disk_space = client.get_disk_space()
        results['checks']['disk_space'] = []
        
        for disk in disk_space:
            path = disk.get('path', 'Unknown')
            free = disk.get('freeSpace', 0)
            total = disk.get('totalSpace', 0)
            
            if total > 0:
                free_gb = free / (1024**3)
                total_gb = total / (1024**3)
                used_percent = ((total - free) / total) * 100
                
                disk_info = {
                    'path': path,
                    'free_gb': round(free_gb, 1),
                    'total_gb': round(total_gb, 1),
                    'used_percent': round(used_percent, 1)
                }
                results['checks']['disk_space'].append(disk_info)
                
                # Check for low disk space
                if used_percent > 90:
                    results['errors'].append(f"Critical: Disk {path} is {used_percent:.1f}% full")
                    results['status'] = 'error'
                elif used_percent > 80:
                    results['warnings'].append(f"Warning: Disk {path} is {used_percent:.1f}% full")
                    if results['status'] == 'healthy':
                        results['status'] = 'warning'
                
                if verbose:
                    status_icon = "✗" if used_percent > 90 else "⚠" if used_percent > 80 else "✓"
                    print(f"{status_icon} Disk {path}: {free_gb:.1f} GB free of {total_gb:.1f} GB ({used_percent:.1f}% used)")
    
    except Exception as e:
        results['errors'].append(f"Failed to check disk space: {e}")
        if results['status'] != 'error':
            results['status'] = 'warning'
        if verbose:
            print(f"⚠ Failed to check disk space: {e}")
    
    try:
        # Queue status check
        queue_result = client.get_queue(page=1, page_size=100)
        queue_items = queue_result.get('records', [])
        total_queue = queue_result.get('totalRecords', 0)
        
        # Analyze queue
        active_downloads = len([item for item in queue_items if item.get('status') in ['downloading', 'queued']])
        failed_downloads = len([item for item in queue_items if item.get('status') in ['failed', 'warning']])
        stalled_downloads = len([item for item in queue_items if item.get('status') == 'delay'])
        
        results['checks']['queue'] = {
            'total_items': total_queue,
            'active_downloads': active_downloads,
            'failed_downloads': failed_downloads,
            'stalled_downloads': stalled_downloads
        }
        
        if failed_downloads > 0:
            results['warnings'].append(f"Warning: {failed_downloads} failed downloads in queue")
            if results['status'] == 'healthy':
                results['status'] = 'warning'
        
        if stalled_downloads > 5:
            results['warnings'].append(f"Warning: {stalled_downloads} stalled downloads")
            if results['status'] == 'healthy':
                results['status'] = 'warning'
        
        if verbose:
            status_icon = "⚠" if failed_downloads > 0 or stalled_downloads > 5 else "✓"
            print(f"{status_icon} Queue: {total_queue} total, {active_downloads} active, {failed_downloads} failed, {stalled_downloads} stalled")
    
    except Exception as e:
        results['errors'].append(f"Failed to check queue: {e}")
        if results['status'] != 'error':
            results['status'] = 'warning'
        if verbose:
            print(f"⚠ Failed to check queue: {e}")
    
    try:
        # Wanted albums check
        wanted_result = client.get_wanted(page=1, page_size=1)
        total_wanted = wanted_result.get('totalRecords', 0)
        results['checks']['wanted_albums'] = total_wanted
        
        if verbose:
            print(f"ℹ Wanted albums: {total_wanted}")
    
    except Exception as e:
        results['warnings'].append(f"Failed to check wanted albums: {e}")
        if results['status'] == 'healthy':
            results['status'] = 'warning'
        if verbose:
            print(f"⚠ Failed to check wanted albums: {e}")
    
    return results


def monitor_queue_continuously(client: LidarrClient, interval: int = 60, max_failed: int = 10) -> None:
    """Continuously monitor the download queue."""
    print(f"Starting continuous queue monitoring (checking every {interval} seconds)")
    print(f"Will alert if failed downloads exceed {max_failed}")
    print("Press Ctrl+C to stop...")
    
    try:
        while True:
            try:
                queue_result = client.get_queue(page=1, page_size=100)
                queue_items = queue_result.get('records', [])
                total_queue = queue_result.get('totalRecords', 0)
                
                active_downloads = len([item for item in queue_items if item.get('status') in ['downloading', 'queued']])
                failed_downloads = len([item for item in queue_items if item.get('status') in ['failed', 'warning']])
                stalled_downloads = len([item for item in queue_items if item.get('status') == 'delay'])
                
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                if failed_downloads > max_failed:
                    print(f"🚨 ALERT [{timestamp}]: {failed_downloads} failed downloads (threshold: {max_failed})")
                    
                    # Show details of failed downloads
                    failed_items = [item for item in queue_items if item.get('status') in ['failed', 'warning']]
                    for item in failed_items[:5]:  # Show first 5
                        artist = item.get('artist', {}).get('artistName', 'Unknown') if item.get('artist') else 'Unknown'
                        album = item.get('album', {}).get('title', 'Unknown') if item.get('album') else 'Unknown'
                        error_message = item.get('errorMessage', 'No error message')
                        print(f"  ✗ {artist} - {album}: {error_message}")
                    
                    if len(failed_items) > 5:
                        print(f"  ... and {len(failed_items) - 5} more failed items")
                
                else:
                    status_msg = f"[{timestamp}] Queue: {total_queue} total, {active_downloads} active"
                    if failed_downloads > 0:
                        status_msg += f", {failed_downloads} failed"
                    if stalled_downloads > 0:
                        status_msg += f", {stalled_downloads} stalled"
                    
                    print(status_msg)
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"Error monitoring queue: {e}")
                time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\nMonitoring stopped")


def check_recent_history(client: LidarrClient, hours: int = 24) -> None:
    """Check recent download history for issues."""
    try:
        # Get history from the last N hours
        since = datetime.now() - timedelta(hours=hours)
        since_str = since.isoformat()
        
        history = client.get_history(page=1, page_size=100, sort_key='date', sort_dir='desc')
        records = history.get('records', [])
        
        # Filter to recent items
        recent_records = []
        for record in records:
            try:
                record_date = datetime.fromisoformat(record.get('date', '').replace('Z', '+00:00'))
                if record_date >= since.replace(tzinfo=record_date.tzinfo):
                    recent_records.append(record)
            except:
                continue
        
        if not recent_records:
            print(f"No history items found in the last {hours} hours")
            return
        
        # Analyze recent history
        grabbed = len([r for r in recent_records if r.get('eventType') == 'grabbed'])
        imported = len([r for r in recent_records if r.get('eventType') == 'trackFileImported'])
        failed = len([r for r in recent_records if r.get('eventType') == 'downloadFailed'])
        
        print(f"Recent Activity (last {hours} hours):")
        print(f"  Grabbed: {grabbed}")
        print(f"  Imported: {imported}")
        print(f"  Failed: {failed}")
        
        if failed > 0:
            print("\nRecent Failures:")
            failed_items = [r for r in recent_records if r.get('eventType') == 'downloadFailed'][:10]
            for item in failed_items:
                artist = item.get('artist', {}).get('artistName', 'Unknown') if item.get('artist') else 'Unknown'
                album = item.get('album', {}).get('title', 'Unknown') if item.get('album') else 'Unknown'
                date = item.get('date', 'Unknown')
                try:
                    date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    date = date_obj.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
                
                print(f"  ✗ [{date}] {artist} - {album}")
        
        # Success rate
        total_attempts = grabbed
        success_rate = (imported / total_attempts * 100) if total_attempts > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}% ({imported}/{total_attempts})")
        
    except Exception as e:
        print(f"Error checking recent history: {e}")


def export_health_report(client: LidarrClient, output_file: str) -> None:
    """Export a comprehensive health report to JSON."""
    try:
        print("Generating comprehensive health report...")
        
        report = system_status_check(client, verbose=False)
        
        # Add additional details for export
        try:
            # Add artist count
            artists = client.get_all_artists()
            report['checks']['total_artists'] = len(artists)
            report['checks']['monitored_artists'] = len([a for a in artists if a.get('monitored')])
        except:
            report['warnings'].append("Failed to get artist statistics")
        
        try:
            # Add profile information
            quality_profiles = client.get_quality_profiles()
            metadata_profiles = client.get_metadata_profiles()
            report['checks']['profiles'] = {
                'quality_profiles_count': len(quality_profiles),
                'metadata_profiles_count': len(metadata_profiles)
            }
        except:
            report['warnings'].append("Failed to get profile information")
        
        try:
            # Add import list information
            import_lists = client.get_import_lists()
            enabled_lists = len([l for l in import_lists if l.get('enabled')])
            report['checks']['import_lists'] = {
                'total_lists': len(import_lists),
                'enabled_lists': enabled_lists
            }
        except:
            report['warnings'].append("Failed to get import list information")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"Health report exported to {output_file}")
        print(f"Overall status: {report['status'].upper()}")
        if report['warnings']:
            print(f"Warnings: {len(report['warnings'])}")
        if report['errors']:
            print(f"Errors: {len(report['errors'])}")
    
    except Exception as e:
        print(f"Error exporting health report: {e}")


def main() -> int:
    """Main entry point for the monitoring script."""
    parser = argparse.ArgumentParser(
        description="Lidarr monitoring and health check utilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick health check
  %(prog)s status
  
  # Detailed health check
  %(prog)s status --verbose
  
  # Monitor queue continuously
  %(prog)s monitor --interval 30
  
  # Check recent history
  %(prog)s history --hours 48
  
  # Export comprehensive health report
  %(prog)s export --output health_report.json
        """
    )
    
    parser.add_argument('--url', help='Lidarr server URL')
    parser.add_argument('--api-key', help='Lidarr API key')
    parser.add_argument('--config', help='Config file path')
    parser.add_argument('--timeout', type=int, default=60, help='Request timeout (default: 60)')
    parser.add_argument('--retries', type=int, default=3, help='Number of retries (default: 3)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check system status')
    status_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor queue continuously')
    monitor_parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds (default: 60)')
    monitor_parser.add_argument('--max-failed', type=int, default=10, help='Alert threshold for failed downloads (default: 10)')
    
    # History command
    history_parser = subparsers.add_parser('history', help='Check recent download history')
    history_parser.add_argument('--hours', type=int, default=24, help='Hours to look back (default: 24)')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export health report')
    export_parser.add_argument('--output', required=True, help='Output JSON file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        client = setup_client(args)
        
        if args.command == 'status':
            results = system_status_check(client, args.verbose)
            
            if not args.verbose:
                print(f"Overall Status: {results['status'].upper()}")
                if results['warnings']:
                    print(f"Warnings ({len(results['warnings'])}):")
                    for warning in results['warnings']:
                        print(f"  ⚠ {warning}")
                if results['errors']:
                    print(f"Errors ({len(results['errors'])}):")
                    for error in results['errors']:
                        print(f"  ✗ {error}")
            
            # Return appropriate exit code
            if results['status'] == 'error':
                return 2
            elif results['status'] == 'warning':
                return 1
            else:
                return 0
        
        elif args.command == 'monitor':
            monitor_queue_continuously(client, args.interval, args.max_failed)
        
        elif args.command == 'history':
            check_recent_history(client, args.hours)
        
        elif args.command == 'export':
            export_health_report(client, args.output)
        
        return 0
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())