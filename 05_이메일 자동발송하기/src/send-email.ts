import { Resend } from 'resend';
import type { EmailOptions, EmailResult } from './types.js';

// 환경변수 검증
function getEnvVar(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`환경변수 ${name}이(가) 설정되지 않았습니다.`);
  }
  return value;
}

// Resend 클라이언트 초기화 (lazy)
let resendClient: Resend | null = null;

function getResendClient(): Resend {
  if (!resendClient) {
    const apiKey = getEnvVar('RESEND_API_KEY');
    resendClient = new Resend(apiKey);
  }
  return resendClient;
}

/**
 * 이메일 발송 함수
 * @param options - 이메일 발송 옵션
 * @returns 발송 결과 (이메일 ID)
 */
export async function sendEmail(options: EmailOptions): Promise<EmailResult> {
  const resend = getResendClient();
  const fromEmail = getEnvVar('FROM_EMAIL');
  const fromName = getEnvVar('FROM_NAME');

  const { data, error } = await resend.emails.send({
    from: `${fromName} <${fromEmail}>`,
    to: options.to,
    subject: options.subject,
    html: options.html,
    text: options.text,
    replyTo: options.replyTo,
  });

  if (error) {
    throw new Error(`이메일 발송 실패: ${error.message}`);
  }

  if (!data?.id) {
    throw new Error('이메일 발송 결과를 받지 못했습니다.');
  }

  return { id: data.id };
}

/**
 * 여러 수신자에게 개별 이메일 발송
 * @param recipients - 수신자 목록
 * @param options - 이메일 옵션 (to 제외)
 * @returns 각 수신자별 발송 결과
 */
export async function sendBulkEmails(
  recipients: string[],
  options: Omit<EmailOptions, 'to'>
): Promise<{ email: string; result: EmailResult | Error }[]> {
  const results = await Promise.allSettled(
    recipients.map((email) =>
      sendEmail({ ...options, to: email })
    )
  );

  return recipients.map((email, index) => {
    const result = results[index];
    return {
      email,
      result: result.status === 'fulfilled'
        ? result.value
        : result.reason as Error,
    };
  });
}
