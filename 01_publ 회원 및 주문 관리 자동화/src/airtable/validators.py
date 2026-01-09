"""데이터 유효성 검사 모듈

Airtable 및 CSV 데이터의 중복 검사 기능을 제공합니다.
"""

from collections import Counter, defaultdict
from typing import Any

from pyairtable import Table


def check_airtable_duplicates(table: Table, key_field: str) -> dict[str, list[str]]:
    """Airtable 테이블에서 중복 키 검사

    Args:
        table: Airtable 테이블 객체
        key_field: 고유 키 필드명

    Returns:
        key_value -> [record_id1, record_id2, ...] (2개 이상인 것만)
    """
    key_records: dict[str, list[str]] = defaultdict(list)

    for record in table.all():
        key_value = record['fields'].get(key_field)
        if key_value:
            key_records[key_value].append(record['id'])

    return {
        key: ids
        for key, ids in key_records.items()
        if len(ids) > 1
    }


def check_csv_duplicates(csv_data: list[dict[str, Any]], key_field: str) -> dict[str, int]:
    """CSV 데이터에서 중복 키 검사

    Args:
        csv_data: CSV 레코드 리스트
        key_field: 고유 키 필드명

    Returns:
        key_value -> 출현 횟수 (2회 이상인 것만)
    """
    keys = [row.get(key_field) for row in csv_data if row.get(key_field)]
    counter = Counter(keys)

    return {
        key: count
        for key, count in counter.items()
        if count > 1
    }
