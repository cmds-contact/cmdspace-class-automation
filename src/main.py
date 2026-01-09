"""publ-data-manager 메인 실행 스크립트

워크플로우:
1. publ.biz에서 데이터 다운로드 (회원, 주문, 환불)
2. 다운로드한 CSV 데이터를 Airtable에 동기화
3. 처리 완료된 CSV 파일 아카이브
4. 동기화 히스토리 기록 (SyncHistory 테이블)

초기화 모드:
--init-orders 옵션으로 주문 전체 페이지 다운로드
"""

import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from . import config
from .downloader import download_all, download_orders_all_pages, get_timestamp, login
from .airtable_syncer import sync_all_to_airtable, record_sync_history
from .logger import logger


def archive_files() -> int:
    """다운로드 폴더의 CSV 파일을 아카이브로 이동

    Returns:
        이동된 파일 수
    """
    csv_files = list(config.DOWNLOAD_DIR.glob('*.csv'))
    if not csv_files:
        return 0

    # 오늘 날짜 폴더 생성
    today = datetime.now().strftime("%Y%m%d")
    archive_subdir = config.ARCHIVE_DIR / today
    archive_subdir.mkdir(exist_ok=True)

    moved = 0
    for csv_file in csv_files:
        dest = archive_subdir / csv_file.name
        # 동일 파일명 존재 시 덮어쓰기 방지
        if dest.exists():
            timestamp = datetime.now().strftime("%H%M%S")
            dest = archive_subdir / f"{csv_file.stem}_{timestamp}{csv_file.suffix}"
        shutil.move(str(csv_file), str(dest))
        moved += 1

    return moved


def print_summary(
    download_files: dict[str, Path],
    airtable_results: dict[str, Any],
    archived_count: int
) -> None:
    """실행 결과 요약 출력

    Args:
        download_files: 다운로드된 파일 경로 딕셔너리
        airtable_results: Airtable 동기화 결과
        archived_count: 아카이브된 파일 수
    """
    logger.info("")
    logger.info("=" * 60)
    logger.info("실행 결과 요약")
    logger.info("=" * 60)

    # 다운로드 결과
    logger.info("")
    logger.info("[다운로드]")
    for data_type, file_path in download_files.items():
        filename = Path(file_path).name if file_path else "실패"
        logger.info(f"  {data_type}: {filename}")

    # Airtable 동기화 결과
    logger.info("")
    logger.info("[Airtable 동기화]")
    if 'error' in airtable_results:
        logger.error(f"  오류: {airtable_results['error']}")
    else:
        # 출력 순서 지정
        display_order = ['members', 'orders', 'products', 'member_products', 'refunds']
        for data_type in display_order:
            result = airtable_results.get(data_type)
            if isinstance(result, dict):
                if 'error' in result:
                    logger.error(f"  {data_type.upper()}: 오류 - {result['error']}")
                elif 'updated' in result:
                    logger.info(f"  {data_type.upper()}: {result['new']}개 신규, {result['updated']}개 업데이트")
                else:
                    logger.info(f"  {data_type.upper()}: {result['new']}개 신규")

    # 아카이브 결과
    logger.info("")
    logger.info("[아카이브]")
    logger.info(f"  {archived_count}개 파일 이동")


def main() -> None:
    """메인 실행 함수"""
    start_time = datetime.now()

    logger.info("")
    logger.info("=" * 60)
    logger.info("PUBL DATA MANAGER")
    logger.info(f"시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # 환경변수 검증
    try:
        config.validate_config()
    except ValueError as e:
        logger.error(f"설정 오류:\n{e}")
        logger.error(".env 파일을 확인해주세요.")
        return

    # 디렉토리 생성
    config.ensure_directories()

    # 1. 데이터 다운로드
    logger.info("")
    logger.info("#" * 60)
    logger.info("# STEP 1: 데이터 다운로드")
    logger.info("#" * 60)

    try:
        download_files = download_all()
    except Exception as e:
        logger.error(f"다운로드 오류: {e}")
        return

    # 2. Airtable 동기화
    logger.info("")
    logger.info("#" * 60)
    logger.info("# STEP 2: Airtable 동기화")
    logger.info("#" * 60)

    airtable_results: dict[str, Any] = {}
    try:
        airtable_results = sync_all_to_airtable()
    except Exception as e:
        logger.error(f"Airtable 동기화 오류: {e}")
        airtable_results = {'error': str(e)}

    # 3. 파일 아카이브
    logger.info("")
    logger.info("#" * 60)
    logger.info("# STEP 3: 파일 아카이브")
    logger.info("#" * 60)

    archived_count = archive_files()
    logger.info(f"{archived_count}개 파일을 archive 폴더로 이동")

    # 결과 요약
    print_summary(download_files, airtable_results, archived_count)

    # 완료
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    logger.info("")
    logger.info("=" * 60)
    logger.info(f"완료 시간: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"소요 시간: {duration:.1f}초")
    logger.info("=" * 60)

    # 4. 동기화 히스토리 기록
    logger.info("")
    logger.info("#" * 60)
    logger.info("# STEP 4: 히스토리 기록")
    logger.info("#" * 60)

    # 다운로드 파일명 목록 생성
    downloaded_files_list = [
        Path(fp).name for fp in download_files.values() if fp
    ]
    downloaded_files_str = ', '.join(downloaded_files_list)

    # 동기화 결과에서 값 추출
    has_error = 'error' in airtable_results
    status = 'Failed' if has_error else 'Success'

    members_new = airtable_results.get('members', {}).get('new', 0) if not has_error else 0
    orders_new = airtable_results.get('orders', {}).get('new', 0) if not has_error else 0
    refunds_new = airtable_results.get('refunds', {}).get('new', 0) if not has_error else 0
    refunds_updated = airtable_results.get('refunds', {}).get('updated', 0) if not has_error else 0

    record_sync_history(
        sync_date=start_time.strftime('%Y-%m-%d %H:%M:%S'),
        duration=duration,
        status=status,
        members_new=members_new,
        orders_new=orders_new,
        refunds_new=refunds_new,
        refunds_updated=refunds_updated,
        downloaded_files=downloaded_files_str
    )


def run_init_orders() -> None:
    """주문 전체 페이지 다운로드 (초기화용)"""
    from playwright.sync_api import sync_playwright

    logger.info("")
    logger.info("=" * 60)
    logger.info("주문 전체 페이지 다운로드 (초기화)")
    logger.info("=" * 60)

    # 환경변수 검증
    try:
        config.validate_config()
    except ValueError as e:
        logger.error(f"설정 오류:\n{e}")
        logger.error(".env 파일을 확인해주세요.")
        return

    config.ensure_directories()
    timestamp = get_timestamp()
    context = None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=config.HEADLESS)

            try:
                context, page = login(browser)
                orders_file = download_orders_all_pages(page, timestamp)
                logger.info(f"다운로드 완료: {orders_file}")

            finally:
                if context:
                    context.close()
                browser.close()

    except Exception as e:
        logger.error(f"오류: {e}")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--init-orders':
            run_init_orders()
        else:
            logger.warning(f"알 수 없는 옵션: {sys.argv[1]}")
            logger.info("사용법:")
            logger.info("  python -m src.main              # 일반 동기화")
            logger.info("  python -m src.main --init-orders # 주문 전체 페이지 다운로드")
    else:
        main()
