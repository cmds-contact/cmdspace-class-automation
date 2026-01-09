"""validators 모듈 테스트"""

import pytest
from unittest.mock import MagicMock

from src.airtable.validators import check_csv_duplicates, check_airtable_duplicates


class TestCheckCsvDuplicates:
    """check_csv_duplicates 함수 테스트"""

    def test_finds_duplicates(self, sample_csv_data):
        """중복 키 발견"""
        result = check_csv_duplicates(sample_csv_data, 'Member Code')

        assert 'M001' in result
        assert result['M001'] == 2  # M001이 2번 등장
        assert 'M002' not in result  # M002는 1번만 등장

    def test_no_duplicates(self, sample_csv_data_no_duplicates):
        """중복 없음"""
        result = check_csv_duplicates(sample_csv_data_no_duplicates, 'Member Code')

        assert result == {}

    def test_empty_data(self):
        """빈 데이터"""
        result = check_csv_duplicates([], 'Member Code')

        assert result == {}

    def test_missing_key_field(self):
        """존재하지 않는 키 필드"""
        data = [{'Name': 'Test1'}, {'Name': 'Test2'}]
        result = check_csv_duplicates(data, 'Member Code')

        assert result == {}

    def test_none_values_ignored(self):
        """None 값 무시"""
        data = [
            {'Member Code': None, 'Name': 'Test1'},
            {'Member Code': 'M001', 'Name': 'Test2'},
            {'Member Code': 'M001', 'Name': 'Test3'},
        ]
        result = check_csv_duplicates(data, 'Member Code')

        assert 'M001' in result
        assert result['M001'] == 2


class TestCheckAirtableDuplicates:
    """check_airtable_duplicates 함수 테스트"""

    def test_finds_duplicates(self, mock_table, sample_airtable_records):
        """중복 키 발견"""
        mock_table.all.return_value = sample_airtable_records

        result = check_airtable_duplicates(mock_table, 'Member Code')

        assert 'M001' in result
        assert len(result['M001']) == 2  # rec1, rec3
        assert 'rec1' in result['M001']
        assert 'rec3' in result['M001']

    def test_no_duplicates(self, mock_table, sample_airtable_records_no_duplicates):
        """중복 없음"""
        mock_table.all.return_value = sample_airtable_records_no_duplicates

        result = check_airtable_duplicates(mock_table, 'Member Code')

        assert result == {}

    def test_empty_table(self, mock_table):
        """빈 테이블"""
        mock_table.all.return_value = []

        result = check_airtable_duplicates(mock_table, 'Member Code')

        assert result == {}

    def test_missing_key_field(self, mock_table):
        """키 필드가 없는 레코드"""
        records = [
            {'id': 'rec1', 'fields': {'Name': 'Test1'}},  # Member Code 없음
            {'id': 'rec2', 'fields': {'Member Code': 'M001', 'Name': 'Test2'}},
        ]
        mock_table.all.return_value = records

        result = check_airtable_duplicates(mock_table, 'Member Code')

        assert result == {}  # M001은 1번만 등장
