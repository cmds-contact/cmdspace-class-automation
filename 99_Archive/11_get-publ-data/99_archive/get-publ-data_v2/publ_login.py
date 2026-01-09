"""
PUBL 콘솔 로그인 자동화 스크립트
"""
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv


def setup_driver():
    """Chrome 드라이버 설정"""
    options = webdriver.ChromeOptions()
    # 브라우저가 보이도록 설정 (headless 모드 비활성화)
    # options.add_argument('--headless')  # 필요시 주석 해제
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 드라이버 초기화
    try:
        # ChromeDriver 자동 설치 및 경로 가져오기
        driver_path = ChromeDriverManager().install()
        print(f"📦 ChromeDriver 경로: {driver_path}")
        
        # 실제 chromedriver 실행 파일 찾기
        import os
        if os.path.isdir(driver_path):
            # 디렉토리인 경우, chromedriver 실행 파일 찾기
            for root, dirs, files in os.walk(driver_path):
                for file in files:
                    if file == 'chromedriver':
                        driver_path = os.path.join(root, file)
                        break
        
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.maximize_window()
        
        return driver
    except Exception as e:
        print(f"❌ ChromeDriver 설정 오류: {str(e)}")
        print("💡 시스템의 Chrome 브라우저를 사용하여 재시도합니다...")
        # 시스템 ChromeDriver 사용 시도
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        return driver


def login_to_publ(driver, email, password):
    """PUBL 콘솔에 로그인"""
    try:
        # 1. PUBL 콘솔 페이지로 이동
        print("📍 PUBL 콘솔 페이지로 이동 중...")
        driver.get("https://console.publ.biz/?type=enter")
        
        # 페이지 로딩 대기
        wait = WebDriverWait(driver, 15)
        time.sleep(2)  # 페이지가 완전히 로드될 때까지 대기
        
        # 페이지의 모든 input 요소 확인
        print("🔍 페이지 요소 분석 중...")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"   - 발견된 input 요소 수: {len(inputs)}")
        
        # 2. 이메일 입력 필드 찾기 및 입력
        print("✉️  이메일 입력 중...")
        email_field = None
        
        # 여러 방법으로 이메일 필드 찾기
        selectors = [
            "input[type='email']",
            "input[name='email']",
            "input[id*='email']",
            "input[placeholder*='이메일']",
            "input[placeholder*='email']",
            "input[placeholder*='Email']",
            "input[autocomplete='username']",
            "input[autocomplete='email']"
        ]
        
        for selector in selectors:
            try:
                email_field = driver.find_element(By.CSS_SELECTOR, selector)
                if email_field and email_field.is_displayed():
                    print(f"   - 이메일 필드 발견: {selector}")
                    break
            except:
                continue
        
        # 찾지 못한 경우 첫 번째 input 사용
        if not email_field and len(inputs) > 0:
            email_field = inputs[0]
            print(f"   - 첫 번째 input 요소 사용")
        
        if email_field:
            # 클릭하여 포커스
            email_field.click()
            time.sleep(0.3)
            # 기존 값 지우기
            email_field.clear()
            time.sleep(0.3)
            # send_keys로 입력
            email_field.send_keys(email)
            time.sleep(0.5)
            print(f"   - 이메일 입력 완료: {email}")
        else:
            print("❌ 이메일 입력 필드를 찾을 수 없습니다.")
            return False
        
        # 3. 비밀번호 입력 필드 찾기 및 입력
        print("🔒 비밀번호 입력 중...")
        password_field = None
        
        password_selectors = [
            "input[type='password']",
            "input[name='password']",
            "input[id*='password']",
            "input[autocomplete='current-password']"
        ]
        
        for selector in password_selectors:
            try:
                password_field = driver.find_element(By.CSS_SELECTOR, selector)
                if password_field and password_field.is_displayed():
                    print(f"   - 비밀번호 필드 발견: {selector}")
                    break
            except:
                continue
        
        # 찾지 못한 경우 두 번째 input 사용
        if not password_field and len(inputs) > 1:
            password_field = inputs[1]
            print(f"   - 두 번째 input 요소 사용")
        
        if password_field:
            # 클릭하여 포커스
            password_field.click()
            time.sleep(0.3)
            # 기존 값 지우기
            password_field.clear()
            time.sleep(0.3)
            # send_keys로 한 글자씩 입력
            for char in password:
                password_field.send_keys(char)
                time.sleep(0.05)  # 각 문자 사이에 약간의 딜레이
            time.sleep(0.5)
            print(f"   - 비밀번호 입력 완료 ({len(password)}자)")
        else:
            print("❌ 비밀번호 입력 필드를 찾을 수 없습니다.")
            return False
        
        # 4. 로그인 버튼 찾기 및 클릭
        print("🔑 로그인 버튼 클릭 중...")
        login_button = None
        
        button_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button.login",
            "button.btn-login",
            "a.login-button"
        ]
        
        for selector in button_selectors:
            try:
                login_button = driver.find_element(By.CSS_SELECTOR, selector)
                if login_button and login_button.is_displayed():
                    print(f"   - 로그인 버튼 발견: {selector}")
                    break
            except:
                continue
        
        # 버튼을 찾지 못한 경우 모든 버튼 검색
        if not login_button:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                text = btn.text.lower()
                if '로그인' in text or 'login' in text or '입장' in text:
                    login_button = btn
                    print(f"   - 로그인 버튼 발견 (텍스트 기반): {btn.text}")
                    break
        
        if login_button:
            # JavaScript로 클릭 (더 안정적)
            driver.execute_script("arguments[0].click();", login_button)
            time.sleep(1)
            print(f"   - 로그인 버튼 클릭 완료")
        else:
            print("❌ 로그인 버튼을 찾을 수 없습니다.")
            # Enter 키로 폼 제출 시도
            print("💡 Enter 키로 폼 제출 시도...")
            from selenium.webdriver.common.keys import Keys
            password_field.send_keys(Keys.RETURN)
        
        # 5. 로그인 완료 대기 (URL 변경 또는 특정 요소 확인)
        print("⏳ 로그인 처리 중...")
        time.sleep(3)
        
        # 현재 URL 확인
        current_url = driver.current_url
        print(f"   - 현재 URL: {current_url}")
        
        # 페이지 소스에서 오류 메시지 확인
        page_source = driver.page_source
        
        # 로그인 성공 확인
        if "type=enter" not in current_url:
            print("✅ 로그인 성공! (URL 변경 감지)")
            return True
        else:
            print("⚠️  로그인 페이지에 머물러 있습니다.")
            print("   - 추가 확인을 위해 10초간 대기합니다...")
            time.sleep(10)
            
            current_url = driver.current_url
            print(f"   - 10초 후 URL: {current_url}")
            
            if "type=enter" not in current_url:
                print("✅ 로그인 성공!")
                return True
            else:
                print("   - 로그인 정보를 확인하거나 수동으로 로그인해주세요.")
                print("   - 브라우저 창을 확인하세요.")
                return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 실행 함수"""
    # 환경변수 로드
    load_dotenv()
    
    email = os.getenv('PUBL_EMAIL')
    password = os.getenv('PUBL_PASSWORD')
    
    if not email or not password:
        print("❌ 환경변수가 설정되지 않았습니다.")
        print("   .env 파일에 PUBL_EMAIL과 PUBL_PASSWORD를 설정해주세요.")
        return
    
    print("=" * 50)
    print("🚀 PUBL 콘솔 로그인 자동화 시작")
    print("=" * 50)
    
    driver = None
    try:
        # 드라이버 설정
        driver = setup_driver()
        
        # 로그인 실행
        success = login_to_publ(driver, email, password)
        
        if success:
            print("\n" + "=" * 50)
            print("✅ 모든 작업이 완료되었습니다!")
            print("=" * 50)
            
            # 브라우저를 열어둔 상태로 대기 (확인용)
            input("\n계속하려면 Enter 키를 누르세요...")
        else:
            print("\n" + "=" * 50)
            print("❌ 로그인에 실패했습니다.")
            print("=" * 50)
            
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {str(e)}")
        
    finally:
        if driver:
            print("\n🔚 브라우저를 종료합니다...")
            driver.quit()


if __name__ == "__main__":
    main()

