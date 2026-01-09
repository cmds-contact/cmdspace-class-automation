require('dotenv').config();

/**
 * 로그인 정보 확인 및 유효성 검증
 * @returns {{email: string, password: string} | null} 로그인 정보 또는 null
 */
function getLoginCredentials() {
  const email = process.env.PUBL_EMAIL || process.argv[2];
  const password = process.env.PUBL_PASSWORD || process.argv[3];

  console.log('🔍 환경변수 확인:');
  console.log(`  - EMAIL: ${email ? '✓ 설정됨 (' + email.length + '자)' : '✗ 없음'}`);
  console.log(`  - EMAIL 값: ${email ? email.substring(0, 3) + '***' + email.substring(email.length - 3) : 'N/A'}`);
  console.log(`  - PASSWORD: ${password ? '✓ 설정됨 (' + password.length + '자)' : '✗ 없음'}`);
  console.log(`  - PASSWORD 값: ${password ? password.substring(0, 2) + '***' + password.substring(password.length - 2) : 'N/A'}`);

  if (!email || !password) {
    console.error('❌ 이메일과 비밀번호가 필요합니다.');
    console.log('사용 방법:');
    console.log('1. .env 파일에 PUBL_EMAIL과 PUBL_PASSWORD 설정');
    console.log('2. 또는 명령줄 인자로 전달: node script.js <email> <password>');
    return null;
  }

  return { email, password };
}

/**
 * 로그인 페이지로 이동
 * @param {Page} page - Playwright Page 객체
 * @returns {Promise<void>}
 */
async function navigateToLoginPage(page) {
  console.log('publ.biz 로그인 페이지로 이동 중...');
  
  try {
    await page.goto('https://console.publ.biz/?type=enter', {
      waitUntil: 'domcontentloaded',
      timeout: 60000
    });
    console.log('✓ 페이지 이동 완료');
  } catch (e) {
    console.log('⚠️  페이지 로드 타임아웃, 계속 진행...');
  }

  // 페이지 로드 대기 - 로그인 폼이 나타날 때까지 대기
  console.log('페이지 로드 대기 중...');
  try {
    await page.waitForSelector('input[name="email"]', { timeout: 10000, state: 'visible' });
    console.log('✓ 로그인 폼이 로드되었습니다.');
  } catch (e) {
    console.log('⚠️  로그인 폼 대기 중 타임아웃, 계속 진행...');
    // 페이지 스크린샷 저장
    await page.screenshot({ path: 'page-load-screenshot.png', fullPage: true });
    console.log('페이지 스크린샷이 page-load-screenshot.png에 저장되었습니다.');
  }
  await page.waitForTimeout(500);
}

/**
 * 로그인 정보 입력
 * @param {Page} page - Playwright Page 객체
 * @param {string} email - 이메일
 * @param {string} password - 비밀번호
 * @returns {Promise<void>}
 */
async function fillLoginForm(page, email, password) {
  console.log('로그인 정보 입력 중...');

  // E-mail 입력 필드 찾기 및 입력
  const emailSelectors = [
    'input[name="email"]',
    'input[placeholder="E-mail"]',
    'input[type="text"][placeholder*="mail" i]'
  ];

  let emailFilled = false;
  let lastEmailError = null;
  for (const selector of emailSelectors) {
    try {
      console.log(`  - 이메일 필드 찾기 시도: ${selector}`);
      const element = await page.waitForSelector(selector, { timeout: 3000, state: 'visible' });
      if (element) {
        await element.click();
        await page.waitForTimeout(100);
        await page.keyboard.press('Meta+A');
        await page.keyboard.press('Backspace');
        await page.waitForTimeout(50);
        await element.fill(email);
        await page.waitForTimeout(100);
        const inputValue = await element.inputValue();
        console.log(`✓ 이메일 입력 완료 (${inputValue.length}자 입력됨)`);
        console.log(`  입력된 값: ${inputValue.substring(0, 3)}***${inputValue.substring(inputValue.length - 3)}`);
        emailFilled = true;
        break;
      }
    } catch (e) {
      lastEmailError = e.message;
      console.log(`  - 실패: ${e.message}`);
      continue;
    }
  }

  if (!emailFilled) {
    const allInputs = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('input')).map(inp => ({
        type: inp.type,
        name: inp.name,
        placeholder: inp.placeholder,
        id: inp.id,
        visible: inp.offsetParent !== null
      }));
    });
    console.error('페이지의 모든 input 요소:', JSON.stringify(allInputs, null, 2));
    throw new Error(`이메일 입력 필드를 찾을 수 없습니다. 마지막 오류: ${lastEmailError}`);
  }

  await page.waitForTimeout(300);

  // Password 입력 필드 찾기 및 입력
  const passwordSelectors = [
    'input[name="password"][type="password"]',
    'input[type="password"][placeholder="Password"]',
    'input[type="password"]:not([name="removePassword"])'
  ];

  let passwordFilled = false;
  let lastPasswordError = null;
  for (const selector of passwordSelectors) {
    try {
      console.log(`  - 비밀번호 필드 찾기 시도: ${selector}`);
      const element = await page.waitForSelector(selector, { timeout: 3000, state: 'visible' });
      if (element) {
        await element.click();
        await page.waitForTimeout(100);
        await page.keyboard.press('Meta+A');
        await page.keyboard.press('Backspace');
        await page.waitForTimeout(50);
        await element.fill(password);
        await page.waitForTimeout(100);
        const inputValue = await element.inputValue();
        console.log(`✓ 비밀번호 입력 완료 (${inputValue.length}자 입력됨)`);
        console.log(`  입력된 값: ${inputValue.substring(0, 2)}***${inputValue.substring(inputValue.length - 2)}`);
        passwordFilled = true;
        break;
      }
    } catch (e) {
      lastPasswordError = e.message;
      console.log(`  - 실패: ${e.message}`);
      continue;
    }
  }

  if (!passwordFilled) {
    throw new Error(`비밀번호 입력 필드를 찾을 수 없습니다. 마지막 오류: ${lastPasswordError}`);
  }

  await page.waitForTimeout(300);
}

/**
 * 로그인 버튼 클릭
 * @param {Page} page - Playwright Page 객체
 * @returns {Promise<void>}
 */
async function clickLoginButton(page) {
  const loginButtonSelectors = [
    'button[type="submit"]:has-text("Login")',
    'button:has-text("Login")',
    'button[type="submit"]'
  ];

  let loginClicked = false;
  let lastButtonError = null;
  for (const selector of loginButtonSelectors) {
    try {
      console.log(`  - 로그인 버튼 찾기 시도: ${selector}`);
      const element = await page.waitForSelector(selector, { timeout: 3000, state: 'visible' });
      if (element) {
        const isEnabled = await element.isEnabled();
        console.log(`  - 버튼 활성화 상태: ${isEnabled}`);
        await element.click();
        console.log(`✓ 로그인 버튼 클릭 완료`);
        loginClicked = true;
        break;
      }
    } catch (e) {
      lastButtonError = e.message;
      console.log(`  - 실패: ${e.message}`);
      continue;
    }
  }

  if (!loginClicked) {
    const allButtons = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('button')).map(btn => ({
        text: btn.textContent?.trim(),
        type: btn.type,
        id: btn.id,
        visible: btn.offsetParent !== null,
        enabled: !btn.disabled
      }));
    });
    console.error('페이지의 모든 button 요소:', JSON.stringify(allButtons, null, 2));
    throw new Error(`로그인 버튼을 찾을 수 없습니다. 마지막 오류: ${lastButtonError}`);
  }
}

/**
 * 로그인 결과 확인
 * @param {Page} page - Playwright Page 객체
 * @returns {Promise<boolean>} 로그인 성공 여부
 */
async function verifyLoginResult(page) {
  console.log('로그인 처리 중...');
  
  const initialUrl = page.url();
  console.log(`초기 URL: ${initialUrl}`);
  
  try {
    await page.waitForURL(url => url !== initialUrl && !url.includes('type=enter'), { 
      timeout: 15000 
    });
    console.log('✓ URL이 변경되었습니다.');
  } catch (e) {
    console.log('⚠️  URL 변경 대기 중 타임아웃, 다른 방법으로 확인...');
  }

  await page.waitForTimeout(2000);

  const currentUrl = page.url();
  console.log(`현재 URL: ${currentUrl}`);

  // 로그인 실패 메시지 확인
  const errorSelectors = [
    'text=/error|잘못|incorrect|invalid|failed|fail|실패/i',
    '[role="alert"]',
    '.error',
    '.alert',
    'div[class*="error" i]',
    'span[class*="error" i]'
  ];

  let errorMessage = null;
  for (const selector of errorSelectors) {
    try {
      const element = await page.locator(selector).first();
      if (await element.isVisible({ timeout: 2000 })) {
        errorMessage = await element.textContent();
        console.log(`에러 메시지 발견 (${selector}): ${errorMessage}`);
        break;
      }
    } catch (e) {
      continue;
    }
  }
  
  if (!errorMessage) {
    const pageText = await page.evaluate(() => document.body.innerText);
    const errorPatterns = [/error/i, /잘못/i, /실패/i, /incorrect/i, /invalid/i, /failed/i];
    for (const pattern of errorPatterns) {
      if (pattern.test(pageText)) {
        const lines = pageText.split('\n').filter(line => pattern.test(line));
        if (lines.length > 0) {
          errorMessage = lines[0].trim();
          console.log(`페이지 텍스트에서 에러 발견: ${errorMessage}`);
          break;
        }
      }
    }
  }
  
  if (errorMessage && errorMessage.trim()) {
    console.error(`❌ 로그인 실패: ${errorMessage.trim()}`);
    return false;
  } else if (currentUrl.includes('console.publ.biz') && !currentUrl.includes('type=enter')) {
    console.log('✅ 로그인 성공!');
    return true;
  } else {
    const loginFormExists = await page.locator('input[name="email"]').isVisible().catch(() => false);
    if (loginFormExists) {
      console.log('⚠️  로그인 폼이 여전히 표시됩니다. 로그인 정보를 확인해주세요.');
      return false;
    } else {
      console.log('✅ 로그인 성공 가능성 높음 (로그인 폼이 사라짐)');
      return true;
    }
  }
}

/**
 * 로그인 프로세스 실행
 * @param {Page} page - Playwright Page 객체
 * @param {string} email - 이메일
 * @param {string} password - 비밀번호
 * @returns {Promise<boolean>} 로그인 성공 여부
 */
async function performLogin(page, email, password) {
  await navigateToLoginPage(page);
  await fillLoginForm(page, email, password);
  await clickLoginButton(page);
  return await verifyLoginResult(page);
}

module.exports = {
  getLoginCredentials,
  performLogin,
  navigateToLoginPage,
  fillLoginForm,
  clickLoginButton,
  verifyLoginResult
};

