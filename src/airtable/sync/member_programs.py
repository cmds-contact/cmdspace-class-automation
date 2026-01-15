"""회원별 프로그램(MemberPrograms) 동기화 모듈

회원과 프로그램의 조합을 MemberPrograms 테이블로 동기화합니다.
동일 프로그램의 다른 구매 옵션은 하나의 레코드로 관리됩니다.

Program Code 추출 규칙:
- Product Code의 처음 3개 세그먼트를 Program Code로 사용
- 예: KM-CMDS-OBM-ME-1 -> KM-CMDS-OBM
- 뒷부분(ME-1, YE-2 등)은 구매 옵션을 나타냄
"""

from pyairtable import Api

from ... import config
from ...logger import logger
from ...utils import batch_iterator, extract_program_code

from ..client import get_table
from ..records import get_existing_by_key, get_existing_member_programs

# Airtable 배치 크기 (API 제한)
AIRTABLE_BATCH_SIZE = 10


def sync_member_programs(api: Api) -> dict[str, int]:
    """회원별 프로그램 조합을 MemberPrograms 테이블에 동기화 (신규만)

    구독 상태 및 만료일은 Airtable Formula가 처리.
    이 함수는 신규 MemberPrograms 레코드 생성만 담당.

    Args:
        api: Airtable API 클라이언트

    Returns:
        {'new': int} 딕셔너리
    """
    logger.info(f"\n{'='*50}")
    logger.info(f"Airtable 회원별 프로그램 동기화 (신규만)")
    logger.info(f"{'='*50}")

    # 테이블 객체
    orders_table = get_table(api, config.AIRTABLE_TABLES['orders'])
    members_table = get_table(api, config.AIRTABLE_TABLES['members'])
    products_table = get_table(api, config.AIRTABLE_TABLES['products'])
    member_programs_table = get_table(api, config.AIRTABLE_TABLES['member_programs'])

    # 기존 데이터 조회
    logger.info("데이터 조회 중...")

    # Members: Member Code -> record_id
    existing_members = get_existing_by_key(members_table, 'Member Code')

    # Products: Product Code -> record_id
    # Program Code로 시작하는 Product 중 하나를 대표로 사용
    products_data: dict[str, str] = {}
    products_by_program: dict[str, str] = {}  # Program Code -> 첫 번째 Product record_id
    for record in products_table.all():
        product_code = record['fields'].get('Product Code')
        if product_code:
            products_data[product_code] = record['id']
            program_code = extract_program_code(product_code)
            if program_code not in products_by_program:
                products_by_program[program_code] = record['id']

    # MemberPrograms: MemberPrograms Code -> record_id
    existing_member_programs = get_existing_member_programs(member_programs_table)

    logger.info(f"  Members: {len(existing_members)}개")
    logger.info(f"  Products: {len(products_data)}개")
    logger.info(f"  Programs (고유): {len(products_by_program)}개")
    logger.info(f"  MemberPrograms 기존: {len(existing_member_programs)}개")

    # Orders에서 (Member Code, Program Code) 조합 수집
    logger.info("Orders 집계 중...")
    member_program_combos: set[tuple[str, str]] = set()

    for record in orders_table.all():
        member_code = record['fields'].get('Member Code')
        product_name = record['fields'].get('Product name')
        if member_code and product_name:
            # Product Code에서 Program Code 추출
            program_code = extract_program_code(product_name)
            member_program_combos.add((member_code, program_code))

    logger.info(f"  회원+프로그램 조합: {len(member_program_combos)}개")

    # 신규 레코드 생성
    new_records = []
    for member_code, program_code in member_program_combos:
        member_programs_code = f"{member_code}_{program_code}"

        # 이미 존재하면 건너뛰기
        if member_programs_code in existing_member_programs:
            continue

        member_id = existing_members.get(member_code)
        product_id = products_by_program.get(program_code)

        if not member_id or not product_id:
            continue

        record_fields = {
            'MemberPrograms Code': member_programs_code,
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
            member_programs_table.batch_create(batch)
            inserted += len(batch)
        logger.info(f"삽입 완료: {inserted}개")

    return {'new': inserted}
