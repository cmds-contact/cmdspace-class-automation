"""설정 관리 모듈

환경변수 및 애플리케이션 설정을 중앙 관리.
"""

import os
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv


class TableConfig(TypedDict):
    """테이블 설정 타입"""
    file_pattern: str
    unique_key: str


# 프로젝트 루트 디렉토리
BASE_DIR: Path = Path(__file__).parent.parent

# 환경변수 로드
load_dotenv(BASE_DIR / '.env')

# Publ 인증 정보
PUBL_ID: str | None = os.getenv('PUBL_ID')
PUBL_PW: str | None = os.getenv('PUBL_PW')

# Airtable 인증 정보
AIRTABLE_API_KEY: str | None = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID: str | None = os.getenv('AIRTABLE_BASE_ID')

# Publ Channel ID (base64 encoded)
PUBL_CHANNEL_ID: str = os.getenv('PUBL_CHANNEL_ID', 'L2NoYW5uZWxzLzE3Njkx')

# 경로 설정
DOWNLOAD_DIR: Path = BASE_DIR / 'downloads'
ARCHIVE_DIR: Path = BASE_DIR / 'archive'
SESSION_FILE: Path = BASE_DIR / '.session.json'

# 브라우저 설정
HEADLESS: bool = True  # True: 브라우저 창 숨김, False: 브라우저 창 보임
DEFAULT_TIMEOUT: int = 30000  # 30초

# Publ 콘솔 URL
PUBL_LOGIN_URL: str = 'https://console.publ.biz/?type=enter'
PUBL_CHANNEL_BASE: str = f'https://console.publ.biz/channels/{PUBL_CHANNEL_ID}'
PUBL_MEMBERS_URL: str = f'{PUBL_CHANNEL_BASE}/members/registered-users'
PUBL_ORDERS_URL: str = f'{PUBL_CHANNEL_BASE}/orders/subs-products'
PUBL_REFUNDS_URL: str = f'{PUBL_CHANNEL_BASE}/orders/refunds'

# 테이블 설정 (CSV 파일 패턴 및 고유 키)
TABLES: dict[str, TableConfig] = {
    'members': {
        'file_pattern': '*_members.csv',
        'unique_key': 'Member Code'
    },
    'orders': {
        'file_pattern': '*_orders*.csv',
        'unique_key': 'Order Number'
    },
    'refunds': {
        'file_pattern': '*_refunds.csv',
        'unique_key': 'Order Number'
    }
}

# 처리 순서
PROCESSING_ORDER: list[str] = ['members', 'orders', 'refunds']

# 배치 크기
BATCH_SIZE: int = 100

# Airtable 테이블 설정
AIRTABLE_TABLES: dict[str, str] = {
    'members': 'Members',
    'orders': 'Orders',
    'refunds': 'Refunds',
    'products': 'Products',
    'member_products': 'MemberProducts',
    'sync_history': 'SyncHistory'
}


def validate_config() -> bool:
    """환경변수 검증

    Returns:
        True면 검증 성공

    Raises:
        ValueError: 필수 환경변수가 누락된 경우
    """
    errors: list[str] = []

    if not PUBL_ID:
        errors.append("PUBL_ID가 설정되지 않았습니다.")
    if not PUBL_PW:
        errors.append("PUBL_PW가 설정되지 않았습니다.")
    if not AIRTABLE_API_KEY:
        errors.append("AIRTABLE_API_KEY가 설정되지 않았습니다.")
    if not AIRTABLE_BASE_ID:
        errors.append("AIRTABLE_BASE_ID가 설정되지 않았습니다.")

    if errors:
        raise ValueError("\n".join(errors))

    return True


def ensure_directories() -> None:
    """필요한 디렉토리 생성"""
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    ARCHIVE_DIR.mkdir(exist_ok=True)
