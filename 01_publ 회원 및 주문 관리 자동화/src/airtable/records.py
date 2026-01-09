"""Airtable 레코드 조회 모듈

기존 레코드 조회 및 매핑 기능을 제공합니다.
"""

from typing import Any

from pyairtable import Table


def get_existing_by_key(table: Table, key_field: str) -> dict[str, str]:
    """Airtable 테이블에서 기존 레코드 조회 (범용)

    Args:
        table: Airtable 테이블 객체
        key_field: 고유 키 필드명

    Returns:
        key_value -> record_id 매핑 딕셔너리
    """
    return {
        record['fields'].get(key_field): record['id']
        for record in table.all()
        if record['fields'].get(key_field)
    }


def get_existing_orders(table: Table) -> dict[str, str]:
    """Airtable에서 기존 주문 레코드 조회

    Args:
        table: Airtable Orders 테이블 객체

    Returns:
        order_number -> record_id 매핑 딕셔너리
    """
    return get_existing_by_key(table, 'Order Number')


def get_existing_member_products(table: Table) -> dict[str, str]:
    """Airtable에서 기존 MemberProducts 레코드 조회

    Args:
        table: Airtable MemberProducts 테이블 객체

    Returns:
        MemberProducts Code -> record_id 매핑 딕셔너리
    """
    return get_existing_by_key(table, 'MemberProducts Code')


def get_pending_refunds(table: Table) -> dict[str, dict[str, Any]]:
    """Airtable에서 미결정 상태 환불 레코드 조회

    Refunded, Rejected가 아닌 환불만 조회 (상태 변경 추적용)

    Args:
        table: Airtable Refunds 테이블 객체

    Returns:
        order_number -> {id, status} 매핑 딕셔너리
    """
    final_statuses = {'Refunded', 'Rejected'}
    result = {}
    for record in table.all():
        order_number = record['fields'].get('Order Number')
        status = record['fields'].get('Refund Status')
        if order_number and status not in final_statuses:
            result[order_number] = {
                'id': record['id'],
                'status': status
            }
    return result
