"""회원별 상품(MemberProducts) 동기화 모듈

회원과 상품의 조합을 MemberProducts 테이블로 동기화합니다.
"""

from pyairtable import Api

from ... import config
from ...logger import logger
from ...utils import batch_iterator

from ..client import get_table
from ..records import get_existing_by_key, get_existing_member_products

# Airtable 배치 크기 (API 제한)
AIRTABLE_BATCH_SIZE = 10


def sync_member_products(api: Api) -> dict[str, int]:
    """회원별 상품 조합을 MemberProducts 테이블에 동기화 (신규만)

    구독 상태 및 만료일은 Airtable Formula가 처리.
    이 함수는 신규 MemberProducts 레코드 생성만 담당.

    Args:
        api: Airtable API 클라이언트

    Returns:
        {'new': int} 딕셔너리
    """
    logger.info(f"\n{'='*50}")
    logger.info(f"Airtable 회원별 상품 동기화 (신규만)")
    logger.info(f"{'='*50}")

    # 테이블 객체
    orders_table = get_table(api, config.AIRTABLE_TABLES['orders'])
    members_table = get_table(api, config.AIRTABLE_TABLES['members'])
    products_table = get_table(api, config.AIRTABLE_TABLES['products'])
    member_products_table = get_table(api, config.AIRTABLE_TABLES['member_products'])

    # 기존 데이터 조회
    logger.info("데이터 조회 중...")

    # Members: Member Code -> record_id
    existing_members = get_existing_by_key(members_table, 'Member Code')

    # Products: Product Code -> record_id
    products_data: dict[str, str] = {}
    for record in products_table.all():
        product_code = record['fields'].get('Product Code')
        if product_code:
            products_data[product_code] = record['id']

    # MemberProducts: MemberProducts Code -> record_id
    existing_member_products = get_existing_member_products(member_products_table)

    logger.info(f"  Members: {len(existing_members)}개")
    logger.info(f"  Products: {len(products_data)}개")
    logger.info(f"  MemberProducts 기존: {len(existing_member_products)}개")

    # Orders에서 (Member Code, Product name) 조합 수집
    logger.info("Orders 집계 중...")
    member_product_combos: set[tuple[str, str]] = set()

    for record in orders_table.all():
        member_code = record['fields'].get('Member Code')
        product_name = record['fields'].get('Product name')
        if member_code and product_name:
            member_product_combos.add((member_code, product_name))

    logger.info(f"  회원+상품 조합: {len(member_product_combos)}개")

    # 신규 레코드 생성
    new_records = []
    for member_code, product_name in member_product_combos:
        member_products_code = f"{member_code}_{product_name}"

        # 이미 존재하면 건너뛰기
        if member_products_code in existing_member_products:
            continue

        member_id = existing_members.get(member_code)
        product_id = products_data.get(product_name)

        if not member_id or not product_id:
            continue

        record_fields = {
            'MemberProducts Code': member_products_code,
            'Member': [member_id],
            'Product': [product_id],
            'Welcome Sent': False,
        }
        new_records.append(record_fields)

    logger.info(f"새 레코드: {len(new_records)}")

    # 레코드 삽입
    inserted = 0
    if new_records:
        for batch in batch_iterator(new_records, AIRTABLE_BATCH_SIZE):
            member_products_table.batch_create(batch)
            inserted += len(batch)
        logger.info(f"삽입 완료: {inserted}개")

    return {'new': inserted}
