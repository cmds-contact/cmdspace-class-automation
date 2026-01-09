# 4단계 통합 가이드

이 가이드는 `login.js`에 4단계(주문 목록 CSV 다운로드) 기능을 추가하는 방법을 설명합니다.

## 📋 통합 단계

### 1단계: 헬퍼 함수 추가

`login.js` 파일의 5줄 (`require('dotenv').config();` 다음)에 다음 헬퍼 함수를 추가하세요:

```javascript
// CSV 다운로드 헬퍼 함수
async function downloadCSVFromPage(page, downloadPath, pageLabel) {
  console.log(`다운로드 버튼 찾는 중 (${pageLabel} 페이지)...`);
  
  const downloadSelectors = [
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
        
        const [download] = await Promise.all([
          page.waitForEvent('download', { timeout: 15000 }).catch(() => null),
          element.click()
        ]);
        
        console.log(`✓ 다운로드 버튼 클릭 완료`);
        
        if (download) {
          const suggestedName = download.suggestedFilename() || `download-${Date.now()}.file`;
          const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
          const fileExtension = path.extname(suggestedName);
          const fileNameWithoutExt = path.basename(suggestedName, fileExtension);
          const fileName = `${fileNameWithoutExt}_${pageLabel}_${timestamp}${fileExtension}`;
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
```

### 2단계: 4단계 로직 추가

`login.js` 파일의 552줄 (3단계 완료 후, 브라우저 유지 전)에 다음 코드를 추가하세요:

```javascript
    // 4단계: 주문 목록 첫번째 페이지와 마지막 페이지의 CSV 다운로드
    if (currentUrl.includes('console.publ.biz') && !currentUrl.includes('type=enter')) {
      console.log('\n=== 4단계: 주문 목록 CSV 다운로드 시작 ===');
      
      try {
        const ordersBaseUrl = 'https://console.publ.biz/channels/L2NoYW5uZWxzLzE3Njkx/orders/subs-products';
        const firstPageUrl = `${ordersBaseUrl}?page=1&limit=300`;
        
        // 4-1. 첫번째 페이지로 이동
        console.log('\n[4-1] 주문 목록 첫번째 페이지로 이동 중...');
        console.log(`목표 URL: ${firstPageUrl}`);
        
        await page.goto(firstPageUrl, {
          waitUntil: 'domcontentloaded',
          timeout: 30000
        });
        await page.waitForTimeout(2000);
        
        const currentPageUrl = page.url();
        console.log(`현재 페이지: ${currentPageUrl}`);
        
        if (currentPageUrl.includes('type=enter')) {
          console.log('⚠️  로그인 세션이 만료되었습니다. 로그인을 다시 시도해주세요.');
        } else if (!currentPageUrl.includes('orders/subs-products')) {
          console.log('⚠️  주문 목록 페이지에 도달하지 못했습니다.');
        } else {
          console.log('✓ 첫번째 페이지에 성공적으로 도달했습니다.');
          
          // 4-2. 마지막 페이지 번호 찾기
          console.log('\n[4-2] 마지막 페이지 번호 찾는 중...');
          
          let lastPageNumber = 1;
          try {
            // class="sc-epOimh jJQXSN" 요소 찾기
            const pageNumberSelectors = [
              '.sc-epOimh.jJQXSN',
              '[class*="sc-epOimh"][class*="jJQXSN"]',
              '.sc-epOimh',
              '[class*="sc-epOimh"]'
            ];
            
            let pageNumberElement = null;
            for (const selector of pageNumberSelectors) {
              try {
                pageNumberElement = await page.waitForSelector(selector, { timeout: 5000, state: 'visible' });
                if (pageNumberElement) {
                  console.log(`✓ 페이지 번호 요소 발견: ${selector}`);
                  break;
                }
              } catch (e) {
                continue;
              }
            }
            
            if (pageNumberElement) {
              // 페이지의 모든 페이지 번호 요소 찾기
              const pageNumbers = await page.evaluate(() => {
                const elements = Array.from(document.querySelectorAll('[class*="sc-epOimh"], [class*="jJQXSN"]'));
                const numbers = [];
                elements.forEach(el => {
                  const text = el.textContent?.trim();
                  const num = parseInt(text);
                  if (!isNaN(num) && num > 0) {
                    numbers.push(num);
                  }
                });
                return numbers;
              });
              
              if (pageNumbers.length > 0) {
                lastPageNumber = Math.max(...pageNumbers);
                console.log(`✓ 발견된 페이지 번호들: ${pageNumbers.join(', ')}`);
                console.log(`✓ 마지막 페이지 번호: ${lastPageNumber}`);
              } else {
                // 대안: 페이지네이션 요소에서 찾기
                const paginationInfo = await page.evaluate(() => {
                  // 페이지네이션 관련 텍스트 찾기
                  const allText = document.body.innerText;
                  const pageMatch = allText.match(/페이지\s*(\d+)\s*\/\s*(\d+)/i) || 
                                   allText.match(/page\s*(\d+)\s*of\s*(\d+)/i) ||
                                   allText.match(/(\d+)\s*\/\s*(\d+)/);
                  if (pageMatch) {
                    return parseInt(pageMatch[pageMatch.length - 1]);
                  }
                  return null;
                });
                
                if (paginationInfo) {
                  lastPageNumber = paginationInfo;
                  console.log(`✓ 페이지네이션에서 마지막 페이지 번호 발견: ${lastPageNumber}`);
                } else {
                  console.log('⚠️  마지막 페이지 번호를 찾을 수 없습니다. 첫번째 페이지만 다운로드합니다.');
                }
              }
            } else {
              console.log('⚠️  페이지 번호 요소를 찾을 수 없습니다. 첫번째 페이지만 다운로드합니다.');
            }
          } catch (e) {
            console.log(`⚠️  마지막 페이지 번호 찾기 실패: ${e.message}`);
            console.log('첫번째 페이지만 다운로드합니다.');
          }
          
          // 4-3. 첫번째 페이지 CSV 다운로드
          console.log('\n[4-3] 첫번째 페이지 CSV 다운로드 중...');
          await downloadCSVFromPage(page, downloadPath, '첫번째');
          
          // 4-4. 마지막 페이지로 이동 및 다운로드 (마지막 페이지가 1이 아닌 경우)
          if (lastPageNumber > 1) {
            console.log(`\n[4-4] 마지막 페이지(${lastPageNumber})로 이동 중...`);
            const lastPageUrl = `${ordersBaseUrl}?page=${lastPageNumber}&limit=300`;
            console.log(`목표 URL: ${lastPageUrl}`);
            
            await page.goto(lastPageUrl, {
              waitUntil: 'domcontentloaded',
              timeout: 30000
            });
            await page.waitForTimeout(2000);
            
            const finalUrl = page.url();
            console.log(`현재 페이지: ${finalUrl}`);
            
            if (finalUrl.includes('orders/subs-products')) {
              console.log(`✓ 마지막 페이지(${lastPageNumber})에 성공적으로 도달했습니다.`);
              console.log('\n[4-5] 마지막 페이지 CSV 다운로드 중...');
              await downloadCSVFromPage(page, downloadPath, `마지막(${lastPageNumber})`);
            } else {
              console.log('⚠️  마지막 페이지에 도달하지 못했습니다.');
            }
          } else {
            console.log('마지막 페이지가 첫번째 페이지와 동일하므로 추가 다운로드 없음.');
          }
          
          console.log('\n✅ 4단계 완료: 주문 목록 CSV 다운로드 완료');
        }
      } catch (e) {
        console.error(`⚠️  4단계 실패: ${e.message}`);
        console.error('스택:', e.stack);
      }
    }
```

## 📍 정확한 위치

1. **헬퍼 함수**: `login.js`의 5줄 다음 (6줄 위치)
2. **4단계 로직**: `login.js`의 552줄 다음 (3단계 완료 후, 브라우저 유지 전)

## ✅ 확인 사항

통합 후 다음을 확인하세요:

1. 코드 구문 오류가 없는지 확인
2. `downloadPath` 변수가 사용 가능한지 확인 (이미 3단계에서 사용 중이므로 문제 없음)
3. `currentUrl` 변수가 사용 가능한지 확인 (이미 3단계에서 사용 중이므로 문제 없음)

## 🧪 테스트

통합 후 다음 명령어로 테스트하세요:

```bash
npm run login
```

또는

```bash
node login.js
```

## 📝 참고

- 전체 코드는 `step4-orders-download.js` 파일에도 있습니다.
- 자세한 워크플로우는 `WORKFLOW.md` 파일의 4단계 섹션을 참조하세요.

