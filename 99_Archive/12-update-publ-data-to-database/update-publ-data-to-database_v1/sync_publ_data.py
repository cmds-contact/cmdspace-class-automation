#!/usr/bin/env python3
"""
Publ Data to Supabase Sync Script
- Syncs members, orders, and refunds data
- Only inserts NEW records (deduplication by unique keys)
- Updates refund statuses if changed
"""

import os
import csv
import glob
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Table configuration
TABLES = {
    'members': {
        'name': 'publ-member-db',
        'file_pattern': '*_members.csv',
        'unique_key': 'Member Code'
    },
    'orders': {
        'name': 'publ-order-db',
        'file_pattern': '*_orders_latest.csv',
        'unique_key': 'Order Number'
    },
    'refunds': {
        'name': 'publ-refund-db',
        'file_pattern': '*_refunds.csv',
        'unique_key': 'Order Number'
    }
}

# Processing order as specified
PROCESSING_ORDER = ['members', 'orders', 'refunds']


def get_supabase_client():
    """Create and return Supabase client"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def read_csv_file(file_path):
    """Read CSV file with UTF-8 BOM encoding"""
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        return list(reader)


def find_csv_file(data_dir, pattern):
    """Find CSV file matching pattern in data directory"""
    files = glob.glob(os.path.join(data_dir, pattern))
    if not files:
        raise FileNotFoundError(f"No file matching pattern: {pattern}")
    return files[0]  # Return most recent if multiple


def get_existing_keys(supabase, table_name, key_column):
    """Fetch all existing unique keys from Supabase table"""
    all_keys = set()
    page_size = 1000
    offset = 0

    while True:
        # Use select('*') to avoid issues with column names containing spaces
        result = supabase.table(table_name).select('*').range(offset, offset + page_size - 1).execute()
        if not result.data:
            break
        for row in result.data:
            all_keys.add(row[key_column])
        if len(result.data) < page_size:
            break
        offset += page_size

    return all_keys


def sync_members(supabase, data_dir):
    """Sync members data - insert only new records"""
    config = TABLES['members']
    file_path = find_csv_file(data_dir, config['file_pattern'])

    print(f"\n{'='*50}")
    print(f"Syncing MEMBERS from: {os.path.basename(file_path)}")
    print(f"{'='*50}")

    # Read CSV data
    csv_data = read_csv_file(file_path)
    print(f"CSV records: {len(csv_data)}")

    # Get existing keys from Supabase
    existing_keys = get_existing_keys(supabase, config['name'], config['unique_key'])
    print(f"Existing records in Supabase: {len(existing_keys)}")

    # Filter new records
    new_records = [row for row in csv_data if row[config['unique_key']] not in existing_keys]
    print(f"New records to insert: {len(new_records)}")

    # Insert new records
    if new_records:
        # Remove 'Number' column as it's auto-generated or not needed
        for record in new_records:
            if 'Number' in record:
                del record['Number']

        # Insert in batches
        batch_size = 100
        inserted = 0
        for i in range(0, len(new_records), batch_size):
            batch = new_records[i:i + batch_size]
            result = supabase.table(config['name']).insert(batch).execute()
            inserted += len(result.data)

        print(f"Successfully inserted: {inserted} records")
    else:
        print("No new records to insert")

    return len(new_records)


def sync_orders(supabase, data_dir):
    """Sync orders data - insert only new records"""
    config = TABLES['orders']
    file_path = find_csv_file(data_dir, config['file_pattern'])

    print(f"\n{'='*50}")
    print(f"Syncing ORDERS from: {os.path.basename(file_path)}")
    print(f"{'='*50}")

    # Read CSV data
    csv_data = read_csv_file(file_path)
    print(f"CSV records: {len(csv_data)}")

    # Get existing keys from Supabase
    existing_keys = get_existing_keys(supabase, config['name'], config['unique_key'])
    print(f"Existing records in Supabase: {len(existing_keys)}")

    # Filter new records
    new_records = [row for row in csv_data if row[config['unique_key']] not in existing_keys]
    print(f"New records to insert: {len(new_records)}")

    # Insert new records
    if new_records:
        for record in new_records:
            if 'Number' in record:
                del record['Number']

        batch_size = 100
        inserted = 0
        for i in range(0, len(new_records), batch_size):
            batch = new_records[i:i + batch_size]
            result = supabase.table(config['name']).insert(batch).execute()
            inserted += len(result.data)

        print(f"Successfully inserted: {inserted} records")
    else:
        print("No new records to insert")

    return len(new_records)


def sync_refunds(supabase, data_dir):
    """Sync refunds data - insert new records and update status changes"""
    config = TABLES['refunds']
    file_path = find_csv_file(data_dir, config['file_pattern'])

    print(f"\n{'='*50}")
    print(f"Syncing REFUNDS from: {os.path.basename(file_path)}")
    print(f"{'='*50}")

    # Read CSV data
    csv_data = read_csv_file(file_path)
    print(f"CSV records: {len(csv_data)}")

    # Get existing records from Supabase (need full data for status comparison)
    existing_data = {}
    page_size = 1000
    offset = 0

    while True:
        result = supabase.table(config['name']).select('*').range(offset, offset + page_size - 1).execute()
        if not result.data:
            break
        for row in result.data:
            existing_data[row[config['unique_key']]] = row
        if len(result.data) < page_size:
            break
        offset += page_size

    print(f"Existing records in Supabase: {len(existing_data)}")

    new_records = []
    update_records = []

    for row in csv_data:
        order_number = row[config['unique_key']]
        if order_number not in existing_data:
            new_records.append(row)
        else:
            # Check if status changed
            existing_status = existing_data[order_number].get('Refund Status')
            new_status = row.get('Refund Status')
            if existing_status != new_status:
                update_records.append({
                    'order_number': order_number,
                    'new_status': new_status,
                    'old_status': existing_status
                })

    print(f"New records to insert: {len(new_records)}")
    print(f"Records to update (status changed): {len(update_records)}")

    # Insert new records
    if new_records:
        for record in new_records:
            if 'Number' in record:
                del record['Number']

        batch_size = 100
        inserted = 0
        for i in range(0, len(new_records), batch_size):
            batch = new_records[i:i + batch_size]
            result = supabase.table(config['name']).insert(batch).execute()
            inserted += len(result.data)

        print(f"Successfully inserted: {inserted} records")

    # Update status changes
    if update_records:
        updated = 0
        for update in update_records:
            result = supabase.table(config['name']).update({
                'Refund Status': update['new_status']
            }).eq(config['unique_key'], update['order_number']).execute()
            if result.data:
                updated += 1
                print(f"  Updated {update['order_number']}: {update['old_status']} -> {update['new_status']}")

        print(f"Successfully updated: {updated} records")

    return len(new_records), len(update_records)


def main():
    """Main sync function"""
    print("\n" + "="*60)
    print("PUBL DATA TO SUPABASE SYNC")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # Initialize Supabase client
    supabase = get_supabase_client()

    # Data directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'publ-data')

    if not os.path.exists(data_dir):
        print(f"Error: Data directory not found: {data_dir}")
        return

    results = {}

    # Process in order: members -> orders -> refunds
    for data_type in PROCESSING_ORDER:
        try:
            if data_type == 'members':
                results['members'] = {'new': sync_members(supabase, data_dir)}
            elif data_type == 'orders':
                results['orders'] = {'new': sync_orders(supabase, data_dir)}
            elif data_type == 'refunds':
                new_count, update_count = sync_refunds(supabase, data_dir)
                results['refunds'] = {'new': new_count, 'updated': update_count}
        except Exception as e:
            print(f"\nError processing {data_type}: {e}")
            results[data_type] = {'error': str(e)}

    # Summary
    print("\n" + "="*60)
    print("SYNC SUMMARY")
    print("="*60)
    for data_type, result in results.items():
        if 'error' in result:
            print(f"{data_type.upper()}: ERROR - {result['error']}")
        elif 'updated' in result:
            print(f"{data_type.upper()}: {result['new']} new, {result['updated']} updated")
        else:
            print(f"{data_type.upper()}: {result['new']} new")

    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    return results


if __name__ == '__main__':
    main()
