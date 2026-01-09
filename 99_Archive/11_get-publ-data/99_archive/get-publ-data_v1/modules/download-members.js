const { downloadCSVFromPage } = require('../utils/download-helpers');

/**
 * 회원 정보 페이지로 이동
 * @param {Page} page - Playwright Page 객체
 * @returns {Promise<boolean>} 페이지 도달 성공 여부
 */
async function navigateToMembersPage(page) {
  const targetUrl = 'https://console.publ.biz/channels/L2NoYW5uZWxzLzE3Njkx/members/registered-users';
  
  console.log('\n지정된 페이지로 이동 중...');
  console.log(`목표 URL: ${targetUrl}`);
  
  try {
    await page.goto(targetUrl, {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });
    await page.waitForTimeout(2000);
    
    const finalUrl = page.url();
    console.log(`현재 페이지: ${finalUrl}`);
    
    // 로그인 페이지로 리다이렉트되었는지 확인
    if (finalUrl.includes('type=enter') || finalUrl === 'https://console.publ.biz/') {
      console.log('⚠️  로그인 세션이 만료되었거나 페이지 접근 권한이 없습니다.');
      console.log('로그인 상태를 확인해주세요.');
      return false;
    } else if (!finalUrl.includes('registered-users')) {
      console.log('⚠️  페이지가 예상과 다릅니다. 재시도 중...');
      await page.waitForTimeout(2000);
      await page.goto(targetUrl, { 
        waitUntil: 'domcontentloaded', 
        timeout: 30000 
      });
      await page.waitForTimeout(3000);
      
      const checkUrl = page.url();
      if (!checkUrl.includes('registered-users') && !checkUrl.includes('type=enter')) {
        console.log('⚠️  목표 페이지에 도달하지 못했습니다. 다운로드를 건너뜁니다.');
        return false;
      } else if (checkUrl.includes('type=enter')) {
        console.log('⚠️  로그인 페이지로 리다이렉트되었습니다. 로그인을 다시 시도해주세요.');
        return false;
      }
    }
    
    console.log('✓ 목표 페이지에 성공적으로 도달했습니다.');
    console.log('✓ 목표 페이지 확인 완료. 다운로드 버튼을 찾습니다.');
    return true;
  } catch (e) {
    console.error(`⚠️  페이지 이동 실패: ${e.message}`);
    return false;
  }
}

/**
 * 다운로드 버튼 찾기 및 클릭 (상세 분석)
 * @param {Page} page - Playwright Page 객체
 * @param {string} downloadPath - 다운로드 경로
 * @returns {Promise<boolean>} 다운로드 성공 여부
 */
async function findAndClickDownloadButton(page, downloadPath) {
  console.log('\n다운로드 버튼 찾는 중...');
  
  // 먼저 페이지의 모든 요소 확인
  const pageInfo = await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button, a, [role="button"]')).map(el => ({
      tag: el.tagName,
      text: el.textContent?.trim().substring(0, 100),
      innerText: el.innerText?.trim().substring(0, 100),
      href: el.href || null,
      download: el.hasAttribute('download'),
      onclick: el.onclick ? '있음' : null,
      className: el.className,
      id: el.id,
      ariaLabel: el.getAttribute('aria-label'),
      visible: el.offsetParent !== null
    }));
    return { buttons, title: document.title, url: window.location.href };
  });
  
  console.log(`페이지 제목: ${pageInfo.title}`);
  console.log(`페이지 URL: ${pageInfo.url}`);
  console.log(`\n발견된 버튼/링크 수: ${pageInfo.buttons.length}`);
  
  // 다운로드 관련 키워드로 필터링
  const downloadKeywords = ['download', '다운로드', 'export', '내보내기', 'csv', 'excel', 'xlsx', 'xls'];
  const potentialDownloadButtons = pageInfo.buttons.filter(btn => 
    downloadKeywords.some(keyword => 
      (btn.text && btn.text.toLowerCase().includes(keyword.toLowerCase())) ||
      (btn.innerText && btn.innerText.toLowerCase().includes(keyword.toLowerCase())) ||
      (btn.ariaLabel && btn.ariaLabel.toLowerCase().includes(keyword.toLowerCase())) ||
      btn.download
    )
  );
  
  if (potentialDownloadButtons.length > 0) {
    console.log('\n다운로드 가능한 버튼 발견:');
    potentialDownloadButtons.forEach((btn, index) => {
      console.log(`  ${index + 1}. [${btn.tag}] "${btn.text || btn.innerText}" (visible: ${btn.visible})`);
    });
  }
  
  // downloadCSVFromPage 함수 사용
  const success = await downloadCSVFromPage(page, downloadPath, '');
  
  if (!success) {
    console.log('\n⚠️  다운로드 버튼을 찾을 수 없습니다.');
    console.log('\n페이지의 주요 버튼/링크 목록 (최대 30개):');
    pageInfo.buttons.slice(0, 30).forEach((item, index) => {
      const text = item.text || item.innerText || '(텍스트 없음)';
      const visible = item.visible ? '✓' : '✗';
      console.log(`  ${index + 1}. [${visible}] [${item.tag}] ${text.substring(0, 50)}`);
    });
    
    console.log('\n💡 수동으로 다운로드 버튼을 클릭해주세요. 브라우저가 열려있습니다.');
  }
  
  return success;
}

/**
 * 회원 정보 CSV 다운로드 프로세스 실행
 * @param {Page} page - Playwright Page 객체
 * @param {string} downloadPath - 다운로드 경로
 * @returns {Promise<boolean>} 다운로드 성공 여부
 */
async function downloadMembersCSV(page, downloadPath) {
  console.log('\n=== 3단계: 회원 정보 CSV 파일 다운로드 시작 ===');
  
  const navigated = await navigateToMembersPage(page);
  if (!navigated) {
    return false;
  }
  
  const downloaded = await findAndClickDownloadButton(page, downloadPath);
  
  if (downloaded) {
    console.log('\n✅ 3단계 완료: 회원 정보 CSV 다운로드 완료');
  } else {
    console.log('\n⚠️  3단계 완료: 회원 정보 CSV 다운로드 실패');
  }
  
  return downloaded;
}

module.exports = {
  downloadMembersCSV,
  navigateToMembersPage,
  findAndClickDownloadButton
};

