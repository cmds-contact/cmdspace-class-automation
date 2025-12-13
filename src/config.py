"""설정 관리 모듈"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리
BASE_DIR = Path(__file__).parent.parent

# 환경변수 로드
load_dotenv(BASE_DIR / '.env')

# Publ 인증 정보
PUBL_ID = os.getenv('PUBL_ID')
PUBL_PW = os.getenv('PUBL_PW')

# Supabase 인증 정보
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Publ Channel ID (base64 encoded)
PUBL_CHANNEL_ID = os.getenv('PUBL_CHANNEL_ID', 'L2NoYW5uZWxzLzE3Njkx')

# 경로 설정
DOWNLOAD_DIR = BASE_DIR / 'downloads'
ARCHIVE_DIR = BASE_DIR / 'archive'
SESSION_FILE = BASE_DIR / '.session.json'

# 브라우저 설정
HEADLESS = True  # False로 변경하면 브라우저 창이 보임
DEFAULT_TIMEOUT = 30000  # 30초

# Publ 콘솔 URL
PUBL_LOGIN_URL = 'https://console.publ.biz/?type=enter'
PUBL_CHANNEL_BASE = f'https://console.publ.biz/channels/{PUBL_CHANNEL_ID}'
PUBL_MEMBERS_URL = f'{PUBL_CHANNEL_BASE}/members/registered-users'
PUBL_ORDERS_URL = f'{PUBL_CHANNEL_BASE}/orders/subs-products'
PUBL_REFUNDS_URL = f'{PUBL_CHANNEL_BASE}/orders/refunds'

# Supabase 테이블 설정
TABLES = {
    'members': {
        'name': 'publ-member-db',
        'file_pattern': '*_members.csv',
        'unique_key': 'Member Code'
    },
    'orders': {
        'name': 'publ-order-db',
        'file_pattern': '*_orders_latest.csv',
        'unique_key': 'Order Number'
    },
    'refunds': {
        'name': 'publ-refund-db',
        'file_pattern': '*_refunds.csv',
        'unique_key': 'Order Number'
    }
}

# 처리 순서
PROCESSING_ORDER = ['members', 'orders', 'refunds']

# 배치 크기
BATCH_SIZE = 100


def validate_config():
    """환경변수 검증"""
    errors = []

    if not PUBL_ID:
        errors.append("PUBL_ID가 설정되지 않았습니다.")
    if not PUBL_PW:
        errors.append("PUBL_PW가 설정되지 않았습니다.")
    if not SUPABASE_URL:
        errors.append("SUPABASE_URL이 설정되지 않았습니다.")
    if not SUPABASE_KEY:
        errors.append("SUPABASE_KEY가 설정되지 않았습니다.")

    if errors:
        raise ValueError("\n".join(errors))

    return True


def ensure_directories():
    """필요한 디렉토리 생성"""
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    ARCHIVE_DIR.mkdir(exist_ok=True)
