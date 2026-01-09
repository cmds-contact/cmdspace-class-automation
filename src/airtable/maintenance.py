"""Airtable 유지보수 모듈

데이터 백필 및 수정 기능을 제공합니다.
"""

from pyairtable import Api

from .. import config
from ..logger import logger
from ..utils import batch_iterator, to_iso_datetime

from .client import get_api, get_table
from .records import get_existing_orders

# Airtable 배치 크기 (API 제한)
AIRTABLE_BATCH_SIZE = 10


def backfill_iso_dates(api: Api = None) -> dict[str, int]:
    """기존 레코드의 (ISO) 날짜 필드를 채우는 백필 함수

    각 테이블에서 원본 날짜 필드는 있지만 (ISO) 필드가 비어있는 레코드를 찾아
    ISO 8601 형식으로 변환하여 업데이트

    Args:
        api: Airtable API 클라이언트 (없으면 새로 생성)

    Returns:
        테이블별 업데이트된 레코드 수
    """
    if api is None:
        api = get_api()

    logger.info(f"\n{'='*60}")
    logger.info("ISO 날짜 필드 백필 시작")
    logger.info("=" * 60)

    results = {}

    # 테이블별 필드 매핑: (테이블명, 원본필드, ISO필드)
    table_fields = [
        ('Members', 'Sign-up Date', 'Sign-up Date (ISO)'),
        ('Orders', 'Date and Time of Payment', 'Date and Time of Payment (ISO)'),
        ('Refunds', 'Refund Request Date', 'Refund Request Date (ISO)'),
    ]

    for table_name, original_field, iso_field in table_fields:
        logger.info(f"\n{'='*50}")
        logger.info(f"{table_name} 테이블 백필")
        logger.info(f"{'='*50}")

        table = get_table(api, table_name)
        all_records = table.all()
        logger.info(f"전체 레코드: {len(all_records)}")

        records_to_update = []

        for record in all_records:
            fields = record['fields']
            original_value = fields.get(original_field)
            iso_value = fields.get(iso_field)

            # 원본은 있는데 ISO가 없는 경우만 처리
            if original_value and not iso_value:
                # 먼저 표준 변환 시도 (YYYY-MM-DD HH:MM:SS 형식)
                iso_converted = to_iso_datetime(original_value)

                # 변환 실패 시, 이미 ISO 형식인지 확인 (T와 +/- 포함)
                if not iso_converted and 'T' in original_value:
                    # 이미 ISO 형식이면 그대로 사용
                    iso_converted = original_value

                if iso_converted:
                    records_to_update.append({
                        'id': record['id'],
                        'fields': {iso_field: iso_converted}
                    })

        logger.info(f"업데이트 대상: {len(records_to_update)}")

        if records_to_update:
            updated = 0
            for batch in batch_iterator(records_to_update, AIRTABLE_BATCH_SIZE):
                table.batch_update(batch)
                updated += len(batch)
            logger.info(f"업데이트 완료: {updated}개")
            results[table_name] = updated
        else:
            results[table_name] = 0

    logger.info(f"\n{'='*60}")
    logger.info("백필 완료")
    logger.info("=" * 60)

    return results


def fix_member_products_codes(api: Api = None) -> int:
    """MemberProducts 테이블의 잘못된 MemberProducts Code 필드를 수정

    MemberProducts Code 형식: MemberCode_ProductCode
    예: SUBIJIML5JEDXC7HCAK-JKWV2_KM-CMDS-OBM-ME-1

    Args:
        api: Airtable API 클라이언트 (없으면 새로 생성)

    Returns:
        수정된 레코드 수
    """
    if api is None:
        api = get_api()

    logger.info(f"\n{'='*60}")
    logger.info("MemberProducts Code 필드 수정")
    logger.info("=" * 60)

    member_products_table = get_table(api, config.AIRTABLE_TABLES['member_products'])
    members_table = get_table(api, config.AIRTABLE_TABLES['members'])
    products_table = get_table(api, config.AIRTABLE_TABLES['products'])

    # Members: record_id -> Member Code
    members_by_id: dict[str, str] = {}
    for record in members_table.all():
        member_code = record['fields'].get('Member Code')
        if member_code:
            members_by_id[record['id']] = member_code

    # Products: record_id -> Product Code
    products_by_id: dict[str, str] = {}
    for record in products_table.all():
        product_code = record['fields'].get('Product Code')
        if product_code:
            products_by_id[record['id']] = product_code

    logger.info(f"Members: {len(members_by_id)}개")
    logger.info(f"Products: {len(products_by_id)}개")

    # MemberProducts에서 잘못된 코드 찾기
    all_records = member_products_table.all()
    records_to_update = []

    for record in all_records:
        code = record['fields'].get('MemberProducts Code', '')

        # 코드에 '_'가 없으면 잘못된 형식
        if '_' not in code:
            member_links = record['fields'].get('Member', [])
            product_links = record['fields'].get('Product', [])

            if member_links and product_links:
                member_id = member_links[0]
                product_id = product_links[0]

                member_code = members_by_id.get(member_id)
                product_code = products_by_id.get(product_id)

                if member_code and product_code:
                    new_code = f"{member_code}_{product_code}"
                    records_to_update.append({
                        'id': record['id'],
                        'fields': {'MemberProducts Code': new_code}
                    })

    logger.info(f"수정 대상: {len(records_to_update)}개")

    if not records_to_update:
        logger.info("수정할 레코드가 없습니다.")
        return 0

    # 배치 업데이트
    updated = 0
    for batch in batch_iterator(records_to_update, AIRTABLE_BATCH_SIZE):
        member_products_table.batch_update(batch)
        updated += len(batch)

    logger.info(f"수정 완료: {updated}개")
    return updated


def backfill_is_active(api: Api = None) -> int:
    """기존 Members 레코드의 'Is Active' 필드를 True로 설정

    'Is Active'가 설정되지 않은 모든 회원을 활성 상태로 변경합니다.

    Args:
        api: Airtable API 클라이언트 (없으면 새로 생성)

    Returns:
        업데이트된 레코드 수
    """
    if api is None:
        api = get_api()

    logger.info(f"\n{'='*60}")
    logger.info("Members 'Is Active' 필드 백필")
    logger.info("=" * 60)

    table = get_table(api, config.AIRTABLE_TABLES['members'])
    all_records = table.all()
    logger.info(f"전체 회원: {len(all_records)}")

    records_to_update = []

    for record in all_records:
        is_active = record['fields'].get('Is Active')
        # Is Active가 None이거나 False인 경우 업데이트 대상
        if not is_active:
            records_to_update.append({
                'id': record['id'],
                'fields': {'Is Active': True}
            })

    logger.info(f"업데이트 대상: {len(records_to_update)}")

    if not records_to_update:
        logger.info("업데이트할 레코드가 없습니다.")
        return 0

    # 배치 업데이트
    updated = 0
    for batch in batch_iterator(records_to_update, AIRTABLE_BATCH_SIZE):
        table.batch_update(batch)
        updated += len(batch)

    logger.info(f"업데이트 완료: {updated}개")
    return updated


def validate_required_fields(api: Api = None, auto_fix: bool = True) -> dict[str, dict]:
    """테이블별 필수 필드 누락 검증 및 자동 복구

    config.REQUIRED_FIELDS에 정의된 필수 필드가 누락된 레코드를 감지하고,
    auto_fix=True인 경우 자동으로 기본값을 설정합니다.

    Args:
        api: Airtable API 클라이언트 (없으면 새로 생성)
        auto_fix: True면 누락된 필드를 자동으로 기본값으로 설정

    Returns:
        테이블별 검증 결과 딕셔너리
        {
            'members': {
                'total': 전체 레코드 수,
                'missing': {'Is Active': 누락 수, ...},
                'fixed': {'Is Active': 복구 수, ...}  # auto_fix=True인 경우
            }
        }
    """
    if api is None:
        api = get_api()

    logger.info(f"\n{'='*60}")
    logger.info("필수 필드 검증" + (" (자동 복구 활성화)" if auto_fix else ""))
    logger.info("=" * 60)

    results = {}

    for table_key, required_fields in config.REQUIRED_FIELDS.items():
        if not required_fields:
            continue

        table_name = config.AIRTABLE_TABLES.get(table_key)
        if not table_name:
            continue

        logger.info(f"\n[{table_name}] 검증 중...")

        table = get_table(api, table_name)
        all_records = table.all()
        total = len(all_records)

        logger.info(f"  전체 레코드: {total}")

        results[table_key] = {
            'total': total,
            'missing': {},
            'fixed': {}
        }

        # 각 필수 필드별로 검증
        for field_name, (default_value, description) in required_fields.items():
            records_to_update = []

            for record in all_records:
                field_value = record['fields'].get(field_name)
                # 값이 None이거나 빈 값인 경우 누락으로 판단
                if field_value is None or field_value == '' or field_value is False:
                    records_to_update.append({
                        'id': record['id'],
                        'fields': {field_name: default_value}
                    })

            missing_count = len(records_to_update)
            results[table_key]['missing'][field_name] = missing_count

            if missing_count == 0:
                logger.info(f"  ✓ {field_name}: 모두 정상")
            else:
                logger.warning(f"  ✗ {field_name}: {missing_count}개 누락 ({description})")

                if auto_fix and records_to_update:
                    # 배치 업데이트로 복구
                    fixed = 0
                    for batch in batch_iterator(records_to_update, AIRTABLE_BATCH_SIZE):
                        table.batch_update(batch)
                        fixed += len(batch)

                    results[table_key]['fixed'][field_name] = fixed
                    logger.info(f"    → {fixed}개 자동 복구 완료 (기본값: {default_value})")

    # 요약
    logger.info(f"\n{'='*60}")
    logger.info("검증 완료")
    logger.info("=" * 60)

    total_missing = sum(
        sum(table_result['missing'].values())
        for table_result in results.values()
    )
    total_fixed = sum(
        sum(table_result.get('fixed', {}).values())
        for table_result in results.values()
    )

    if total_missing == 0:
        logger.info("✓ 모든 필수 필드가 정상입니다.")
    else:
        logger.info(f"총 누락: {total_missing}개" + (f", 복구: {total_fixed}개" if auto_fix else ""))

    return results


def backfill_refunds_orders_link(api: Api = None) -> int:
    """기존 Refunds 레코드의 Orders Linked Record 복구

    Orders 필드가 비어있는 Refunds 레코드를 찾아
    Order Number로 매칭하여 Linked Record를 설정합니다.

    Args:
        api: Airtable API 클라이언트 (없으면 새로 생성)

    Returns:
        업데이트된 레코드 수
    """
    if api is None:
        api = get_api()

    logger.info(f"\n{'='*60}")
    logger.info("Refunds → Orders Linked Record 복구")
    logger.info("=" * 60)

    refunds_table = get_table(api, config.AIRTABLE_TABLES['refunds'])
    orders_table = get_table(api, config.AIRTABLE_TABLES['orders'])

    # Orders: Order Number -> record_id 매핑
    existing_orders = get_existing_orders(orders_table)
    logger.info(f"Orders: {len(existing_orders)}개")

    # Refunds 전체 조회
    all_refunds = refunds_table.all()
    logger.info(f"Refunds 전체: {len(all_refunds)}개")

    # Orders 필드가 비어있는 Refunds 필터링
    records_to_update = []
    missing_orders = []

    for record in all_refunds:
        # 이미 Orders가 연결되어 있으면 건너뛰기
        if record['fields'].get('Orders'):
            continue

        order_number = record['fields'].get('Order Number')
        if not order_number:
            continue

        order_id = existing_orders.get(order_number)
        if order_id:
            records_to_update.append({
                'id': record['id'],
                'fields': {'Orders': [order_id]}
            })
        else:
            missing_orders.append(order_number)

    logger.info(f"복구 대상: {len(records_to_update)}개")
    if missing_orders:
        logger.warning(f"Orders 테이블에 없는 주문: {len(missing_orders)}개")
        logger.warning(f"  예시: {missing_orders[:5]}")

    if not records_to_update:
        logger.info("복구할 레코드가 없습니다.")
        return 0

    # 배치 업데이트
    updated = 0
    for batch in batch_iterator(records_to_update, AIRTABLE_BATCH_SIZE):
        refunds_table.batch_update(batch)
        updated += len(batch)

    logger.info(f"복구 완료: {updated}개")
    return updated
