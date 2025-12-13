"""로그인 페이지 구조 파악을 위한 reconnaissance 스크립트"""
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

PUBL_ID = os.getenv('PUBL_ID')
PUBL_PW = os.getenv('PUBL_PW')

with sync_playwright() as p:
	browser = p.chromium.launch(headless=False)  # 브라우저 보이게
	page = browser.new_page()
	page.set_default_timeout(60000)  # 60초 타임아웃

	# 1. 로그인 페이지 접속
	print("1. 로그인 페이지 접속...")
	page.goto('https://console.publ.biz/?type=enter')
	page.wait_for_timeout(5000)  # 5초 대기
	page.screenshot(path='screenshots/01_login_page.png', full_page=True)

	# 2. 페이지 구조 파악 - 입력 필드와 버튼 찾기
	print("2. 입력 필드 찾는 중...")
	inputs = page.locator('input').all()
	for i, inp in enumerate(inputs):
		input_type = inp.get_attribute('type') or 'text'
		input_name = inp.get_attribute('name') or ''
		input_placeholder = inp.get_attribute('placeholder') or ''
		print(f"   Input {i}: type={input_type}, name={input_name}, placeholder={input_placeholder}")

	buttons = page.locator('button').all()
	for i, btn in enumerate(buttons):
		btn_text = btn.inner_text()
		print(f"   Button {i}: {btn_text}")

	# 3. 로그인 시도
	print("3. 로그인 시도...")
	# 이메일 입력
	email_input = page.locator('input[name="email"]')
	email_input.fill(PUBL_ID)

	# 비밀번호 입력 (placeholder가 "Password"인 것)
	pw_input = page.locator('input[name="password"][placeholder="Password"]')
	pw_input.fill(PUBL_PW)

	# 로그인 버튼 클릭 (정확히 "Login"만)
	login_btn = page.get_by_role("button", name="Login", exact=True)
	login_btn.click()

	# 로그인 후 대기
	page.wait_for_timeout(5000)  # 5초 대기

	# 4. 로그인 후 화면 스크린샷
	print("4. 로그인 후 화면...")
	page.screenshot(path='screenshots/02_after_login.png', full_page=True)
	print(f"   현재 URL: {page.url}")

	# 5. 메뉴 구조 파악
	print("5. 메뉴/링크 찾는 중...")
	links = page.locator('a, button').all()
	for i, link in enumerate(links[:30]):  # 처음 30개만
		text = link.inner_text().strip()
		if text:
			print(f"   [{i}] {text[:50]}")

	print("\n브라우저를 30초간 열어둡니다. 직접 확인하세요...")
	page.wait_for_timeout(30000)

	browser.close()
