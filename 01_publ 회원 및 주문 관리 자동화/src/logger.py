"""로깅 설정 모듈

표준 logging 모듈을 사용하여 콘솔 + 파일 로깅 구현.
- 콘솔: INFO 이상
- 파일: DEBUG 이상 (logs/sync_YYYYMMDD.log)
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 디렉토리 (config.py와 동일한 방식)
BASE_DIR: Path = Path(__file__).parent.parent

# 로그 디렉토리
LOG_DIR: Path = BASE_DIR / 'logs'


def setup_logger(name: str = 'publ_data_manager') -> logging.Logger:
    """로거 설정 및 반환

    Args:
        name: 로거 이름

    Returns:
        설정된 Logger 객체
    """
    # 로그 디렉토리 생성
    LOG_DIR.mkdir(exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 이미 핸들러가 있으면 스킵 (중복 방지)
    if logger.handlers:
        return logger

    # 포맷터 설정
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 콘솔 핸들러 (INFO 이상)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (DEBUG 이상, 일별 로그)
    today = datetime.now().strftime('%Y%m%d')
    log_file = LOG_DIR / f'sync_{today}.log'
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# 전역 로거 인스턴스 (모든 모듈에서 import하여 사용)
logger = setup_logger()


def get_log_file_path() -> Path:
    """현재 로그 파일 경로 반환"""
    today = datetime.now().strftime('%Y%m%d')
    return LOG_DIR / f'sync_{today}.log'


def log_section(title: str, width: int = 50) -> None:
    """섹션 헤더 출력

    Args:
        title: 섹션 제목
        width: 구분선 너비 (기본값: 50)
    """
    logger.info("")
    logger.info("=" * width)
    logger.info(title)
    logger.info("=" * width)
