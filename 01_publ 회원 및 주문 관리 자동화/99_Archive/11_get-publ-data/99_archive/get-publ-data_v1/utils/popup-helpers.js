/**
 * "Key features" 팝업 닫기
 * @param {Page} page - Playwright Page 객체
 * @param {number} maxWaitTime - 팝업이 나타날 때까지 최대 대기 시간 (밀리초, 기본값: 10000)
 * @returns {Promise<boolean>} 팝업 닫기 성공 여부
 */
async function closeKeyFeaturesPopup(page, maxWaitTime = 10000) {
  console.log('팝업 확인 중...');
  
  try {
    // 먼저 페이지가 완전히 로드될 때까지 대기
    await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(2000); // 추가 대기 시간 (팝업이 나타날 시간)
    
    // 팝업이 나타날 때까지 반복적으로 확인 (최대 maxWaitTime 동안)
    const startTime = Date.now();
    let popupFound = false;
    const checkInterval = 1000; // 1초마다 확인
    
    while (Date.now() - startTime < maxWaitTime && !popupFound) {
      // 팝업이 있는지 확인 (여러 방법으로 시도)
      const popupSelectors = [
        // 모달/팝업 컨테이너 찾기
        '[class*="modal"]',
        '[class*="popup"]',
        '[class*="dialog"]',
        '[role="dialog"]',
        // "Key features" 텍스트가 있는 요소
        'text="Key features"',
        'text="Key features" >> ..',
        // 일반적인 닫기 버튼
        'button[aria-label*="close" i]',
        'button[aria-label*="닫기" i]',
        '[aria-label*="close" i]',
        '[aria-label*="닫기" i]',
        // X 버튼 (일반적인 패턴)
        'button:has(svg) >> near="Key features"',
        'button >> near="Key features"',
      ];
      
      // 팝업이 존재하는지 확인
      for (const selector of popupSelectors) {
        try {
          const element = await page.waitForSelector(selector, { timeout: 500, state: 'visible' });
          if (element) {
            const text = await element.textContent();
            const isVisible = await element.isVisible();
            
            // "Key features" 텍스트가 포함되어 있으면 팝업으로 간주
            if (isVisible && (text?.includes('Key features') || text?.includes('features'))) {
              popupFound = true;
              console.log(`✓ 팝업 발견: "${text?.substring(0, 50)}"`);
              break;
            }
          }
        } catch (e) {
          continue;
        }
      }
      
      // 더 포괄적인 방법: 페이지에서 "Key features" 텍스트 찾기
      if (!popupFound) {
        const hasKeyFeatures = await page.evaluate(() => {
          const allText = document.body.innerText || '';
          // "Key features" 텍스트가 있고, 보이는 요소인지 확인
          const keyFeaturesElements = Array.from(document.querySelectorAll('*')).filter(el => {
            const text = el.textContent || '';
            return (text.includes('Key features') || text.includes('Welcome!')) && 
                   el.offsetParent !== null; // 보이는 요소만
          });
          return keyFeaturesElements.length > 0;
        });
        
        if (hasKeyFeatures) {
          popupFound = true;
          console.log('✓ "Key features" 팝업이 페이지에 존재합니다.');
        }
      }
      
      // 팝업을 찾았으면 루프 종료
      if (popupFound) {
        break;
      }
      
      // 아직 팝업이 없으면 잠시 대기 후 다시 확인
      if (Date.now() - startTime < maxWaitTime) {
        await page.waitForTimeout(checkInterval);
      }
    }
    
    if (!popupFound) {
      console.log('팝업이 없습니다. 계속 진행합니다.');
      return true;
    }
    
    // 닫기 버튼 찾기 및 클릭 (여러 번 시도)
    const closeButtonSelectors = [
      // X 버튼 (일반적인 패턴)
      'button:has-text("×")',
      'button:has-text("✕")',
      'button:has-text("X")',
      '[aria-label*="close" i]',
      '[aria-label*="닫기" i]',
      // "Key features" 근처의 버튼
      'text="Key features" >> .. >> button',
      'text="Key features" >> .. >> [role="button"]',
      // 모달 내부의 닫기 버튼
      '[role="dialog"] button:has(svg)',
      '[role="dialog"] >> button >> near="Key features"',
      // 일반적인 닫기 아이콘 버튼
      'button[type="button"] >> near="Key features"',
      // IconButton 타입의 닫기 버튼
      'button[x-pds-name="IconButton"] >> near="Key features"',
    ];
    
    let closed = false;
    const maxAttempts = 3; // 최대 3번 시도
    
    for (let attempt = 1; attempt <= maxAttempts && !closed; attempt++) {
      console.log(`닫기 버튼 찾기 시도 ${attempt}/${maxAttempts}...`);
      
      for (const selector of closeButtonSelectors) {
        try {
          const closeButton = await page.waitForSelector(selector, { timeout: 2000, state: 'visible' });
          if (closeButton) {
            const isVisible = await closeButton.isVisible();
            if (isVisible) {
              await closeButton.click();
              console.log(`✓ 닫기 버튼 클릭 완료 (선택자: ${selector})`);
              await page.waitForTimeout(1500); // 팝업이 닫힐 때까지 대기
              
              // 팝업이 실제로 닫혔는지 확인
              const popupStillVisible = await page.evaluate(() => {
                const keyFeaturesElements = Array.from(document.querySelectorAll('*')).filter(el => {
                  const text = el.textContent || '';
                  return text.includes('Key features') && el.offsetParent !== null;
                });
                return keyFeaturesElements.length > 0;
              });
              
              if (!popupStillVisible) {
                closed = true;
                break;
              }
            }
          }
        } catch (e) {
          continue;
        }
      }
      
      // 버튼을 찾지 못했거나 클릭해도 닫히지 않은 경우 ESC 키 시도
      if (!closed && attempt < maxAttempts) {
        console.log(`닫기 버튼을 찾지 못했습니다. ESC 키를 시도합니다... (시도 ${attempt}/${maxAttempts})`);
        await page.keyboard.press('Escape');
        await page.waitForTimeout(1500);
        
        // 다시 확인
        const popupStillVisible = await page.evaluate(() => {
          const keyFeaturesElements = Array.from(document.querySelectorAll('*')).filter(el => {
            const text = el.textContent || '';
            return text.includes('Key features') && el.offsetParent !== null;
          });
          return keyFeaturesElements.length > 0;
        });
        
        if (!popupStillVisible) {
          closed = true;
          break;
        }
      }
    }
    
    // 최종 확인
    const popupStillVisible = await page.evaluate(() => {
      const keyFeaturesElements = Array.from(document.querySelectorAll('*')).filter(el => {
        const text = el.textContent || '';
        return text.includes('Key features') && el.offsetParent !== null;
      });
      return keyFeaturesElements.length > 0;
    });
    
    if (!popupStillVisible) {
      console.log('✓ 팝업이 성공적으로 닫혔습니다.');
      return true;
    } else {
      console.log('⚠️  팝업이 여전히 보입니다. 계속 진행합니다.');
      return false;
    }
    
  } catch (e) {
    console.log(`⚠️  팝업 닫기 중 오류 발생: ${e.message}`);
    console.log('계속 진행합니다.');
    return false;
  }
}

module.exports = {
  closeKeyFeaturesPopup
};

