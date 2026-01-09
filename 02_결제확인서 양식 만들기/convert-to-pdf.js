const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function convertHtmlToPdf() {
  const htmlFile = path.join(__dirname, 'payment_confirmation_bilingual_v0.5.html');
  const outputFile = path.join(__dirname, 'payment_confirmation_bilingual_v0.5.pdf');

  // HTML 파일 존재 확인
  if (!fs.existsSync(htmlFile)) {
    console.error('HTML 파일을 찾을 수 없습니다:', htmlFile);
    process.exit(1);
  }

  console.log('PDF 변환을 시작합니다...');
  
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    const page = await browser.newPage();
    
    // HTML 파일을 로드
    await page.goto(`file://${htmlFile}`, {
      waitUntil: 'networkidle0'
    });

    // PDF 생성
    await page.pdf({
      path: outputFile,
      format: 'A4',
      printBackground: true,
      margin: {
        top: '0',
        right: '0',
        bottom: '0',
        left: '0'
      }
    });

    console.log('PDF 변환이 완료되었습니다:', outputFile);
  } catch (error) {
    console.error('PDF 변환 중 오류가 발생했습니다:', error);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

convertHtmlToPdf();

