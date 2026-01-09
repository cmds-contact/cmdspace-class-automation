"""공통 테스트 fixtures"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_table():
    """Mock Airtable Table object"""
    table = MagicMock()
    return table


@pytest.fixture
def sample_csv_data():
    """샘플 CSV 데이터 (중복 포함)"""
    return [
        {'Member Code': 'M001', 'Name': 'Test1'},
        {'Member Code': 'M002', 'Name': 'Test2'},
        {'Member Code': 'M001', 'Name': 'Test1-dup'},  # M001 중복
        {'Member Code': 'M003', 'Name': 'Test3'},
    ]


@pytest.fixture
def sample_csv_data_no_duplicates():
    """샘플 CSV 데이터 (중복 없음)"""
    return [
        {'Member Code': 'M001', 'Name': 'Test1'},
        {'Member Code': 'M002', 'Name': 'Test2'},
        {'Member Code': 'M003', 'Name': 'Test3'},
    ]


@pytest.fixture
def sample_airtable_records():
    """샘플 Airtable 레코드 (중복 포함)"""
    return [
        {'id': 'rec1', 'fields': {'Member Code': 'M001', 'Name': 'Test1'}},
        {'id': 'rec2', 'fields': {'Member Code': 'M002', 'Name': 'Test2'}},
        {'id': 'rec3', 'fields': {'Member Code': 'M001', 'Name': 'Test1-dup'}},  # M001 중복
    ]


@pytest.fixture
def sample_airtable_records_no_duplicates():
    """샘플 Airtable 레코드 (중복 없음)"""
    return [
        {'id': 'rec1', 'fields': {'Member Code': 'M001', 'Name': 'Test1'}},
        {'id': 'rec2', 'fields': {'Member Code': 'M002', 'Name': 'Test2'}},
    ]


@pytest.fixture
def sample_refund_records():
    """샘플 환불 레코드 (상태별)"""
    return [
        {'id': 'ref1', 'fields': {'Order Number': 'ORD001', 'Refund Status': 'Pending'}},
        {'id': 'ref2', 'fields': {'Order Number': 'ORD002', 'Refund Status': 'Refunded'}},  # 완료
        {'id': 'ref3', 'fields': {'Order Number': 'ORD003', 'Refund Status': 'Processing'}},
        {'id': 'ref4', 'fields': {'Order Number': 'ORD004', 'Refund Status': 'Rejected'}},  # 거부
    ]
