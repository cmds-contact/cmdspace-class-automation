"""Airtable 동기화 히스토리 모듈

동기화 히스토리 기록 기능을 제공합니다.
"""

from datetime import datetime

from .. import config
from ..logger import logger

from .client import get_api, get_table


def record_sync_history(
    sync_date: str,
    duration: float,
    status: str,
    members_new: int = 0,
    orders_new: int = 0,
    refunds_new: int = 0,
    refunds_updated: int = 0,
    downloaded_files: str = ''
) -> bool:
    """동기화 히스토리를 Airtable에 기록

    Args:
        sync_date: 동기화 실행 시간 (YYYY-MM-DD HH:MM:SS 형식)
        duration: 소요 시간 (초)
        status: 상태 (Success/Failed)
        members_new: 신규 회원 수
        orders_new: 신규 주문 수
        refunds_new: 신규 환불 수
        refunds_updated: 업데이트된 환불 수
        downloaded_files: 다운로드된 파일명 목록

    Returns:
        True면 기록 성공
    """
    logger.info(f"\n{'='*50}")
    logger.info("동기화 히스토리 기록")
    logger.info(f"{'='*50}")

    try:
        api = get_api()
        table = get_table(api, config.AIRTABLE_TABLES['sync_history'])

        # sync_date를 ISO 8601 형식으로 변환 (Airtable dateTime 필드용)
        # 입력: "2024-12-27 15:30:45" (KST) -> 출력: "2024-12-27T15:30:45+09:00"
        dt = datetime.strptime(sync_date, '%Y-%m-%d %H:%M:%S')
        iso_datetime = dt.strftime('%Y-%m-%dT%H:%M:%S') + config.TIMEZONE

        record = {
            'Sync DateTime': iso_datetime,
            'Duration (sec)': round(duration, 1),
            'Status': status,
            'Members New': members_new,
            'Orders New': orders_new,
            'Refunds New': refunds_new,
            'Refunds Updated': refunds_updated,
            'Downloaded Files': downloaded_files,
        }

        table.create(record)
        logger.info(f"히스토리 기록 완료: {status}")
        return True

    except Exception as e:
        logger.error(f"히스토리 기록 실패: {e}")
        return False
