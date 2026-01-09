"""records 모듈 테스트"""

import pytest
from unittest.mock import MagicMock

from src.airtable.records import (
    get_existing_by_key,
    get_existing_orders,
    get_existing_member_products,
    get_pending_refunds,
)


class TestGetExistingByKey:
    """get_existing_by_key 함수 테스트"""

    def test_returns_key_to_id_mapping(self, mock_table, sample_airtable_records_no_duplicates):
        """키 -> record_id 매핑 반환"""
        mock_table.all.return_value = sample_airtable_records_no_duplicates

        result = get_existing_by_key(mock_table, 'Member Code')

        assert result == {
            'M001': 'rec1',
            'M002': 'rec2',
        }

    def test_skips_empty_keys(self, mock_table):
        """빈 키 값 건너뛰기"""
        records = [
            {'id': 'rec1', 'fields': {'Member Code': 'M001'}},
            {'id': 'rec2', 'fields': {'Member Code': None}},  # None
            {'id': 'rec3', 'fields': {'Member Code': ''}},    # 빈 문자열
            {'id': 'rec4', 'fields': {'Name': 'Test'}},       # 키 필드 없음
        ]
        mock_table.all.return_value = records

        result = get_existing_by_key(mock_table, 'Member Code')

        # 빈 문자열('')은 falsy이므로 건너뜀
        assert result == {'M001': 'rec1'}

    def test_empty_table(self, mock_table):
        """빈 테이블"""
        mock_table.all.return_value = []

        result = get_existing_by_key(mock_table, 'Member Code')

        assert result == {}


class TestGetExistingOrders:
    """get_existing_orders 함수 테스트"""

    def test_uses_order_number_field(self, mock_table):
        """Order Number 필드 사용"""
        records = [
            {'id': 'rec1', 'fields': {'Order Number': 'ORD001'}},
            {'id': 'rec2', 'fields': {'Order Number': 'ORD002'}},
        ]
        mock_table.all.return_value = records

        result = get_existing_orders(mock_table)

        assert result == {
            'ORD001': 'rec1',
            'ORD002': 'rec2',
        }


class TestGetExistingMemberProducts:
    """get_existing_member_products 함수 테스트"""

    def test_uses_member_products_code_field(self, mock_table):
        """MemberProducts Code 필드 사용"""
        records = [
            {'id': 'rec1', 'fields': {'MemberProducts Code': 'M001_PROD1'}},
            {'id': 'rec2', 'fields': {'MemberProducts Code': 'M002_PROD2'}},
        ]
        mock_table.all.return_value = records

        result = get_existing_member_products(mock_table)

        assert result == {
            'M001_PROD1': 'rec1',
            'M002_PROD2': 'rec2',
        }


class TestGetPendingRefunds:
    """get_pending_refunds 함수 테스트"""

    def test_excludes_final_statuses(self, mock_table, sample_refund_records):
        """Refunded, Rejected 상태 제외"""
        mock_table.all.return_value = sample_refund_records

        result = get_pending_refunds(mock_table)

        # Pending, Processing만 포함 (Refunded, Rejected 제외)
        assert 'ORD001' in result  # Pending
        assert 'ORD003' in result  # Processing
        assert 'ORD002' not in result  # Refunded (제외)
        assert 'ORD004' not in result  # Rejected (제외)

    def test_returns_id_and_status(self, mock_table, sample_refund_records):
        """id와 status 반환"""
        mock_table.all.return_value = sample_refund_records

        result = get_pending_refunds(mock_table)

        assert result['ORD001'] == {'id': 'ref1', 'status': 'Pending'}
        assert result['ORD003'] == {'id': 'ref3', 'status': 'Processing'}

    def test_empty_table(self, mock_table):
        """빈 테이블"""
        mock_table.all.return_value = []

        result = get_pending_refunds(mock_table)

        assert result == {}

    def test_all_final_statuses(self, mock_table):
        """모두 최종 상태일 때"""
        records = [
            {'id': 'ref1', 'fields': {'Order Number': 'ORD001', 'Refund Status': 'Refunded'}},
            {'id': 'ref2', 'fields': {'Order Number': 'ORD002', 'Refund Status': 'Rejected'}},
        ]
        mock_table.all.return_value = records

        result = get_pending_refunds(mock_table)

        assert result == {}
