"""publ 데이터 통합 다운로드 스크립트 (최적화 버전)"""
import os
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

PUBL_ID = os.getenv('PUBL_ID')
PUBL_PW = os.getenv('PUBL_PW')

# 폴더 설정
BASE_DIR = os.path.dirname(__file__)
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'downloads')
SESSION_FILE = os.path.join(BASE_DIR, '.session.json')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 설정
HEADLESS = True  # 브라우저 안 보임

def get_timestamp():
	"""타임스탬프 생성 (YYMMDD_HHMMSS)"""
	return datetime.now().strftime("%y%m%d_%H%M%S")

def save_download(download, filename):
	"""다운로드 파일 저장"""
	download_path = os.path.join(DOWNLOAD_DIR, filename)
	download.save_as(download_path)
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
	try:
		page = context.new_page()
		page.goto('https://console.publ.biz/all-channels')
		# 로그인 페이지로 리다이렉트되면 세션 만료
		page.wait_for_timeout(2000)
		if 'type=enter' in page.url:
			page.close()
			return False
		page.close()
		return True
	except:
		return False

with sync_playwright() as p:
	browser = p.chromium.launch(headless=HEADLESS)

	# ========================================
	# 세션 로드 또는 새로 로그인
	# ========================================
	print("=" * 50)
	print("1. 로그인")
	print("=" * 50)

	# 저장된 세션이 있으면 로드 시도
	if os.path.exists(SESSION_FILE):
		print("   저장된 세션 확인 중...")
		context = browser.new_context(
			storage_state=SESSION_FILE,
			accept_downloads=True
		)
		context.set_default_timeout(30000)

		# 리소스 차단 적용
		context.route("**/*", block_resources)

		if is_session_valid(context):
			print("   저장된 세션 사용!")
			page = context.new_page()
		else:
			print("   세션 만료, 다시 로그인...")
			context.close()
			context = None
	else:
		context = None

	# 새로 로그인 필요한 경우
	if context is None:
		context = browser.new_context(accept_downloads=True)
		context.set_default_timeout(30000)

		# 리소스 차단 적용
		context.route("**/*", block_resources)

		page = context.new_page()
		page.goto('https://console.publ.biz/?type=enter')

		# 로그인 폼이 나타날 때까지 대기 (고정 시간 대신)
		page.wait_for_selector('input[name="email"]')

		page.locator('input[name="email"]').fill(PUBL_ID)
		page.locator('input[name="password"][placeholder="Password"]').fill(PUBL_PW)
		page.get_by_role("button", name="Login", exact=True).click()

		# 로그인 완료될 때까지 대기 (URL 변경 감지)
		page.wait_for_url('**/all-channels**', timeout=30000)

		# 세션 저장
		context.storage_state(path=SESSION_FILE)
		print("   로그인 완료! (세션 저장됨)")

	# ========================================
	# 1. 회원 목록 다운로드
	# ========================================
	print("\n" + "=" * 50)
	print("2. 회원 목록 다운로드")
	print("=" * 50)

	page.goto('https://console.publ.biz/channels/L2NoYW5uZWxzLzE3Njkx/members/registered-users')

	# 다운로드 버튼이 나타날 때까지 대기
	download_btn = page.get_by_role("button", name="All Member download(CSV)")
	download_btn.wait_for(state="visible")

	with page.expect_download() as download_info:
		download_btn.click()

	download = download_info.value
	save_download(download, f"{get_timestamp()}_members.csv")

	# ========================================
	# 2. 주문 목록 (최신) 다운로드
	# ========================================
	print("\n" + "=" * 50)
	print("3. 주문 목록 (Latest) 다운로드")
	print("=" * 50)

	page.goto('https://console.publ.biz/channels/L2NoYW5uZWxzLzE3Njkx/orders/subs-products')

	# 다운로드 버튼이 나타날 때까지 대기
	download_btn = page.locator('svg path[d*="20.1835,14.7857"]').locator('xpath=ancestor::button')
	download_btn.wait_for(state="visible")

	with page.expect_download() as download_info:
		download_btn.click()

	download = download_info.value
	save_download(download, f"{get_timestamp()}_orders_latest.csv")

	# ========================================
	# 3. 환불 목록 다운로드
	# ========================================
	print("\n" + "=" * 50)
	print("4. 환불 목록 다운로드")
	print("=" * 50)

	page.goto('https://console.publ.biz/channels/L2NoYW5uZWxzLzE3Njkx/orders/refunds')

	# 다운로드 버튼이 나타날 때까지 대기
	download_btn = page.locator('svg path[d*="20.1835,14.7857"]').locator('xpath=ancestor::button')
	download_btn.wait_for(state="visible")

	with page.expect_download() as download_info:
		download_btn.click()

	download = download_info.value
	save_download(download, f"{get_timestamp()}_refunds.csv")

	# ========================================
	# 완료
	# ========================================
	print("\n" + "=" * 50)
	print("모든 다운로드 완료!")
	print("=" * 50)

	browser.close()
