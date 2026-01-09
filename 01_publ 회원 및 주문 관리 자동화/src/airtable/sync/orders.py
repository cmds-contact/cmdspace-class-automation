"""주문(Orders) 동기화 모듈

CSV 데이터를 Orders 테이블로 동기화합니다.
"""

from typing import Any

from pyairtable import Api

from ... import config
from ...logger import logger
from ...utils import parse_price, safe_get, batch_iterator, to_iso_datetime

from ..client import get_table
from ..csv_reader import read_csv, find_csv
from ..records import get_existing_by_key, get_existing_orders, get_existing_member_products

# Airtable 배치 크기 (API 제한)
AIRTABLE_BATCH_SIZE = 10


def sync_orders(api: Api) -> int:
    """주문 데이터를 CSV에서 읽어 Airtable로 동기화 (Member Linked Record 포함)

    Args:
        api: Airtable API 클라이언트

    Returns:
        삽입된 레코드 수
    """
    table_config = config.TABLES['orders']
    file_path = find_csv(table_config['file_pattern'])
    orders_table = get_table(api, config.AIRTABLE_TABLES['orders'])
    members_table = get_table(api, config.AIRTABLE_TABLES['members'])

    logger.info(f"\n{'='*50}")
    logger.info(f"Airtable 주문 동기화: {file_path.split('/')[-1]}")
    logger.info(f"{'='*50}")

    csv_data = read_csv(file_path)
    logger.info(f"CSV 레코드: {len(csv_data)}")

    existing_orders = get_existing_orders(orders_table)
    existing_members = get_existing_by_key(members_table, 'Member Code')

    logger.info(f"Airtable 기존 주문: {len(existing_orders)}")

    new_records: list[dict[str, Any]] = []

    for row in csv_data:
        order_number = row.get('Order Number')
        if not order_number:
            continue

        # 이미 존재하는 주문은 건너뛰기 (신규만 추가)
        if order_number in existing_orders:
            continue

        member_code = safe_get(row, 'Member Code')
        member_id = existing_members.get(member_code)

        # Date and Time of Payment를 ISO dateTime으로 변환
        payment_date_str = safe_get(row, 'Date and Time of Payment')
        payment_datetime = to_iso_datetime(payment_date_str)

        record_fields = {
            'Order Number': order_number,
            'Product name': safe_get(row, 'Product name'),
            'Type': safe_get(row, 'Type'),
            'Price': parse_price(row.get('Price')),
            'Name': safe_get(row, 'Name'),
            'E-mail': safe_get(row, 'E-mail'),
            'Member Code': member_code,
            'Payment Type': safe_get(row, 'Payment Type'),
            'Payment Method': safe_get(row, 'Payment Method'),
            'Date and Time of Payment': payment_date_str,  # 원본 텍스트
        }

        # Date and Time of Payment (ISO) - dateTime 형식
        if payment_datetime:
            record_fields['Date and Time of Payment (ISO)'] = payment_datetime

        # Member Linked Record 추가
        if member_id:
            record_fields['Member'] = [member_id]

        new_records.append(record_fields)

    logger.info(f"새 레코드: {len(new_records)}")

    inserted = 0
    if new_records:
        for batch in batch_iterator(new_records, AIRTABLE_BATCH_SIZE):
            orders_table.batch_create(batch)
            inserted += len(batch)
        logger.info(f"삽입 완료: {inserted}개")

    return inserted


def update_orders_member_products_link(api: Api) -> int:
    """Orders 테이블의 MemberProducts Linked Record 업데이트

    MemberProducts 동기화 후 호출하여 Orders에 Linked Record 연결.
    이미 연결된 Orders는 건너뜀.

    Args:
        api: Airtable API 클라이언트

    Returns:
        업데이트된 레코드 수
    """
    logger.info(f"\n{'='*50}")
    logger.info(f"Orders → MemberProducts 연결 업데이트")
    logger.info(f"{'='*50}")

    orders_table = get_table(api, config.AIRTABLE_TABLES['orders'])
    member_products_table = get_table(api, config.AIRTABLE_TABLES['member_products'])

    # MemberProducts: MemberProducts Code -> record_id
    existing_member_products = get_existing_member_products(member_products_table)
    logger.info(f"MemberProducts: {len(existing_member_products)}개")

    # Orders 순회하여 연결되지 않은 레코드 찾기
    records_to_update = []
    orders_all = orders_table.all()
    logger.info(f"Orders 전체: {len(orders_all)}개")

    for record in orders_all:
        # 이미 MemberProducts가 연결되어 있으면 건너뛰기
        if record['fields'].get('MemberProducts'):
            continue

        member_code = record['fields'].get('Member Code')
        product_name = record['fields'].get('Product name')

        if not member_code or not product_name:
            continue

        member_products_code = f"{member_code}_{product_name}"
        member_products_id = existing_member_products.get(member_products_code)

        if member_products_id:
            records_to_update.append({
                'id': record['id'],
                'fields': {'MemberProducts': [member_products_id]}
            })

    logger.info(f"연결 대상: {len(records_to_update)}개")

    # 배치 업데이트
    updated = 0
    if records_to_update:
        for batch in batch_iterator(records_to_update, AIRTABLE_BATCH_SIZE):
            orders_table.batch_update(batch)
            updated += len(batch)
        logger.info(f"연결 완료: {updated}개")

    return updated
