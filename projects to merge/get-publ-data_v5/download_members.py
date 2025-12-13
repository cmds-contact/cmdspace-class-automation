"""회원 목록 다운로드 스크립트"""
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

	# 3. 회원 목록 페이지로 이동
	print("3. 회원 목록 페이지로 이동...")
	page.goto('https://console.publ.biz/channels/L2NoYW5uZWxzLzE3Njkx/members/registered-users')
	page.wait_for_timeout(3000)
	page.screenshot(path='screenshots/03_members_page.png', full_page=True)

	# 4. 다운로드 버튼 찾기
	print("4. 다운로드 버튼 찾는 중...")
	buttons = page.locator('button').all()
	for i, btn in enumerate(buttons):
		text = btn.inner_text().strip()
		if text:
			print(f"   [{i}] {text[:50]}")

	# 5. "All Member download(CSV)" 버튼 클릭
	print("5. All Member download(CSV) 버튼 클릭...")
	with page.expect_download() as download_info:
		page.get_by_role("button", name="All Member download(CSV)").click()

	download = download_info.value
	# 타임스탬프 추가 (251129_101111 형식)
	timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
	filename = f"members_{timestamp}.csv"
	download_path = os.path.join(DOWNLOAD_DIR, filename)
	download.save_as(download_path)
	print(f"   다운로드 완료: {download_path}")

	browser.close()
	print("\n완료!")
