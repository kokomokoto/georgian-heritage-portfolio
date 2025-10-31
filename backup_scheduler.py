#!/usr/bin/env python3
"""
Auto-backup scheduler for database
ავტომატური backup მონაცემთა ბაზისთვის
"""

import schedule
import time
import os
from database_backup import backup_database

def daily_backup():
    """Create daily backup"""
    try:
        backup_filename = backup_database()
        print(f"📅 Daily backup created: {backup_filename}")
        
        # Keep only last 7 backups
        cleanup_old_backups()
        
    except Exception as e:
        print(f"❌ Daily backup failed: {e}")

def cleanup_old_backups():
    """Keep only the last 7 backup files"""
    backups = [f for f in os.listdir('.') if f.startswith('database_backup_') and f.endswith('.json')]
    backups.sort(reverse=True)  # Latest first
    
    # Delete old backups (keep latest 7)
    for old_backup in backups[7:]:
        try:
            os.remove(old_backup)
            print(f"🗑️ Deleted old backup: {old_backup}")
        except Exception as e:
            print(f"❌ Failed to delete {old_backup}: {e}")

# Schedule daily backup at 3 AM
schedule.every().day.at("03:00").do(daily_backup)

if __name__ == "__main__":
    print("🕐 Starting backup scheduler...")
    print("Daily backups scheduled at 3:00 AM")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute