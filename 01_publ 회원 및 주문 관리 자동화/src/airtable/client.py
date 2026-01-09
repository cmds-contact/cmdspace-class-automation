"""Airtable API 클라이언트

Airtable API 연결 및 테이블 접근을 담당합니다.
"""

from pyairtable import Api, Table

from .. import config


def get_api() -> Api:
    """Airtable API 클라이언트 생성

    Returns:
        Airtable API 클라이언트 인스턴스
    """
    return Api(config.AIRTABLE_API_KEY)


def get_table(api: Api, table_name: str) -> Table:
    """Airtable 테이블 객체 가져오기

    Args:
        api: Airtable API 클라이언트
        table_name: 테이블 이름

    Returns:
        Airtable 테이블 객체
    """
    return api.table(config.AIRTABLE_BASE_ID, table_name)
