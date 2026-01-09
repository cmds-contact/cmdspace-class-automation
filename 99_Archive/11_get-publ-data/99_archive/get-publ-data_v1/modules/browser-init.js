const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

/**
 * 브라우저 초기화 및 환경 설정
 * @returns {Promise<{browser: Browser, context: BrowserContext, page: Page, downloadPath: string}>}
 */
async function initializeBrowser() {
  console.log('브라우저 시작 중...');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 100,
    args: [
      '--disable-crash-reporter',
      '--disable-crashpad'
    ],
    ignoreDefaultArgs: ['--enable-automation']
  });

  // 다운로드 경로 설정
  const downloadPath = path.resolve('./downloads');
  
  // downloads 폴더가 없으면 생성
  if (!fs.existsSync(downloadPath)) {
    fs.mkdirSync(downloadPath, { recursive: true });
    console.log(`✓ downloads 폴더 생성: ${downloadPath}`);
  }
  
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    acceptDownloads: true
  });
  
  console.log('✓ 브라우저가 시작되었습니다.');
  console.log(`✓ 다운로드 경로 설정: ${downloadPath}`);

  const page = await context.newPage();
  console.log('✓ 새 페이지가 생성되었습니다.');
  
  // CDP를 통해 다운로드 경로 설정 및 브라우저 창 크기 조정
  try {
    const client = await context.newCDPSession(page);
    
    // 다운로드 설정
    await client.send('Browser.setDownloadBehavior', {
      behavior: 'allow',
      downloadPath: downloadPath
    });
    console.log('✓ 다운로드 동작 설정 완료');
    
    // 브라우저 창 크기 조정
    try {
      const targetInfo = await client.send('Browser.getWindowForTarget', { 
        targetId: page._target._targetId 
      });
      
      if (targetInfo && targetInfo.windowId) {
        await client.send('Browser.setWindowBounds', {
          windowId: targetInfo.windowId,
          bounds: { 
            width: 1280, 
            height: 800, 
            left: 0, 
            top: 0, 
            windowState: 'normal' 
          }
        });
        console.log('✓ 브라우저 창 크기 조정 완료 (1280x800)');
      }
    } catch (e) {
      console.log('⚠️  브라우저 창 크기 자동 조정 실패, 수동으로 조정해주세요');
    }
  } catch (e) {
    console.log('⚠️  CDP 설정 실패, 기본 설정 사용:', e.message);
  }

  return {
    browser,
    context,
    page,
    downloadPath
  };
}

module.exports = {
  initializeBrowser
};

