"""Airtable 동기화 패키지

이 패키지는 publ.biz 데이터를 Airtable로 동기화하는 기능을 제공합니다.
"""

from .client import get_api, get_table
from .csv_reader import read_csv, find_csv
from .records import (
    get_existing_by_key,
    get_existing_orders,
    get_existing_member_programs,
    get_pending_refunds,
)
from .validators import check_airtable_duplicates, check_csv_duplicates

# Sync functions
from .sync import (
    sync_members,
    sync_orders,
    sync_refunds,
    sync_products,
    sync_member_programs,
    update_orders_member_programs_link,
)

# Schema, History, Maintenance
from .schema import ensure_tables_exist
from .history import record_sync_history
from .maintenance import (
    backfill_iso_dates,
    fix_member_programs_codes,
    backfill_is_active,
    validate_required_fields,
    backfill_refunds_orders_link,
    count_active_members,
    count_csv_members,
    deactivate_withdrawn_members,
)

__all__ = [
    # Client
    'get_api',
    'get_table',
    # CSV
    'read_csv',
    'find_csv',
    # Records
    'get_existing_by_key',
    'get_existing_orders',
    'get_existing_member_programs',
    'get_pending_refunds',
    # Validators
    'check_airtable_duplicates',
    'check_csv_duplicates',
    # Sync
    'sync_members',
    'sync_orders',
    'sync_refunds',
    'sync_products',
    'sync_member_programs',
    'update_orders_member_programs_link',
    # Schema, History, Maintenance
    'ensure_tables_exist',
    'record_sync_history',
    'backfill_iso_dates',
    'fix_member_programs_codes',
    'backfill_is_active',
    'validate_required_fields',
    'backfill_refunds_orders_link',
    # Member management
    'count_active_members',
    'count_csv_members',
    'deactivate_withdrawn_members',
]
