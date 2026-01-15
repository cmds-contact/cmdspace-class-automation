"""MemberProducts -> MemberPrograms 마이그레이션 스크립트

실행 전 체크리스트:
1. Airtable에서 MemberProducts 테이블을 MemberPrograms로 이름 변경
2. MemberProducts Code 필드를 MemberPrograms Code로 이름 변경
3. Orders 테이블의 MemberProducts 필드를 MemberPrograms로 이름 변경
4. 이 스크립트 실행 (Code 재생성 및 중복 병합)

사용법:
    # Dry run (시뮬레이션만)
    python -c "from src.airtable.migration import migrate_to_member_programs; migrate_to_member_programs(dry_run=True)"

    # 실제 마이그레이션
    python -c "from src.airtable.migration import migrate_to_member_programs; migrate_to_member_programs(dry_run=False)"
"""

from collections import defaultdict

from pyairtable import Api

from ... import config
from ...logger import logger
from ...utils import batch_iterator, extract_program_code

from ..client import get_api, get_table


def migrate_to_member_programs(api: Api = None, dry_run: bool = True) -> dict:
    """MemberProducts Code를 MemberPrograms Code로 마이그레이션

    기존 레코드의 Code를 새 규칙(Program Code 기반)으로 재생성하고,
    같은 프로그램의 다른 옵션으로 생긴 중복 레코드를 병합합니다.

    Args:
        api: Airtable API 클라이언트
        dry_run: True면 실제 변경 없이 시뮬레이션만

    Returns:
        마이그레이션 결과 딕셔너리
    """
    if api is None:
        api = get_api()

    logger.info(f"\n{'='*60}")
    logger.info("MemberPrograms 마이그레이션" + (" (DRY RUN)" if dry_run else ""))
    logger.info("=" * 60)

    member_programs_table = get_table(api, config.AIRTABLE_TABLES['member_programs'])
    members_table = get_table(api, config.AIRTABLE_TABLES['members'])
    products_table = get_table(api, config.AIRTABLE_TABLES['products'])

    # 1. 현재 레코드 분석
    all_records = member_programs_table.all()
    logger.info(f"총 레코드: {len(all_records)}개")

    # Members: record_id -> Member Code
    members_by_id = {}
    for record in members_table.all():
        member_code = record['fields'].get('Member Code')
        if member_code:
            members_by_id[record['id']] = member_code

    # Products: record_id -> Product Code
    products_by_id = {}
    for record in products_table.all():
        product_code = record['fields'].get('Product Code')
        if product_code:
            products_by_id[record['id']] = product_code

    logger.info(f"Members: {len(members_by_id)}개")
    logger.info(f"Products: {len(products_by_id)}개")

    # 2. 새 Code 계산 및 그룹화
    # new_code -> list of record data (중복 감지용)
    code_groups: dict[str, list[dict]] = defaultdict(list)
    skipped = 0

    for record in all_records:
        old_code = record['fields'].get('MemberPrograms Code', '')
        member_links = record['fields'].get('Member', [])
        product_links = record['fields'].get('Product', [])

        if not member_links or not product_links:
            logger.warning(f"연결 누락: {record['id']}")
            skipped += 1
            continue

        member_id = member_links[0]
        product_id = product_links[0]

        member_code = members_by_id.get(member_id)
        product_code = products_by_id.get(product_id)

        if not member_code or not product_code:
            logger.warning(f"코드 누락: {record['id']}")
            skipped += 1
            continue

        # *** 핵심: Program Code 추출 ***
        program_code = extract_program_code(product_code)
        new_code = f"{member_code}_{program_code}"

        code_groups[new_code].append({
            'id': record['id'],
            'old_code': old_code,
            'member_code': member_code,
            'product_code': product_code,
            'program_code': program_code,
            'welcome_sent': record['fields'].get('Welcome Sent', False),
        })

    # 3. 중복 분석
    unique_codes = {k: v for k, v in code_groups.items() if len(v) == 1}
    duplicate_codes = {k: v for k, v in code_groups.items() if len(v) > 1}

    logger.info(f"\n분석 결과:")
    logger.info(f"  고유 Code: {len(unique_codes)}개")
    logger.info(f"  중복 Code: {len(duplicate_codes)}개 ({sum(len(v) for v in duplicate_codes.values())} 레코드)")
    logger.info(f"  건너뜀: {skipped}개")

    # 4. 마이그레이션 계획
    records_to_update = []
    records_to_delete = []

    # 4a. 고유 Code - 단순 업데이트
    for new_code, records in unique_codes.items():
        rec = records[0]
        if rec['old_code'] != new_code:
            records_to_update.append({
                'id': rec['id'],
                'fields': {'MemberPrograms Code': new_code}
            })

    # 4b. 중복 Code - 병합
    for new_code, records in duplicate_codes.items():
        # 대표 레코드 선택 (Welcome Sent = True 우선, 없으면 첫 번째)
        representative = next(
            (r for r in records if r['welcome_sent']),
            records[0]
        )

        # 대표 레코드 업데이트
        if representative['old_code'] != new_code:
            records_to_update.append({
                'id': representative['id'],
                'fields': {'MemberPrograms Code': new_code}
            })

        # 나머지 레코드 삭제 예정
        for rec in records:
            if rec['id'] != representative['id']:
                records_to_delete.append(rec)

        logger.info(f"\n병합: {new_code}")
        logger.info(f"  대표: {representative['product_code']} (Welcome Sent: {representative['welcome_sent']})")
        for rec in records:
            if rec['id'] != representative['id']:
                logger.info(f"  제거: {rec['product_code']}")

    logger.info(f"\n마이그레이션 계획:")
    logger.info(f"  업데이트 예정: {len(records_to_update)}개")
    logger.info(f"  삭제 예정: {len(records_to_delete)}개")

    # 5. 실행 (dry_run이 아닐 때만)
    if dry_run:
        logger.info("\n" + "=" * 60)
        logger.info("DRY RUN - 실제 변경 없음")
        logger.info("=" * 60)
        return {
            'dry_run': True,
            'total': len(all_records),
            'unique': len(unique_codes),
            'duplicates': len(duplicate_codes),
            'to_update': len(records_to_update),
            'to_delete': len(records_to_delete),
            'skipped': skipped,
        }

    # 업데이트 실행
    updated = 0
    if records_to_update:
        for batch in batch_iterator(records_to_update, 10):
            member_programs_table.batch_update(batch)
            updated += len(batch)
        logger.info(f"업데이트 완료: {updated}개")

    # 삭제 대상 레코드 목록 출력 (수동 처리 권장)
    # 프로젝트 규칙상 자동 삭제 대신 수동 처리
    if records_to_delete:
        logger.warning(f"\n{'='*60}")
        logger.warning("삭제 대상 레코드 (수동 처리 필요)")
        logger.warning("=" * 60)
        logger.warning(f"총 {len(records_to_delete)}개 레코드를 Airtable에서 수동으로 삭제하세요:")
        for rec in records_to_delete:
            logger.warning(f"  - ID: {rec['id']}")
            logger.warning(f"    이전 Code: {rec['old_code']}")
            logger.warning(f"    Product: {rec['product_code']}")

    logger.info(f"\n{'='*60}")
    logger.info("마이그레이션 완료")
    logger.info("=" * 60)

    return {
        'dry_run': False,
        'total': len(all_records),
        'unique': len(unique_codes),
        'duplicates': len(duplicate_codes),
        'updated': updated,
        'to_delete_manually': len(records_to_delete),
        'skipped': skipped,
    }


if __name__ == '__main__':
    import sys
    dry_run = '--execute' not in sys.argv
    result = migrate_to_member_programs(dry_run=dry_run)
    print(f"\n결과: {result}")
