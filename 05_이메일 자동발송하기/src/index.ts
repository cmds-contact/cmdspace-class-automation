import 'dotenv/config';
import { sendEmail } from './send-email.js';

/**
 * 테스트 이메일 발송
 *
 * 사용법:
 * 1. .env.example을 복사하여 .env 파일 생성
 * 2. .env에 실제 값 입력 (RESEND_API_KEY, FROM_EMAIL, FROM_NAME)
 * 3. 아래 TEST_EMAIL을 본인 이메일로 변경
 * 4. npm run dev 실행
 */

// 테스트용 수신자 이메일 (본인 이메일로 변경하세요)
const TEST_EMAIL = 'overmensch280@gmail.com';

async function main() {
  console.log('이메일 발송 테스트를 시작합니다...\n');

  try {
    const result = await sendEmail({
      to: TEST_EMAIL,
      subject: '[테스트] Resend 이메일 발송 테스트',
      html: `
        <h1>이메일 발송 테스트</h1>
        <p>이 이메일이 정상적으로 수신되었다면 Resend 설정이 완료된 것입니다.</p>
        <hr />
        <p style="color: #666; font-size: 12px;">
          발송 시간: ${new Date().toLocaleString('ko-KR')}
        </p>
      `,
    });

    console.log('이메일 발송 성공!');
    console.log(`이메일 ID: ${result.id}`);
    console.log(`수신자: ${TEST_EMAIL}`);
  } catch (error) {
    console.error('이메일 발송 실패:', error);
    process.exit(1);
  }
}

main();
