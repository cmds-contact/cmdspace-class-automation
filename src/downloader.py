"""publ.biz 데이터 다운로드 모듈"""

import os
from datetime import datetime
from playwright.sync_api import sync_playwright

from . import config


def get_timestamp():
    """타임스탬프 생성 (YYMMDD_HHMMSS)"""
    return datetime.now().strftime("%y%m%d_%H%M%S")


def save_download(download, filename):
    """다운로드 파일 저장"""
    download_path = config.DOWNLOAD_DIR / filename
    download.save_as(str(download_path))
    print(f"   저장 완료: {filename}")
    return download_path


def block_resources(route):
    """불필요한 리소스 차단 (이미지, 폰트, 미디어)"""
    if route.request.resource_type in ['image', 'font', 'media']:
        route.abort()
    else:
        route.continue_()


def is_session_valid(context):
    """저장된 세션이 유효한지 확인"""
    page = None
    try:
        page = context.new_page()
        page.goto('https://console.publ.biz/all-channels')
        page.wait_for_timeout(2000)
        if 'type=enter' in page.url:
            return False
        return True
    except Exception:
        return False
    finally:
        if page:
            page.close()


def login(browser):
    """로그인 처리 및 컨텍스트 반환"""
    print("=" * 50)
    print("1. 로그인")
    print("=" * 50)

    session_file = str(config.SESSION_FILE)

    # 저장된 세션이 있으면 로드 시도
    if os.path.exists(session_file):
        print("   저장된 세션 확인 중...")
        context = browser.new_context(
            storage_state=session_file,
            accept_downloads=True
        )
        context.set_default_timeout(config.DEFAULT_TIMEOUT)
        context.route("**/*", block_resources)

        if is_session_valid(context):
            print("   저장된 세션 사용!")
            page = context.new_page()
            return context, page
        else:
            print("   세션 만료, 다시 로그인...")
            context.close()

    # 새로 로그인
    context = browser.new_context(accept_downloads=True)
    context.set_default_timeout(config.DEFAULT_TIMEOUT)
    context.route("**/*", block_resources)

    page = context.new_page()
    page.goto(config.PUBL_LOGIN_URL)

    # 로그인 폼 대기
    page.wait_for_selector('input[name="email"]')

    page.locator('input[name="email"]').fill(config.PUBL_ID)
    page.locator('input[name="password"][placeholder="Password"]').fill(config.PUBL_PW)
    page.get_by_role("button", name="Login", exact=True).click()

    # 로그인 완료 대기
    page.wait_for_url('**/all-channels**', timeout=30000)

    # 세션 저장
    context.storage_state(path=session_file)
    print("   로그인 완료! (세션 저장됨)")

    return context, page


def download_members(page, timestamp):
    """회원 목록 다운로드"""
    print("\n" + "=" * 50)
    print("2. 회원 목록 다운로드")
    print("=" * 50)

    page.goto(config.PUBL_MEMBERS_URL)

    # 다운로드 버튼 대기
    download_btn = page.get_by_role("button", name="All Member download(CSV)")
    download_btn.wait_for(state="visible")

    with page.expect_download() as download_info:
        download_btn.click()

    download = download_info.value
    return save_download(download, f"{timestamp}_members.csv")


def download_orders(page, timestamp):
    """주문 목록 (최신) 다운로드"""
    print("\n" + "=" * 50)
    print("3. 주문 목록 (Latest) 다운로드")
    print("=" * 50)

    page.goto(config.PUBL_ORDERS_URL)

    # 다운로드 버튼 대기 (SVG 아이콘 기반)
    download_btn = page.locator('svg path[d*="20.1835,14.7857"]').locator('xpath=ancestor::button')
    download_btn.wait_for(state="visible")

    with page.expect_download() as download_info:
        download_btn.click()

    download = download_info.value
    return save_download(download, f"{timestamp}_orders_latest.csv")


def download_refunds(page, timestamp):
    """환불 목록 다운로드"""
    print("\n" + "=" * 50)
    print("4. 환불 목록 다운로드")
    print("=" * 50)

    page.goto(config.PUBL_REFUNDS_URL)

    # 다운로드 버튼 대기 (SVG 아이콘 기반)
    download_btn = page.locator('svg path[d*="20.1835,14.7857"]').locator('xpath=ancestor::button')
    download_btn.wait_for(state="visible")

    with page.expect_download() as download_info:
        download_btn.click()

    download = download_info.value
    return save_download(download, f"{timestamp}_refunds.csv")


def download_all():
    """전체 데이터 다운로드"""
    config.ensure_directories()
    timestamp = get_timestamp()
    downloaded_files = {}
    context = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.HEADLESS)

        try:
            context, page = login(browser)

            # 데이터 다운로드
            downloaded_files['members'] = download_members(page, timestamp)
            downloaded_files['orders'] = download_orders(page, timestamp)
            downloaded_files['refunds'] = download_refunds(page, timestamp)

            print("\n" + "=" * 50)
            print("다운로드 완료!")
            print("=" * 50)

        finally:
            if context:
                context.close()
            browser.close()

    return downloaded_files


if __name__ == '__main__':
    download_all()
