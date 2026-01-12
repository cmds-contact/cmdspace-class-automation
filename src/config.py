"""설정 관리 모듈

환경변수 및 애플리케이션 설정을 중앙 관리.
- 민감 정보: .env 파일 (API 키, 비밀번호)
- 운영 설정: settings.yaml 파일 (배치 크기, 타임존 등)
"""

import os
from pathlib import Path
from typing import TypedDict

import yaml
from dotenv import load_dotenv


class TableConfig(TypedDict):
    """테이블 설정 타입"""
    file_pattern: str
    unique_key: str


# 프로젝트 루트 디렉토리
BASE_DIR: Path = Path(__file__).parent.parent

# 환경변수 로드
load_dotenv(BASE_DIR / '.env')

# 설정 파일 경로
SETTINGS_FILE: Path = BASE_DIR / 'settings.yaml'


def load_settings() -> dict:
    """외부 설정 파일 로드

    Returns:
        설정 딕셔너리. 파일이 없거나 오류 시 빈 딕셔너리 반환.
    """
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}
    return {}


# 설정 파일 로드 (한 번만 실행)
_settings: dict = load_settings()

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

# 브라우저 설정 (settings.yaml에서 로드, 기본값 제공)
HEADLESS: bool = _settings.get('browser', {}).get('headless', True)
DEFAULT_TIMEOUT: int = _settings.get('browser', {}).get('timeout_seconds', 30) * 1000

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

# 동기화 설정 (settings.yaml에서 로드, 기본값 제공)
BATCH_SIZE: int = _settings.get('sync', {}).get('batch_size', 100)
TIMEZONE: str = _settings.get('sync', {}).get('timezone', '+09:00')

# Airtable 테이블 설정 (settings.yaml에서 로드, 기본값 제공)
_default_tables: dict[str, str] = {
    'members': 'Members',
    'orders': 'Orders',
    'refunds': 'Refunds',
    'products': 'Products',
    'member_products': 'MemberProducts',
    'sync_history': 'SyncHistory'
}
AIRTABLE_TABLES: dict[str, str] = {
    **_default_tables,
    **_settings.get('airtable_tables', {})
}

# 테스트 데이터 필터링 패턴 (settings.yaml에서 로드, 기본값 제공)
_default_test_patterns: dict[str, list[str]] = {
    'name_keywords': ['테스트', 'test', 'TEST', '임시', 'temp', 'demo'],
    'email_domains': ['test.com', 'example.com', 'temp.com', 'fake.com']
}
TEST_PATTERNS: dict[str, list[str]] = {
    **_default_test_patterns,
    **_settings.get('test_patterns', {})
}

# 테이블별 필수 필드 정의 (동기화 후 자동 검증용)
# 필드명: (기본값, 설명)
# 참고: Is Active는 탈퇴 회원 관리를 위해 자동 복구에서 제외
#       신규 회원은 sync_members()에서 Is Active = True로 생성됨
REQUIRED_FIELDS: dict[str, dict[str, tuple]] = {
    'members': {
        # Is Active는 의도적으로 False일 수 있으므로 여기서 관리하지 않음
    },
    # 필요시 다른 테이블 추가 가능
    # 'orders': {
    #     'Status': ('Pending', '주문 상태'),
    # },
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
