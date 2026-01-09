/**
 * 브라우저를 열어두고 사용자가 수동으로 확인할 수 있도록 대기
 * @returns {Promise<void>}
 */
async function keepBrowserOpen() {
  console.log('\n브라우저를 열어둡니다. 수동으로 닫아주세요.');
  console.log('작업을 계속하려면 Ctrl+C를 눌러 스크립트를 종료하세요.');
  
  // 무한 대기 (사용자가 Ctrl+C로 종료할 때까지)
  await new Promise(() => {});
}

module.exports = {
  keepBrowserOpen
};

