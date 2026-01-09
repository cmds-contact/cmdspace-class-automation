const fs = require('fs');
const path = require('path');
const { closeKeyFeaturesPopup } = require('./popup-helpers');

/**
 * CSV 다운로드 헬퍼 함수
 * @param {Page} page - Playwright Page 객체
 * @param {string} downloadPath - 다운로드 경로
 * @param {string} pageLabel - 페이지 레이블 (파일명에 추가)
 * @returns {Promise<boolean>} 다운로드 성공 여부
 */
async function downloadCSVFromPage(page, downloadPath, pageLabel) {
  console.log(`다운로드 버튼 찾는 중 (${pageLabel} 페이지)...`);
  
  // 다운로드 버튼 클릭 전에 팝업이 나타났는지 확인하고 닫기
  await closeKeyFeaturesPopup(page, 2000).catch(() => {}); // 최대 2초 대기
  
  const downloadSelectors = [
    // 주문 목록 페이지의 특정 다운로드 버튼 (제공된 소스코드 기반)
    'button[x-pds-name="IconButton"]',
    'button.sc-fpAkvV.cVarYZ',
    'div.sc-irvLRx.QsASu button',
    'button.sc-fpAkvV',
    // 일반적인 다운로드 버튼
    'button:has-text("Download")',
    'button:has-text("다운로드")',
    'button:has-text("CSV")',
    'button:has-text("Excel")',
    'a:has-text("Download")',
    'a:has-text("다운로드")',
    'a:has-text("CSV")',
    '[download]',
    'button[aria-label*="download" i]',
    'button[aria-label*="export" i]',
    'a[download]'
  ];
  
  let downloadClicked = false;
  for (const selector of downloadSelectors) {
    try {
      const element = await page.waitForSelector(selector, { timeout: 3000, state: 'visible' });
      if (element) {
        const text = await element.textContent();
        const isVisible = await element.isVisible();
        
        if (!isVisible) continue;
        
        console.log(`✓ 다운로드 버튼 발견: "${text?.trim()}" (선택자: ${selector})`);
        
        await element.scrollIntoViewIfNeeded();
        await page.waitForTimeout(500);
        
        // 다운로드 버튼 클릭 직전에 다시 팝업 확인 및 닫기
        await closeKeyFeaturesPopup(page, 1000).catch(() => {}); // 최대 1초 대기
        
        // 다운로드 버튼 클릭과 동시에 팝업 모니터링 시작
        const popupMonitor = closeKeyFeaturesPopup(page, 5000).catch(() => {}); // 최대 5초 동안 팝업 모니터링
        
        const [download] = await Promise.all([
          page.waitForEvent('download', { timeout: 15000 }).catch(() => null),
          element.click()
        ]);
        
        console.log(`✓ 다운로드 버튼 클릭 완료`);
        
        // 다운로드 이벤트를 기다리는 동안 팝업 모니터링 계속
        // 클릭 후 팝업이 나타날 수 있으므로 더 긴 시간 동안 확인
        await page.waitForTimeout(1000); // 팝업이 나타날 시간 확보
        await closeKeyFeaturesPopup(page, 5000).catch(() => {}); // 최대 5초 대기 (팝업이 늦게 나타날 수 있음)
        
        // 팝업 모니터링 완료 대기
        await popupMonitor;
        
        if (download) {
          const suggestedName = download.suggestedFilename() || `download-${Date.now()}.file`;
          const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
          const fileExtension = path.extname(suggestedName);
          const fileNameWithoutExt = path.basename(suggestedName, fileExtension);
          
          // 페이지 레이블이 있으면 파일명에 추가
          const labelPart = pageLabel ? `${pageLabel}_` : '';
          const fileName = `${fileNameWithoutExt}_${labelPart}${timestamp}${fileExtension}`;
          const filePath = path.resolve(downloadPath, fileName);
          
          await download.saveAs(filePath);
          console.log(`✅ 파일 다운로드 완료: ${filePath}`);
          downloadClicked = true;
          break;
        } else {
          await page.waitForTimeout(5000);
          try {
            const files = fs.readdirSync(downloadPath);
            const recentFiles = files.filter(file => {
              const filePath = path.join(downloadPath, file);
              const stats = fs.statSync(filePath);
              return Date.now() - stats.mtimeMs < 10000;
            });
            
            if (recentFiles.length > 0) {
              console.log(`✅ 다운로드 폴더에 새 파일 발견: ${recentFiles.join(', ')}`);
              downloadClicked = true;
              break;
            }
          } catch (e) {
            // 무시
          }
        }
      }
    } catch (e) {
      continue;
    }
  }
  
  if (!downloadClicked) {
    console.log(`⚠️  ${pageLabel} 페이지에서 다운로드 버튼을 찾을 수 없습니다.`);
  }
  
  return downloadClicked;
}

/**
 * 다운로드 폴더에서 최근 파일 확인
 * @param {string} downloadPath - 다운로드 경로
 * @param {number} timeWindowMs - 확인할 시간 범위 (밀리초)
 * @returns {string[]} 최근 생성된 파일 목록
 */
function getRecentDownloadedFiles(downloadPath, timeWindowMs = 10000) {
  try {
    if (!fs.existsSync(downloadPath)) {
      return [];
    }
    
    const files = fs.readdirSync(downloadPath);
    const recentFiles = files.filter(file => {
      const filePath = path.join(downloadPath, file);
      const stats = fs.statSync(filePath);
      return Date.now() - stats.mtimeMs < timeWindowMs;
    });
    
    return recentFiles;
  } catch (e) {
    return [];
  }
}

module.exports = {
  downloadCSVFromPage,
  getRecentDownloadedFiles
};

