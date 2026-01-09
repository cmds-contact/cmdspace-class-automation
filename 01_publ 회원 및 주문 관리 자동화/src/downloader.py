"""publ.biz 데이터 다운로드 모듈

Playwright를 사용하여 publ.biz 콘솔에서 데이터를 자동으로 다운로드.
- 회원 목록 (members)
- 주문 목록 (orders)
- 환불 목록 (refunds)
"""

import csv
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Download, Route

from . import config
from .logger import logger, log_section


class Timeouts:
    """Playwright 타임아웃 상수 (밀리초)"""
    SESSION_CHECK = 3000      # 세션 확인 대기
    PAGE_LOAD = 2000          # 페이지 로딩 대기
    PAGE_NAVIGATE = 1500      # 페이지 전환 대기
    LOGIN_COMPLETE = 30000    # 로그인 완료 대기
    DOWNLOAD_WAIT = 5000      # 다운로드 대기


def get_timestamp() -> str:
    """타임스탬프 생성 (YYMMDD_HHMMSS)"""
    return datetime.now().strftime("%y%m%d_%H%M%S")


def save_download(download: Download, filename: str) -> Path:
    """다운로드 파일 저장

    Args:
        download: Playwright Download 객체
        filename: 저장할 파일명

    Returns:
        저장된 파일 경로
    """
    download_path = config.DOWNLOAD_DIR / filename
    download.save_as(str(download_path))
    logger.debug(f"저장 완료: {filename}")
    return download_path


def block_resources(route: Route) -> None:
    """불필요한 리소스 차단 (이미지, 폰트, 미디어)

    Args:
        route: Playwright Route 객체
    """
    if route.request.resource_type in ['image', 'font', 'media']:
        route.abort()
    else:
        route.continue_()


def is_session_valid(context: BrowserContext) -> bool:
    """저장된 세션이 유효한지 확인

    Args:
        context: 브라우저 컨텍스트

    Returns:
        True면 세션 유효
    """
    page = None
    try:
        page = context.new_page()
        page.goto('https://console.publ.biz/all-channels')
        page.wait_for_timeout(Timeouts.SESSION_CHECK)
        current_url = page.url
        # 로그인 페이지로 리다이렉트되거나 메인 페이지에 머물면 세션 무효
        if 'type=enter' in current_url:
            return False
        if current_url.rstrip('/') == 'https://console.publ.biz':
            return False
        # all-channels 페이지에 정상적으로 접근했는지 확인
        return 'all-channels' in current_url
    except Exception:
        return False
    finally:
        if page:
            page.close()


def login(browser: Browser) -> tuple[BrowserContext, Page]:
    """로그인 처리 및 컨텍스트 반환

    Args:
        browser: Playwright 브라우저 인스턴스

    Returns:
        (컨텍스트, 페이지) 튜플
    """
    log_section("1. 로그인")

    session_file = str(config.SESSION_FILE)

    # 저장된 세션이 있으면 로드 시도
    if os.path.exists(session_file):
        logger.debug("저장된 세션 확인 중...")
        context = browser.new_context(
            storage_state=session_file,
            accept_downloads=True
        )
        context.set_default_timeout(config.DEFAULT_TIMEOUT)
        context.route("**/*", block_resources)

        if is_session_valid(context):
            logger.info("저장된 세션 사용!")
            page = context.new_page()
            return context, page
        else:
            logger.info("세션 만료, 다시 로그인...")
            context.close()

    # 새로 로그인
    context = browser.new_context(accept_downloads=True)
    context.set_default_timeout(config.DEFAULT_TIMEOUT)
    context.route("**/*", block_resources)

    page = context.new_page()
    page.goto(config.PUBL_LOGIN_URL)

    # 로그인 폼 대기
    page.get_by_role('textbox', name='E-mail').wait_for(state='visible')

    page.get_by_role('textbox', name='E-mail').fill(config.PUBL_ID)
    page.get_by_role('textbox', name='Password').fill(config.PUBL_PW)
    page.get_by_role("button", name="Login", exact=True).click()

    # 로그인 완료 대기
    page.wait_for_url('**/all-channels**', timeout=Timeouts.LOGIN_COMPLETE)

    # 세션 저장
    context.storage_state(path=session_file)
    logger.info("로그인 완료! (세션 저장됨)")

    return context, page


def download_members(page: Page, timestamp: str) -> Path:
    """회원 목록 다운로드

    Args:
        page: Playwright Page 객체
        timestamp: 파일명에 사용할 타임스탬프

    Returns:
        다운로드된 파일 경로
    """
    log_section("2. 회원 목록 다운로드")

    page.goto(config.PUBL_MEMBERS_URL)

    # 다운로드 버튼 대기
    download_btn = page.get_by_role("button", name="All Member download(CSV)")
    download_btn.wait_for(state="visible")

    with page.expect_download() as download_info:
        download_btn.click()

    download = download_info.value
    return save_download(download, f"{timestamp}_members.csv")


def get_total_pages(page: Page) -> int:
    """페이지네이션에서 총 페이지 수 추출

    페이지 텍스트에서 "현재/총" 패턴 (예: 1/10)을 찾아 총 페이지 수 반환

    Args:
        page: Playwright Page 객체

    Returns:
        총 페이지 수 (찾지 못하면 1)
    """
    try:
        text = page.inner_text('body')
        matches = re.findall(r'(\d+)\s*/\s*(\d+)', text)
        if matches:
            # 가장 큰 두 번째 숫자를 총 페이지로 사용
            total = max(int(m[1]) for m in matches)
            return total
    except Exception:
        pass
    return 1


def download_orders(page: Page, timestamp: str) -> Path:
    """주문 목록 (최신 1페이지) 다운로드

    Args:
        page: Playwright Page 객체
        timestamp: 파일명에 사용할 타임스탬프

    Returns:
        다운로드된 파일 경로
    """
    log_section("3. 주문 목록 (Latest) 다운로드")

    page.goto(config.PUBL_ORDERS_URL)

    # 다운로드 버튼 대기 (SVG 아이콘 기반)
    download_btn = page.locator('svg path[d*="20.1835,14.7857"]').locator('xpath=ancestor::button')
    download_btn.wait_for(state="visible")

    with page.expect_download() as download_info:
        download_btn.click()

    download = download_info.value
    return save_download(download, f"{timestamp}_orders_latest.csv")


def download_orders_all_pages(page: Page, timestamp: str) -> Path:
    """주문 목록 전체 페이지 다운로드 및 병합

    모든 페이지의 CSV를 다운로드하여 하나의 파일로 병합

    Args:
        page: Playwright Page 객체
        timestamp: 파일명에 사용할 타임스탬프

    Returns:
        병합된 CSV 파일 경로
    """
    log_section("3. 주문 목록 (전체 페이지) 다운로드")

    # 첫 페이지로 이동하여 총 페이지 수 확인
    page.goto(config.PUBL_ORDERS_URL)
    page.wait_for_timeout(Timeouts.PAGE_LOAD)

    total_pages = get_total_pages(page)
    logger.info(f"총 페이지: {total_pages}")

    downloaded_files: list[Path] = []

    for page_num in range(1, total_pages + 1):
        logger.debug(f"페이지 {page_num}/{total_pages} 다운로드 중...")

        # 페이지 이동
        page_url = f"{config.PUBL_ORDERS_URL}?page={page_num}"
        page.goto(page_url)
        page.wait_for_timeout(Timeouts.PAGE_NAVIGATE)

        # 다운로드 버튼 클릭
        download_btn = page.locator('svg path[d*="20.1835,14.7857"]').locator('xpath=ancestor::button')
        download_btn.wait_for(state="visible")

        with page.expect_download() as download_info:
            download_btn.click()

        download = download_info.value
        file_path = config.DOWNLOAD_DIR / f"{timestamp}_orders_page{page_num}.csv"
        download.save_as(str(file_path))
        downloaded_files.append(file_path)

    # CSV 병합
    logger.debug(f"{len(downloaded_files)}개 파일 병합 중...")

    merged_path = config.DOWNLOAD_DIR / f"{timestamp}_orders_all.csv"
    all_rows: list[dict] = []
    header: list[str] = []

    for i, file_path in enumerate(downloaded_files):
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            if i == 0:
                header = reader.fieldnames or []
            for row in reader:
                all_rows.append(row)

    # Number 필드 재정렬 (1부터 순차)
    for i, row in enumerate(all_rows, 1):
        row['Number'] = str(i)

    # 병합 파일 저장
    with open(merged_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(all_rows)

    # 개별 페이지 파일 정리 (.trash로 이동)
    trash_dir = config.BASE_DIR / '.trash'
    trash_dir.mkdir(exist_ok=True)
    for file_path in downloaded_files:
        shutil.move(str(file_path), str(trash_dir / file_path.name))

    logger.info(f"병합 완료: {len(all_rows)}개 레코드")
    logger.info(f"저장 완료: {merged_path.name}")

    return merged_path


def download_refunds(page: Page, timestamp: str) -> Path:
    """환불 목록 다운로드

    Args:
        page: Playwright Page 객체
        timestamp: 파일명에 사용할 타임스탬프

    Returns:
        다운로드된 파일 경로
    """
    log_section("4. 환불 목록 다운로드")

    page.goto(config.PUBL_REFUNDS_URL)

    # 다운로드 버튼 대기 (SVG 아이콘 기반)
    download_btn = page.locator('svg path[d*="20.1835,14.7857"]').locator('xpath=ancestor::button')
    download_btn.wait_for(state="visible")

    with page.expect_download() as download_info:
        download_btn.click()

    download = download_info.value
    return save_download(download, f"{timestamp}_refunds.csv")


def download_all() -> dict[str, Path]:
    """전체 데이터 다운로드

    Returns:
        데이터 타입별 다운로드된 파일 경로 딕셔너리
    """
    config.ensure_directories()
    timestamp = get_timestamp()
    downloaded_files: dict[str, Path] = {}
    context = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.HEADLESS)

        try:
            context, page = login(browser)

            # 데이터 다운로드
            downloaded_files['members'] = download_members(page, timestamp)
            downloaded_files['orders'] = download_orders(page, timestamp)
            downloaded_files['refunds'] = download_refunds(page, timestamp)

            log_section("다운로드 완료!")

        finally:
            if context:
                context.close()
            browser.close()

    return downloaded_files


if __name__ == '__main__':
    download_all()
