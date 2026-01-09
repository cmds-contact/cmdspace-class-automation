const { initializeBrowser } = require('./modules/browser-init');
const { getLoginCredentials, performLogin } = require('./modules/login');
const { downloadMembersCSV } = require('./modules/download-members');
const { downloadOrdersCSV } = require('./modules/download-orders');
const { keepBrowserOpen } = require('./modules/keep-browser');

/**
 * 전체 워크플로우 실행
 */
async function runWorkflow() {
  let browser = null;
  let page = null;

  try {
    // 1. 초기화 및 환경 설정
    console.log('\n=== 1단계: 초기화 및 환경 설정 ===');
    const { browser: browserInstance, page: pageInstance, downloadPath } = await initializeBrowser();
    browser = browserInstance;
    page = pageInstance;

    // 2. 로그인하기
    console.log('\n=== 2단계: 로그인하기 ===');
    const credentials = getLoginCredentials();
    if (!credentials) {
      await browser.close();
      return;
    }

    const loginSuccess = await performLogin(page, credentials.email, credentials.password);
    if (!loginSuccess) {
      console.error('❌ 로그인 실패. 프로세스를 종료합니다.');
      await browser.close();
      return;
    }

    // 3. 회원 정보 CSV 파일 다운로드
    await downloadMembersCSV(page, downloadPath);

    // 4. 주문 목록 CSV 파일 다운로드
    await downloadOrdersCSV(page, downloadPath);

    // 마지막. 브라우저 유지
    await keepBrowserOpen();

  } catch (error) {
    console.error('\n❌ 오류 발생:', error.message);
    console.error('스택 트레이스:', error.stack);
    
    // 오류 발생 시 스크린샷 저장
    if (page) {
      try {
        await page.screenshot({ path: 'error-screenshot.png', fullPage: true });
        console.log('오류 스크린샷이 error-screenshot.png에 저장되었습니다.');
      } catch (screenshotError) {
        console.log('스크린샷 저장 실패:', screenshotError.message);
      }
    }
    
    // 오류 발생 시에도 브라우저 닫기
    if (browser) {
      await browser.close();
      console.log('브라우저를 닫았습니다.');
    }
  }
}

// 스크립트 실행
if (require.main === module) {
  runWorkflow().catch(console.error);
}

module.exports = {
  runWorkflow
};

