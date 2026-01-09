"""상품(Products) 동기화 모듈

Orders CSV에서 상품 정보를 추출하여 Products 테이블로 동기화합니다.
"""

from pyairtable import Api

from ... import config
from ...logger import logger
from ...utils import batch_iterator

from ..client import get_table
from ..csv_reader import read_csv, find_csv
from ..records import get_existing_by_key

# Airtable 배치 크기 (API 제한)
AIRTABLE_BATCH_SIZE = 10


def sync_products(api: Api) -> int:
    """Orders 데이터에서 상품 정보를 추출하여 Products 테이블에 동기화

    Args:
        api: Airtable API 클라이언트

    Returns:
        삽입된 레코드 수
    """
    table_config = config.TABLES['orders']
    file_path = find_csv(table_config['file_pattern'])
    products_table = get_table(api, config.AIRTABLE_TABLES['products'])

    logger.info(f"\n{'='*50}")
    logger.info(f"Airtable 상품 동기화")
    logger.info(f"{'='*50}")

    csv_data = read_csv(file_path)

    # 상품별 Payment Type 수집 (구독 여부 판단용)
    product_payment_types: dict[str, set[str]] = {}
    for row in csv_data:
        product_name = row.get('Product name', '').strip()
        payment_type = row.get('Payment Type', '').strip()
        if product_name:
            if product_name not in product_payment_types:
                product_payment_types[product_name] = set()
            if payment_type:
                product_payment_types[product_name].add(payment_type)

    logger.info(f"CSV에서 발견된 상품: {len(product_payment_types)}종")

    # 기존 상품 조회
    existing_products = get_existing_by_key(products_table, 'Product Code')
    logger.info(f"Airtable 기존 상품: {len(existing_products)}")

    # 신규 상품만 추가
    new_records = []
    for product_name, payment_types in product_payment_types.items():
        if product_name in existing_products:
            continue

        # Payment Type이 "Regular Payment"를 포함하면 구독 상품
        is_subscription = 'Regular Payment' in payment_types

        record_fields = {
            'Product Code': product_name,
            'Display Name': '',  # 수동 입력용
            'Is Subscription': is_subscription,
            # Subscription Days는 수동 입력
        }
        new_records.append(record_fields)

    logger.info(f"새 상품: {len(new_records)}")

    if not new_records:
        return 0

    inserted = 0
    for batch in batch_iterator(new_records, AIRTABLE_BATCH_SIZE):
        products_table.batch_create(batch)
        inserted += len(batch)

    logger.info(f"상품 삽입 완료: {inserted}개")
    return inserted
