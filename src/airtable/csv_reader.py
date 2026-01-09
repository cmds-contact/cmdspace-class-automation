"""CSV 파일 읽기 모듈

publ.biz에서 다운로드한 CSV 파일을 읽고 처리합니다.
"""

import csv
import glob
from typing import Any

from .. import config


def read_csv(file_path: str) -> list[dict[str, Any]]:
    """CSV 파일 읽기 (UTF-8 BOM 인코딩)

    Args:
        file_path: CSV 파일 경로

    Returns:
        레코드 딕셔너리 리스트
    """
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        return list(reader)


def find_csv(pattern: str) -> str:
    """패턴에 맞는 CSV 파일 찾기

    downloads 디렉토리에서 패턴에 맞는 가장 최근 파일을 찾습니다.

    Args:
        pattern: glob 패턴 (예: '*_members.csv')

    Returns:
        가장 최근 파일 경로

    Raises:
        FileNotFoundError: 패턴에 맞는 파일이 없을 때
    """
    files = glob.glob(str(config.DOWNLOAD_DIR / pattern))
    if not files:
        raise FileNotFoundError(f"패턴에 맞는 파일 없음: {pattern}")
    return sorted(files)[-1]
