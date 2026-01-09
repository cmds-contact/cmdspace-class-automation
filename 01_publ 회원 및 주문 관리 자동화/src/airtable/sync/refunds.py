"""환불(Refunds) 동기화 모듈

CSV 데이터를 Refunds 테이블로 동기화합니다.
신규 환불 추가 및 미결정 상태 환불의 상태 변경 추적을 포함합니다.
"""

from typing import Any

from pyairtable import Api

from ... import config
from ...logger import logger
from ...utils import parse_price, safe_get, batch_iterator, to_iso_datetime

from ..client import get_table
from ..csv_reader import read_csv, find_csv
from ..records import get_existing_by_key, get_existing_orders, get_pending_refunds

# Airtable 배치 크기 (API 제한)
AIRTABLE_BATCH_SIZE = 10


def _prepare_new_refunds(
    csv_data: list[dict[str, Any]],
    existing_refunds: dict[str, str],
    existing_orders: dict[str, str]
) -> list[dict[str, Any]]:
    """신규 환불 레코드 준비

    Args:
        csv_data: CSV 데이터 리스트
        existing_refunds: 기존 환불 레코드 (Order Number -> record_id)
        existing_orders: 기존 주문 레코드 (Order Number -> record_id)

    Returns:
        새로 추가할 레코드 리스트
    """
    new_records = []

    for row in csv_data:
        order_number = row.get('Order Number')
        if not order_number or order_number in existing_refunds:
            continue

        order_id = existing_orders.get(order_number)

        # Refund Request Date를 ISO dateTime으로 변환
        refund_date_str = safe_get(row, 'Refund Request Date')
        refund_datetime = to_iso_datetime(refund_date_str)

        record_fields = {
            'Order Number': order_number,
            'Refund Status': safe_get(row, 'Refund Status'),
            'Refund Request Price': parse_price(row.get('Refund Request Price')),
            'Username': safe_get(row, 'Username'),
            'Member Code': safe_get(row, 'Member Code'),
            'Refund Request Date': refund_date_str,  # 원본 텍스트
        }

        # Refund Request Date (ISO) - dateTime 형식
        if refund_datetime:
            record_fields['Refund Request Date (ISO)'] = refund_datetime

        # Orders Linked Record 추가
        if order_id:
            record_fields['Orders'] = [order_id]

        new_records.append(record_fields)

    return new_records


def _find_status_updates(
    pending_refunds: dict[str, dict[str, Any]],
    csv_by_order: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    """상태 변경 대상 찾기

    Args:
        pending_refunds: 미결정 상태 환불 (Order Number -> {id, status})
        csv_by_order: CSV 데이터 인덱스 (Order Number -> row)

    Returns:
        업데이트할 레코드 리스트 [{id, fields}]
    """
    updates = []

    for order_number, pending_data in pending_refunds.items():
        csv_row = csv_by_order.get(order_number)
        if not csv_row:
            continue

        csv_status = csv_row.get('Refund Status')
        airtable_status = pending_data['status']

        # 상태가 변경되었으면 업데이트 대상에 추가
        if csv_status and csv_status != airtable_status:
            updates.append({
                'id': pending_data['id'],
                'fields': {'Refund Status': csv_status}
            })

    return updates


def sync_refunds(api: Api) -> tuple[int, int]:
    """환불 데이터를 CSV에서 읽어 Airtable로 동기화

    - 신규 환불 추가 (Orders Linked Record 포함)
    - 미결정 상태 환불의 상태 변경 추적 및 업데이트

    Args:
        api: Airtable API 클라이언트

    Returns:
        (삽입된 수, 업데이트된 수) 튜플
    """
    table_config = config.TABLES['refunds']
    file_path = find_csv(table_config['file_pattern'])
    refunds_table = get_table(api, config.AIRTABLE_TABLES['refunds'])
    orders_table = get_table(api, config.AIRTABLE_TABLES['orders'])

    logger.info(f"\n{'='*50}")
    logger.info(f"Airtable 환불 동기화: {file_path.split('/')[-1]}")
    logger.info(f"{'='*50}")

    csv_data = read_csv(file_path)
    logger.info(f"CSV 레코드: {len(csv_data)}")

    # 기존 환불 조회
    existing_refunds = get_existing_by_key(refunds_table, 'Order Number')
    existing_orders = get_existing_orders(orders_table)

    # 미결정 상태 환불만 조회 (상태 변경 추적용)
    pending_refunds = get_pending_refunds(refunds_table)

    logger.info(f"Airtable 기존 환불: {len(existing_refunds)}")
    logger.info(f"미결정 상태 환불: {len(pending_refunds)}")

    # CSV를 Order Number로 인덱싱 (빠른 조회용)
    csv_by_order = {
        row.get('Order Number'): row
        for row in csv_data
        if row.get('Order Number')
    }

    # 1. 신규 환불 준비
    new_records = _prepare_new_refunds(csv_data, existing_refunds, existing_orders)

    # 2. 상태 변경 대상 찾기
    refunds_to_update = _find_status_updates(pending_refunds, csv_by_order)

    logger.info(f"새 환불 레코드: {len(new_records)}")
    logger.info(f"상태 업데이트 대상: {len(refunds_to_update)}")

    # 환불 레코드 삽입
    inserted = 0
    failed_records: list[dict[str, Any]] = []

    if new_records:
        for batch in batch_iterator(new_records, AIRTABLE_BATCH_SIZE):
            try:
                refunds_table.batch_create(batch)
                inserted += len(batch)
            except Exception as e:
                error_msg = str(e)
                # Single Select 옵션 누락 에러 처리
                if 'INVALID_MULTIPLE_CHOICE_OPTIONS' in error_msg:
                    logger.warning("Airtable 'Refund Status' 필드에 새 옵션 추가 필요!")
                    # 실패한 레코드들의 상태값 수집
                    statuses = set(r.get('Refund Status', '') for r in batch)
                    logger.info(f"   누락된 옵션: {statuses}")
                    logger.info("   해결 방법: Airtable에서 Refunds 테이블의 'Refund Status' 필드에")
                    logger.info(f"   '{', '.join(statuses)}' 옵션을 수동으로 추가하세요.")
                    failed_records.extend(batch)
                else:
                    raise

        if inserted > 0:
            logger.info(f"환불 삽입 완료: {inserted}개")
        if failed_records:
            logger.info(f"환불 삽입 실패: {len(failed_records)}개 (상태 옵션 누락)")

    # 환불 상태 업데이트
    updated = 0
    if refunds_to_update:
        for batch in batch_iterator(refunds_to_update, AIRTABLE_BATCH_SIZE):
            try:
                refunds_table.batch_update(batch)
                updated += len(batch)
            except Exception as e:
                error_msg = str(e)
                if 'INVALID_MULTIPLE_CHOICE_OPTIONS' in error_msg:
                    logger.warning("환불 상태 업데이트 실패: 상태 옵션 누락")
                else:
                    raise
        if updated > 0:
            logger.info(f"환불 상태 업데이트 완료: {updated}개")

    return inserted, updated
