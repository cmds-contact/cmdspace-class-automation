#!/usr/bin/env node

/**
 * 개별 모듈 테스트 스크립트
 * 
 * 사용 방법:
 * node test-modules.js <module-name>
 * 
 * 예시:
 * node test-modules.js browser-init
 * node test-modules.js login
 * node test-modules.js download-members
 * node test-modules.js download-orders
 */

const { initializeBrowser } = require('./modules/browser-init');
const { getLoginCredentials, performLogin } = require('./modules/login');
const { downloadMembersCSV } = require('./modules/download-members');
const { downloadOrdersCSV } = require('./modules/download-orders');
const { keepBrowserOpen } = require('./modules/keep-browser');

const moduleName = process.argv[2];

if (!moduleName) {
  console.error('❌ 모듈 이름을 지정해주세요.');
  console.log('\n사용 가능한 모듈:');
  console.log('  - browser-init: 브라우저 초기화 테스트');
  console.log('  - login: 로그인 테스트');
  console.log('  - download-members: 회원 정보 다운로드 테스트');
  console.log('  - download-orders: 주문 목록 다운로드 테스트');
  console.log('  - keep-browser: 브라우저 유지 테스트');
  console.log('\n사용 방법:');
  console.log('  node test-modules.js <module-name>');
  process.exit(1);
}

async function testModule() {
  let browser = null;
  let page = null;
  let downloadPath = null;

  try {
    switch (moduleName) {
      case 'browser-init': {
        console.log('=== 브라우저 초기화 모듈 테스트 ===\n');
        const result = await initializeBrowser();
        browser = result.browser;
        page = result.page;
        downloadPath = result.downloadPath;
        console.log('\n✅ 브라우저 초기화 성공');
        console.log('브라우저를 열어둡니다. 수동으로 닫아주세요.');
        await keepBrowserOpen();
        break;
      }

      case 'login': {
        console.log('=== 로그인 모듈 테스트 ===\n');
        const { browser: browserInstance, page: pageInstance, downloadPath: dp } = await initializeBrowser();
        browser = browserInstance;
        page = pageInstance;
        downloadPath = dp;

        const credentials = getLoginCredentials();
        if (!credentials) {
          await browser.close();
          return;
        }

        const success = await performLogin(page, credentials.email, credentials.password);
        if (success) {
          console.log('\n✅ 로그인 테스트 성공');
          console.log('브라우저를 열어둡니다. 수동으로 닫아주세요.');
          await keepBrowserOpen();
        } else {
          console.log('\n❌ 로그인 테스트 실패');
          await browser.close();
        }
        break;
      }

      case 'download-members': {
        console.log('=== 회원 정보 다운로드 모듈 테스트 ===\n');
        console.log('⚠️  주의: 이 테스트를 실행하려면 먼저 로그인되어 있어야 합니다.\n');
        
        const { browser: browserInstance, page: pageInstance, downloadPath: dp } = await initializeBrowser();
        browser = browserInstance;
        page = pageInstance;
        downloadPath = dp;

        const credentials = getLoginCredentials();
        if (!credentials) {
          await browser.close();
          return;
        }

        const loginSuccess = await performLogin(page, credentials.email, credentials.password);
        if (!loginSuccess) {
          console.error('❌ 로그인 실패. 테스트를 종료합니다.');
          await browser.close();
          return;
        }

        const success = await downloadMembersCSV(page, downloadPath);
        if (success) {
          console.log('\n✅ 회원 정보 다운로드 테스트 성공');
        } else {
          console.log('\n❌ 회원 정보 다운로드 테스트 실패');
        }

        console.log('브라우저를 열어둡니다. 수동으로 닫아주세요.');
        await keepBrowserOpen();
        break;
      }

      case 'download-orders': {
        console.log('=== 주문 목록 다운로드 모듈 테스트 ===\n');
        console.log('⚠️  주의: 이 테스트를 실행하려면 먼저 로그인되어 있어야 합니다.\n');
        
        const { browser: browserInstance, page: pageInstance, downloadPath: dp } = await initializeBrowser();
        browser = browserInstance;
        page = pageInstance;
        downloadPath = dp;

        const credentials = getLoginCredentials();
        if (!credentials) {
          await browser.close();
          return;
        }

        const loginSuccess = await performLogin(page, credentials.email, credentials.password);
        if (!loginSuccess) {
          console.error('❌ 로그인 실패. 테스트를 종료합니다.');
          await browser.close();
          return;
        }

        const success = await downloadOrdersCSV(page, downloadPath);
        if (success) {
          console.log('\n✅ 주문 목록 다운로드 테스트 성공');
        } else {
          console.log('\n❌ 주문 목록 다운로드 테스트 실패');
        }

        console.log('브라우저를 열어둡니다. 수동으로 닫아주세요.');
        await keepBrowserOpen();
        break;
      }

      case 'keep-browser': {
        console.log('=== 브라우저 유지 모듈 테스트 ===\n');
        console.log('브라우저를 열어두는 기능을 테스트합니다.');
        console.log('Ctrl+C를 눌러 종료할 수 있습니다.\n');
        await keepBrowserOpen();
        break;
      }

      default:
        console.error(`❌ 알 수 없는 모듈: ${moduleName}`);
        console.log('\n사용 가능한 모듈:');
        console.log('  - browser-init');
        console.log('  - login');
        console.log('  - download-members');
        console.log('  - download-orders');
        console.log('  - keep-browser');
        process.exit(1);
    }

  } catch (error) {
    console.error('\n❌ 테스트 중 오류 발생:', error.message);
    console.error('스택 트레이스:', error.stack);
    
    if (page) {
      try {
        await page.screenshot({ path: 'error-screenshot.png', fullPage: true });
        console.log('오류 스크린샷이 error-screenshot.png에 저장되었습니다.');
      } catch (screenshotError) {
        console.log('스크린샷 저장 실패:', screenshotError.message);
      }
    }
    
    if (browser) {
      await browser.close();
      console.log('브라우저를 닫았습니다.');
    }
  }
}

testModule().catch(console.error);

