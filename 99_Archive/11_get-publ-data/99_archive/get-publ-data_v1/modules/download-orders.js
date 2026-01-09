const { downloadCSVFromPage } = require('../utils/download-helpers');
const { closeKeyFeaturesPopup } = require('../utils/popup-helpers');

/**
 * 주문 목록 첫번째 페이지로 이동
 * @param {Page} page - Playwright Page 객체
 * @returns {Promise<boolean>} 페이지 도달 성공 여부
 */
async function navigateToFirstOrderPage(page) {
  const ordersBaseUrl = 'https://console.publ.biz/channels/L2NoYW5uZWxzLzE3Njkx/orders/subs-products';
  const firstPageUrl = `${ordersBaseUrl}?page=1&limit=300`;
  
  console.log('\n[4-1] 주문 목록 첫번째 페이지로 이동 중...');
  console.log(`목표 URL: ${firstPageUrl}`);
  
  try {
    await page.goto(firstPageUrl, {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });
    // 페이지 로드 후 충분한 대기 시간 (팝업이 나타날 시간 확보)
    await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(3000); // 추가 대기 시간
    
    const currentPageUrl = page.url();
    console.log(`현재 페이지: ${currentPageUrl}`);
    
    if (currentPageUrl.includes('type=enter')) {
      console.log('⚠️  로그인 세션이 만료되었습니다. 로그인을 다시 시도해주세요.');
      return false;
    } else if (!currentPageUrl.includes('orders/subs-products')) {
      console.log('⚠️  주문 목록 페이지에 도달하지 못했습니다.');
      return false;
    }
    
    console.log('✓ 첫번째 페이지에 성공적으로 도달했습니다.');
    return true;
  } catch (e) {
    console.error(`⚠️  페이지 이동 실패: ${e.message}`);
    return false;
  }
}

/**
 * 마지막 페이지 번호 찾기
 * @param {Page} page - Playwright Page 객체
 * @returns {Promise<number>} 마지막 페이지 번호 (찾지 못하면 1 반환)
 */
async function findLastPageNumber(page) {
  console.log('\n[4-2] 마지막 페이지 번호 찾는 중...');
  
  let lastPageNumber = 1;
  
  try {
    // 페이지 로드 대기
    await page.waitForTimeout(3000);
    
    // 방법 1: 특정 클래스로 페이지 번호 요소 찾기 (가장 정확한 방법)
    console.log('[방법 1] 특정 CSS 클래스로 페이지 번호 찾기...');
    const method1Result = await page.evaluate(() => {
      const classSelectors = [
        '[class*="sc-epOimh"]',
        '[class*="jJQXSN"]',
        '[class*="pagination"]',
        '[class*="page"]'
      ];
      
      const numbers = [];
      for (const selector of classSelectors) {
        const elements = Array.from(document.querySelectorAll(selector));
        for (const el of elements) {
          const text = el.textContent?.trim();
          const num = parseInt(text);
          if (!isNaN(num) && num > 0 && num < 100) {
            numbers.push(num);
          }
        }
        if (numbers.length > 0) break; // 하나라도 찾으면 중단
      }
      
      return numbers.length > 0 ? Math.max(...numbers) : null;
    });
    
    if (method1Result && method1Result > 1) {
      lastPageNumber = method1Result;
      console.log(`✓ 방법 1 성공: 마지막 페이지 번호 = ${lastPageNumber}`);
      return lastPageNumber;
    }
    
    // 방법 2: 페이지네이션 컨테이너에서 찾기
    console.log('[방법 2] 페이지네이션 컨테이너에서 찾기...');
    const method2Result = await page.evaluate(() => {
      const paginationContainers = Array.from(document.querySelectorAll(
        '[class*="pagination"], nav, [role="navigation"], [aria-label*="page" i], [aria-label*="페이지" i]'
      ));
      
      const numbers = [];
      for (const container of paginationContainers) {
        const allText = container.textContent || '';
        const numberMatches = allText.match(/\b([1-9]\d{0,2})\b/g);
        if (numberMatches) {
          for (const match of numberMatches) {
            const num = parseInt(match);
            if (num > 0 && num < 100) {
              numbers.push(num);
            }
          }
        }
      }
      
      return numbers.length > 0 ? Math.max(...numbers) : null;
    });
    
    if (method2Result && method2Result > 1) {
      lastPageNumber = method2Result;
      console.log(`✓ 방법 2 성공: 마지막 페이지 번호 = ${lastPageNumber}`);
      return lastPageNumber;
    }
    
    // 방법 3: 페이지 전체 텍스트에서 패턴 매칭 (가장 신뢰할 수 있는 방법)
    console.log('[방법 3] 페이지 텍스트에서 패턴 매칭...');
    const method3Result = await page.evaluate(() => {
      const bodyText = document.body.innerText || '';
      const patterns = [
        /페이지\s*(\d+)\s*\/\s*(\d+)/i,
        /page\s*(\d+)\s*of\s*(\d+)/i,
        /(\d+)\s*\/\s*(\d+)/,
        /총\s*(\d+)\s*페이지/i,
        /total\s*(\d+)\s*pages/i
      ];
      
      for (const pattern of patterns) {
        const match = bodyText.match(pattern);
        if (match) {
          // 마지막 숫자를 마지막 페이지로 간주
          const numbers = match.slice(1).map(n => parseInt(n)).filter(n => !isNaN(n) && n > 0 && n < 100);
          if (numbers.length > 0) {
            return Math.max(...numbers);
          }
        }
      }
      
      return null;
    });
    
    if (method3Result && method3Result > 1) {
      lastPageNumber = method3Result;
      console.log(`✓ 방법 3 성공: 마지막 페이지 번호 = ${lastPageNumber}`);
      return lastPageNumber;
    }
    
    // 방법 4: 버튼/링크에서 페이지 번호 추출 (마지막 수단)
    console.log('[방법 4] 버튼/링크에서 페이지 번호 추출...');
    const method4Result = await page.evaluate(() => {
      const clickableElements = Array.from(document.querySelectorAll('button, a, [role="button"]'));
      const numbers = [];
      
      for (const el of clickableElements) {
        const text = el.textContent?.trim();
        const href = el.href || '';
        const onclick = el.getAttribute('onclick') || '';
        
        // 텍스트에서 숫자 추출
        const textMatch = text.match(/\b([1-9]\d{0,2})\b/);
        if (textMatch) {
          const num = parseInt(textMatch[1]);
          if (num > 0 && num < 100) {
            numbers.push(num);
          }
        }
        
        // URL에서 페이지 번호 추출
        const urlMatch = (href + onclick).match(/page[=:](\d+)/i);
        if (urlMatch) {
          const num = parseInt(urlMatch[1]);
          if (num > 0 && num < 100) {
            numbers.push(num);
          }
        }
      }
      
      return numbers.length > 0 ? Math.max(...numbers) : null;
    });
    
    if (method4Result && method4Result > 1) {
      lastPageNumber = method4Result;
      console.log(`✓ 방법 4 성공: 마지막 페이지 번호 = ${lastPageNumber}`);
      return lastPageNumber;
    }
    
    console.log('⚠️  모든 방법 실패: 페이지 번호를 찾을 수 없습니다.');
    
    // 최종 검증 및 디버깅 (모든 방법이 실패한 경우에만)
    if (lastPageNumber === 1) {
      console.log('\n[상세 디버깅] 페이지 구조 분석:');
      
      const detailedInfo = await page.evaluate(() => {
        // 페이지네이션 관련 모든 요소 찾기
        const paginationElements = Array.from(document.querySelectorAll(
          '[class*="pagination"], [class*="page"], nav, [role="navigation"], button, a'
        )).slice(0, 30);
        
        return paginationElements.map((el, idx) => {
          const text = el.textContent?.trim();
          const className = el.className;
          const tag = el.tagName;
          const href = el.href || '';
          const visible = el.offsetParent !== null;
          
          return {
            index: idx,
            tag,
            text: text?.substring(0, 50) || '',
            className: className?.substring(0, 50) || '',
            href: href?.substring(0, 100) || '',
            visible
          };
        });
      });
      
      console.log('  페이지네이션 관련 요소 (최대 30개):');
      detailedInfo.forEach((info, idx) => {
        const visibleMark = info.visible ? '✓' : '✗';
        console.log(`    ${idx + 1}. [${visibleMark}] <${info.tag}> "${info.text}"`);
        if (info.className) {
          console.log(`        클래스: ${info.className}`);
        }
        if (info.href) {
          console.log(`        링크: ${info.href}`);
        }
      });
    } else {
      console.log(`\n✅ 최종 확인: 마지막 페이지 번호 = ${lastPageNumber}`);
    }
    
  } catch (e) {
    console.log(`⚠️  마지막 페이지 번호 찾기 실패: ${e.message}`);
    console.log('스택 트레이스:', e.stack);
    console.log('첫번째 페이지만 다운로드합니다.');
  }
  
  return lastPageNumber;
}

/**
 * 마지막 페이지로 이동
 * @param {Page} page - Playwright Page 객체
 * @param {number} lastPageNumber - 마지막 페이지 번호
 * @returns {Promise<boolean>} 페이지 도달 성공 여부
 */
async function navigateToLastOrderPage(page, lastPageNumber) {
  if (lastPageNumber <= 1) {
    console.log('마지막 페이지가 첫번째 페이지와 동일하므로 추가 다운로드 없음.');
    return false;
  }
  
  const ordersBaseUrl = 'https://console.publ.biz/channels/L2NoYW5uZWxzLzE3Njkx/orders/subs-products';
  const lastPageUrl = `${ordersBaseUrl}?page=${lastPageNumber}&limit=300`;
  
  console.log(`\n[4-4] 마지막 페이지(${lastPageNumber})로 이동 중...`);
  console.log(`목표 URL: ${lastPageUrl}`);
  
  try {
    await page.goto(lastPageUrl, {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });
    await page.waitForTimeout(2000);
    
    const finalUrl = page.url();
    console.log(`현재 페이지: ${finalUrl}`);
    
    // URL에서 페이지 번호 확인
    const urlPageMatch = finalUrl.match(/[?&]page=(\d+)/);
    const urlPageNumber = urlPageMatch ? parseInt(urlPageMatch[1]) : null;
    
    if (finalUrl.includes('orders/subs-products')) {
      // 페이지 번호 검증
      if (urlPageNumber === lastPageNumber) {
        console.log(`✓ 마지막 페이지(${lastPageNumber})에 성공적으로 도달했습니다.`);
        console.log(`  URL 확인: page=${urlPageNumber}`);
        
        // 추가 검증: 페이지에 더 이상 다음 페이지가 없는지 확인
        const hasNextPage = await page.evaluate(() => {
          // 다음 페이지 버튼이나 링크가 있는지 확인
          const nextButtons = Array.from(document.querySelectorAll('button, a')).filter(el => {
            const text = el.textContent?.toLowerCase() || '';
            const ariaLabel = el.getAttribute('aria-label')?.toLowerCase() || '';
            return text.includes('next') || text.includes('다음') || 
                   ariaLabel.includes('next') || ariaLabel.includes('다음') ||
                   el.disabled === false && (text.includes('>') || text.includes('→'));
          });
          return nextButtons.length > 0 && nextButtons.some(btn => !btn.disabled);
        });
        
        if (!hasNextPage) {
          console.log(`✓ 검증 완료: 이 페이지가 마지막 페이지입니다 (다음 페이지 버튼 없음).`);
        } else {
          console.log(`⚠️  주의: 다음 페이지 버튼이 보입니다. 실제 마지막 페이지가 아닐 수 있습니다.`);
        }
        
        return true;
      } else if (urlPageNumber) {
        console.log(`⚠️  경고: 목표 페이지(${lastPageNumber})와 다른 페이지(${urlPageNumber})로 이동되었습니다.`);
        console.log(`  실제 도달한 페이지: ${urlPageNumber}`);
        return true; // 여전히 유효한 페이지이므로 계속 진행
      } else {
        console.log(`✓ 주문 목록 페이지에 도달했습니다.`);
        return true;
      }
    } else {
      console.log('⚠️  마지막 페이지에 도달하지 못했습니다.');
      return false;
    }
  } catch (e) {
    console.error(`⚠️  페이지 이동 실패: ${e.message}`);
    return false;
  }
}

/**
 * 새로운 탭에서 마지막 페이지 열기
 * @param {Page} page - 현재 Page 객체 (context를 얻기 위해 사용)
 * @param {number} lastPageNumber - 마지막 페이지 번호
 * @returns {Promise<Page|null>} 새로 열린 페이지 객체 (실패 시 null)
 */
async function openLastPageInNewTab(page, lastPageNumber) {
  const ordersBaseUrl = 'https://console.publ.biz/channels/L2NoYW5uZWxzLzE3Njkx/orders/subs-products';
  const lastPageUrl = `${ordersBaseUrl}?page=${lastPageNumber}&limit=300`;
  
  console.log(`\n[4-3] 새로운 탭에서 마지막 페이지(${lastPageNumber}) 열기...`);
  console.log(`목표 URL: ${lastPageUrl}`);
  
  try {
    // 현재 페이지의 context를 가져와서 새 탭 열기
    const context = page.context();
    const newPage = await context.newPage();
    
    console.log('✓ 새 탭이 생성되었습니다.');
    
    // 새 탭에서 마지막 페이지로 이동
    await newPage.goto(lastPageUrl, {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });
    // 페이지 로드 후 충분한 대기 시간 (팝업이 나타날 시간 확보)
    await newPage.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    await newPage.waitForTimeout(3000); // 추가 대기 시간
    
    const finalUrl = newPage.url();
    console.log(`현재 페이지: ${finalUrl}`);
    
    // URL에서 페이지 번호 확인
    const urlPageMatch = finalUrl.match(/[?&]page=(\d+)/);
    const urlPageNumber = urlPageMatch ? parseInt(urlPageMatch[1]) : null;
    
    if (finalUrl.includes('orders/subs-products')) {
      if (urlPageNumber === lastPageNumber) {
        console.log(`✓ 마지막 페이지(${lastPageNumber})가 새 탭에서 성공적으로 열렸습니다.`);
        console.log(`  URL 확인: page=${urlPageNumber}`);
        return newPage;
      } else if (urlPageNumber) {
        console.log(`⚠️  경고: 목표 페이지(${lastPageNumber})와 다른 페이지(${urlPageNumber})로 이동되었습니다.`);
        console.log(`  실제 도달한 페이지: ${urlPageNumber}`);
        return newPage; // 여전히 유효한 페이지이므로 반환
      } else {
        console.log(`✓ 주문 목록 페이지가 새 탭에서 열렸습니다.`);
        return newPage;
      }
    } else {
      console.log('⚠️  마지막 페이지에 도달하지 못했습니다.');
      await newPage.close();
      return null;
    }
  } catch (e) {
    console.error(`⚠️  새 탭에서 페이지 열기 실패: ${e.message}`);
    return null;
  }
}

/**
 * 주문 목록 CSV 다운로드 프로세스 실행
 * @param {Page} page - Playwright Page 객체
 * @param {string} downloadPath - 다운로드 경로
 * @returns {Promise<boolean>} 다운로드 성공 여부
 */
async function downloadOrdersCSV(page, downloadPath) {
  console.log('\n=== 4단계: 주문 목록 CSV 파일 다운로드 시작 ===');
  
  // 4-1. 첫번째 페이지로 이동
  const navigatedToFirst = await navigateToFirstOrderPage(page);
  if (!navigatedToFirst) {
    return false;
  }
  
  // 4-2. 마지막 페이지 번호 찾기
  const lastPageNumber = await findLastPageNumber(page);
  console.log(`\n[결과] 찾은 마지막 페이지 번호: ${lastPageNumber}`);
  
  // 4-3. 새로운 탭에서 마지막 페이지 열기 (마지막 페이지가 1보다 큰 경우)
  let newPage = null;
  console.log(`\n[4-3 체크] 마지막 페이지 번호(${lastPageNumber}) 확인 중...`);
  if (lastPageNumber > 1) {
    console.log(`✓ 마지막 페이지 번호(${lastPageNumber})가 1보다 크므로 새 탭에서 마지막 페이지를 엽니다.`);
    newPage = await openLastPageInNewTab(page, lastPageNumber);
    if (newPage) {
      console.log(`✓ 마지막 페이지(${lastPageNumber})가 새 탭에서 성공적으로 열렸습니다.`);
    } else {
      console.log('⚠️  새 탭에서 마지막 페이지 열기 실패.');
    }
  } else {
    console.log(`⚠️  마지막 페이지 번호가 ${lastPageNumber}입니다.`);
    console.log('   (마지막 페이지가 1이거나 찾지 못한 경우)');
  }
  
  // 4-4. 첫번째 페이지에서 팝업 닫기
  console.log('\n[4-4] 첫번째 페이지에서 팝업 닫기 중...');
  await closeKeyFeaturesPopup(page, 10000); // 최대 10초 대기
  
  // 4-5. 첫번째 페이지에서 CSV 다운로드
  console.log('\n[4-5] 첫번째 페이지 CSV 다운로드 중...');
  // 다운로드 버튼 클릭 전에 다시 팝업 확인 및 닫기
  await closeKeyFeaturesPopup(page, 3000); // 다운로드 전에 다시 확인 (최대 3초)
  await downloadCSVFromPage(page, downloadPath, '첫번째');
  
  // 4-6. 마지막 페이지 탭에서 팝업 닫기
  if (newPage) {
    console.log('\n[4-6] 마지막 페이지 탭에서 팝업 닫기 중...');
    await closeKeyFeaturesPopup(newPage, 10000); // 최대 10초 대기
    
    // 4-7. 마지막 페이지 탭에서 CSV 다운로드
    console.log('\n[4-7] 마지막 페이지 탭에서 CSV 다운로드 중...');
    // 다운로드 버튼 클릭 전에 다시 팝업 확인 및 닫기
    await closeKeyFeaturesPopup(newPage, 3000); // 다운로드 전에 다시 확인 (최대 3초)
    await downloadCSVFromPage(newPage, downloadPath, `마지막(${lastPageNumber})`);
  }
  
  console.log('\n✅ 4단계 완료: 첫번째 페이지와 마지막 페이지에서 CSV 다운로드 완료');
  return true;
}

module.exports = {
  downloadOrdersCSV,
  navigateToFirstOrderPage,
  findLastPageNumber,
  navigateToLastOrderPage,
  openLastPageInNewTab,
  closeKeyFeaturesPopup // 호환성을 위해 export
};

