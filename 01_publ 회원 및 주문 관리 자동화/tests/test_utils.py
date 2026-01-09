"""utils 모듈 테스트"""

import pytest

from src.utils import (
    parse_price,
    safe_get,
    batch_iterator,
    to_iso_datetime,
    parse_iso_datetime,
)


class TestParsePrice:
    """parse_price 함수 테스트"""

    def test_removes_currency_symbol(self):
        """통화 기호 제거"""
        assert parse_price("1000원") == 1000
        assert parse_price("500원") == 500

    def test_handles_comma(self):
        """천단위 콤마 처리"""
        assert parse_price("1,000") == 1000
        assert parse_price("10,000원") == 10000
        assert parse_price("1,234,567") == 1234567

    def test_handles_integer(self):
        """정수 입력"""
        assert parse_price(1000) == 1000
        assert parse_price(0) == 0

    def test_handles_float(self):
        """실수 입력"""
        assert parse_price(1000.5) == 1000
        assert parse_price(999.9) == 999

    def test_handles_none(self):
        """None 입력"""
        assert parse_price(None) == 0

    def test_handles_empty_string(self):
        """빈 문자열"""
        assert parse_price("") == 0
        assert parse_price("   ") == 0

    def test_handles_plain_number_string(self):
        """숫자 문자열"""
        assert parse_price("500") == 500
        assert parse_price("12345") == 12345


class TestSafeGet:
    """safe_get 함수 테스트"""

    def test_returns_value_when_exists(self):
        """값이 존재할 때"""
        data = {'name': 'Test', 'value': 100}

        assert safe_get(data, 'name') == 'Test'
        assert safe_get(data, 'value') == 100

    def test_returns_default_when_none(self):
        """값이 None일 때 기본값 반환"""
        data = {'name': None}

        assert safe_get(data, 'name') == ''
        assert safe_get(data, 'name', 'default') == 'default'

    def test_returns_default_when_missing(self):
        """키가 없을 때 기본값 반환"""
        data = {'name': 'Test'}

        assert safe_get(data, 'missing') == ''
        assert safe_get(data, 'missing', 'default') == 'default'

    def test_preserves_falsy_values(self):
        """falsy 값 (0, '', False) 보존"""
        data = {'zero': 0, 'empty': '', 'false': False}

        assert safe_get(data, 'zero') == 0
        assert safe_get(data, 'empty') == ''
        assert safe_get(data, 'false') is False


class TestBatchIterator:
    """batch_iterator 함수 테스트"""

    def test_splits_into_batches(self):
        """배치로 분할"""
        items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        batches = list(batch_iterator(items, batch_size=3))

        assert len(batches) == 4
        assert batches[0] == [1, 2, 3]
        assert batches[1] == [4, 5, 6]
        assert batches[2] == [7, 8, 9]
        assert batches[3] == [10]

    def test_single_batch(self):
        """배치 크기보다 작을 때"""
        items = [1, 2, 3]

        batches = list(batch_iterator(items, batch_size=10))

        assert len(batches) == 1
        assert batches[0] == [1, 2, 3]

    def test_exact_batch_size(self):
        """정확히 배치 크기일 때"""
        items = [1, 2, 3, 4]

        batches = list(batch_iterator(items, batch_size=2))

        assert len(batches) == 2
        assert batches[0] == [1, 2]
        assert batches[1] == [3, 4]

    def test_empty_list(self):
        """빈 리스트"""
        batches = list(batch_iterator([], batch_size=10))

        assert batches == []


class TestToIsoDatetime:
    """to_iso_datetime 함수 테스트"""

    def test_converts_datetime_with_seconds(self):
        """초 포함 형식 변환"""
        result = to_iso_datetime("2024-12-27 15:30:45")

        assert result == "2024-12-27T15:30:45+09:00"

    def test_converts_datetime_without_seconds(self):
        """초 없는 형식 변환"""
        result = to_iso_datetime("2024-12-27 15:30")

        assert result == "2024-12-27T15:30:00+09:00"

    def test_returns_none_for_none(self):
        """None 입력"""
        assert to_iso_datetime(None) is None

    def test_returns_none_for_empty_string(self):
        """빈 문자열"""
        assert to_iso_datetime("") is None
        assert to_iso_datetime("   ") is None

    def test_returns_none_for_invalid_format(self):
        """잘못된 형식"""
        assert to_iso_datetime("2024/12/27") is None
        assert to_iso_datetime("invalid") is None

    def test_strips_whitespace(self):
        """공백 제거"""
        result = to_iso_datetime("  2024-12-27 15:30:45  ")

        assert result == "2024-12-27T15:30:45+09:00"


class TestParseIsoDatetime:
    """parse_iso_datetime 함수 테스트"""

    def test_parses_iso_with_timezone(self):
        """타임존 포함 ISO 형식 파싱"""
        from datetime import datetime

        result = parse_iso_datetime("2024-12-27T15:30:45+09:00")

        assert result == datetime(2024, 12, 27, 15, 30, 45)

    def test_parses_iso_with_z(self):
        """Z 타임존 파싱"""
        from datetime import datetime

        result = parse_iso_datetime("2024-12-27T15:30:45Z")

        assert result == datetime(2024, 12, 27, 15, 30, 45)

    def test_returns_none_for_none(self):
        """None 입력"""
        assert parse_iso_datetime(None) is None

    def test_returns_none_for_empty(self):
        """빈 문자열"""
        assert parse_iso_datetime("") is None

    def test_returns_none_for_invalid(self):
        """잘못된 형식"""
        assert parse_iso_datetime("invalid") is None
