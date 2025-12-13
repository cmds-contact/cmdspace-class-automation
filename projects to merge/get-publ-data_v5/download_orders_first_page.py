"""주문 목록 다운로드 스크립트"""
import os
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

PUBL_ID = os.getenv('PUBL_ID')
PUBL_PW = os.getenv('PUBL_PW')

# 다운로드 폴더
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

with sync_playwright() as p:
	browser = p.chromium.launch(headless=False)
	context = browser.new_context(accept_downloads=True)
	page = context.new_page()
	page.set_default_timeout(60000)

	# 1. 로그인 페이지 접속
	print("1. 로그인 페이지 접속...")
	page.goto('https://console.publ.biz/?type=enter')
	page.wait_for_timeout(3000)

	# 2. 로그인
	print("2. 로그인 중...")
	page.locator('input[name="email"]').fill(PUBL_ID)
	page.locator('input[name="password"][placeholder="Password"]').fill(PUBL_PW)
	page.get_by_role("button", name="Login", exact=True).click()
	page.wait_for_timeout(5000)

	# 3. 주문 목록 페이지로 이동
	print("3. 주문 목록 페이지로 이동...")
	page.goto('https://console.publ.biz/channels/L2NoYW5uZWxzLzE3Njkx/orders/subs-products')
	page.wait_for_timeout(3000)
	page.screenshot(path='screenshots/04_orders_page.png', full_page=True)

	# 4. 페이지 요소 확인
	print("4. 페이지 요소 확인 중...")

	# 모든 버튼과 링크 출력
	all_buttons = page.locator('button, a').all()
	for i, elem in enumerate(all_buttons):
		text = elem.inner_text().strip()
		if text:
			print(f"   [{i}] {text[:50]}")

	# 5. 다운로드 아이콘 클릭 (오른쪽 상단의 다운로드 아이콘)
	print("5. 다운로드 아이콘 클릭...")
	# path 속성에 다운로드 아이콘 특유의 경로가 있는 SVG를 가진 버튼 찾기
	download_btn = page.locator('svg path[d*="20.1835,14.7857"]').locator('xpath=ancestor::button')

	with page.expect_download() as download_info:
		download_btn.click()

	download = download_info.value
	# 타임스탬프 추가 (251129_101111 형식)
	timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
	filename = f"orders_{timestamp}.csv"
	download_path = os.path.join(DOWNLOAD_DIR, filename)
	download.save_as(download_path)
	print(f"   다운로드 완료: {download_path}")

	browser.close()
	print("\n완료!")
