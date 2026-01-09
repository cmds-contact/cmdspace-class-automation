"""Airtable 스키마 관리 모듈

테이블 생성 및 스키마 관리 기능을 제공합니다.
"""

from pyairtable import Api

from .. import config
from ..logger import logger


def _create_products_table(base) -> bool:
    """Products 테이블 생성

    Args:
        base: Airtable Base 객체

    Returns:
        생성 성공 여부
    """
    products_name = config.AIRTABLE_TABLES['products']

    try:
        base.create_table(
            products_name,
            fields=[
                {"name": "Product Code", "type": "singleLineText"},
                {"name": "Display Name", "type": "singleLineText"},
                {"name": "Is Subscription", "type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},
                {"name": "Subscription Days", "type": "number", "options": {"precision": 0}},
            ]
        )
        logger.info(f"{products_name} 테이블 생성 완료")
        return True
    except Exception as e:
        logger.error(f"{products_name} 테이블 생성 실패: {e}")
        return False


def _create_member_products_table(base, members_table_id: str | None, products_table_id: str | None) -> bool:
    """MemberProducts 테이블 생성

    Args:
        base: Airtable Base 객체
        members_table_id: Members 테이블 ID (Linked Record용)
        products_table_id: Products 테이블 ID (Linked Record용)

    Returns:
        생성 성공 여부
    """
    member_products_name = config.AIRTABLE_TABLES['member_products']

    # Primary field는 반드시 text 타입이어야 함
    fields = [
        {"name": "MemberProducts Code", "type": "singleLineText"},  # Primary field (MemberCode_ProductCode)
        {"name": "Subscription Status", "type": "singleSelect", "options": {
            "choices": [
                {"name": "Active", "color": "greenBright"},
                {"name": "Expired", "color": "redBright"},
                {"name": "N/A", "color": "grayBright"}
            ]
        }},
        {"name": "Last Payment Date", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
        {"name": "Expiry Date", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
        {"name": "Welcome Sent", "type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},
    ]

    # Linked Record 필드 추가 (Primary field 이후에)
    if members_table_id:
        fields.insert(1, {
            "name": "Member",
            "type": "multipleRecordLinks",
            "options": {"linkedTableId": members_table_id}
        })

    if products_table_id:
        fields.insert(2 if members_table_id else 1, {
            "name": "Product",
            "type": "multipleRecordLinks",
            "options": {"linkedTableId": products_table_id}
        })

    try:
        base.create_table(member_products_name, fields=fields)
        logger.info(f"{member_products_name} 테이블 생성 완료")
        return True
    except Exception as e:
        logger.error(f"{member_products_name} 테이블 생성 실패: {e}")
        return False


def ensure_tables_exist(api: Api) -> dict[str, bool]:
    """Products와 MemberProducts 테이블이 존재하는지 확인하고 없으면 생성

    pyairtable 3.x의 Base.schema() API를 사용하여 테이블 생성

    Args:
        api: Airtable API 클라이언트

    Returns:
        테이블별 생성 여부 딕셔너리
    """
    logger.info(f"\n{'='*50}")
    logger.info("테이블 존재 확인")
    logger.info(f"{'='*50}")

    results = {'products': False, 'member_products': False}

    # 기존 테이블 목록 조회
    try:
        base = api.base(config.AIRTABLE_BASE_ID)
        schema = base.schema()
        existing_tables = {table.name for table in schema.tables}
        logger.info(f"기존 테이블: {', '.join(existing_tables)}")
    except Exception as e:
        logger.error(f"스키마 조회 실패: {e}")
        return results

    # Products 테이블 확인/생성
    products_name = config.AIRTABLE_TABLES['products']
    if products_name not in existing_tables:
        logger.info(f"\n{products_name} 테이블 생성 중...")
        results['products'] = _create_products_table(base)
    else:
        logger.info(f"{products_name} 테이블 이미 존재")

    # MemberProducts 테이블 확인/생성
    member_products_name = config.AIRTABLE_TABLES['member_products']
    if member_products_name not in existing_tables:
        logger.info(f"\n{member_products_name} 테이블 생성 중...")

        # Members와 Products 테이블 ID 조회
        members_table_id = None
        products_table_id = None

        # 다시 스키마 조회 (Products가 방금 생성됐을 수 있음)
        schema = base.schema()
        for table in schema.tables:
            if table.name == config.AIRTABLE_TABLES['members']:
                members_table_id = table.id
            elif table.name == products_name:
                products_table_id = table.id

        results['member_products'] = _create_member_products_table(
            base, members_table_id, products_table_id
        )
    else:
        logger.info(f"{member_products_name} 테이블 이미 존재")

    return results
