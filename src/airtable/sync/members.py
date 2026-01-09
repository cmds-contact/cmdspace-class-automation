"""회원(Members) 동기화 모듈

CSV 데이터를 Members 테이블로 동기화합니다.
"""

from pyairtable import Api

from ... import config
from ...logger import logger
from ...utils import safe_get, batch_iterator, to_iso_datetime

from ..client import get_table
from ..csv_reader import read_csv, find_csv
from ..records import get_existing_by_key
from ..validators import check_airtable_duplicates, check_csv_duplicates

# Airtable 배치 크기 (API 제한)
AIRTABLE_BATCH_SIZE = 10


def sync_members(api: Api) -> int:
    """회원 데이터를 CSV에서 읽어 Airtable로 동기화

    중복 방지 로직 포함:
    - Airtable 기존 중복 검사
    - CSV 내 중복 검사
    - 삽입 후 카운트 검증

    Args:
        api: Airtable API 클라이언트

    Returns:
        삽입된 레코드 수
    """
    table_config = config.TABLES['members']
    file_path = find_csv(table_config['file_pattern'])
    table = get_table(api, config.AIRTABLE_TABLES['members'])

    logger.info(f"\n{'='*50}")
    logger.info(f"Airtable 회원 동기화: {file_path.split('/')[-1]}")
    logger.info(f"{'='*50}")

    csv_data = read_csv(file_path)
    logger.info(f"CSV 레코드: {len(csv_data)}")

    # [중복 방지] Airtable 기존 중복 검사
    airtable_duplicates = check_airtable_duplicates(table, 'Member Code')
    if airtable_duplicates:
        logger.warning(f"Airtable 중복 발견: {len(airtable_duplicates)}개")
        for code, record_ids in list(airtable_duplicates.items())[:3]:
            logger.info(f"   - {code}: {len(record_ids)}개 레코드")

    # [중복 방지] CSV 내 중복 검사
    csv_duplicates = check_csv_duplicates(csv_data, 'Member Code')
    if csv_duplicates:
        logger.warning(f"CSV 내 중복 발견: {len(csv_duplicates)}개")
        for code, count in list(csv_duplicates.items())[:3]:
            logger.info(f"   - {code}: {count}회")

    existing = get_existing_by_key(table, 'Member Code')
    logger.info(f"Airtable 기존 레코드: {len(existing)}")

    new_records = []
    for row in csv_data:
        member_code = row.get('Member Code')
        if not member_code or member_code in existing:
            continue

        # Birth year 처리
        birth_year = row.get('Birth year')
        birth_year_str = str(birth_year) if birth_year else ''

        # Sign-up Date를 ISO dateTime으로 변환
        signup_date_str = safe_get(row, 'Sign-up Date')
        signup_datetime = to_iso_datetime(signup_date_str)

        record_fields = {
            'Member Code': member_code,
            'Username': safe_get(row, 'Username'),
            'E-mail': safe_get(row, 'E-mail'),
            'Country': safe_get(row, 'Country'),
            'Name': safe_get(row, 'Name'),
            'Gender': safe_get(row, 'Gender'),
            'Birth year': birth_year_str,
            'Personal email address': safe_get(row, 'Personal email address'),
            'Mobile number': safe_get(row, 'Mobile number'),
            'Sign-up Date': signup_date_str,  # 원본 텍스트
            'Is Active': True,  # 새 회원은 활성 상태로 추가
        }

        # Sign-up Date (ISO) - dateTime 형식
        if signup_datetime:
            record_fields['Sign-up Date (ISO)'] = signup_datetime

        new_records.append(record_fields)

    logger.info(f"새 레코드: {len(new_records)}")

    if not new_records:
        return 0

    inserted = 0
    for batch in batch_iterator(new_records, AIRTABLE_BATCH_SIZE):
        table.batch_create(batch)
        inserted += len(batch)

    logger.info(f"삽입 완료: {inserted}개")

    # [중복 방지] 삽입 후 카운트 검증
    final_count = len(get_existing_by_key(table, 'Member Code'))
    expected_count = len(existing) + inserted
    if final_count != expected_count:
        logger.warning(f"카운트 불일치: 예상 {expected_count}개, 실제 {final_count}개")
    else:
        logger.info(f"✓ 카운트 검증 완료: {final_count}개")

    return inserted
