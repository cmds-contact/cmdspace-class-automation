/**
 * 이메일 발송 옵션 타입
 */
export interface EmailOptions {
  /** 수신자 이메일 (단일 또는 배열) */
  to: string | string[];
  /** 이메일 제목 */
  subject: string;
  /** HTML 본문 */
  html: string;
  /** 텍스트 본문 (선택) */
  text?: string;
  /** 회신 주소 (선택) */
  replyTo?: string;
}

/**
 * 이메일 발송 결과 타입
 */
export interface EmailResult {
  /** Resend에서 반환한 이메일 ID */
  id: string;
}

/**
 * 환경변수 타입
 */
export interface EnvConfig {
  RESEND_API_KEY: string;
  FROM_EMAIL: string;
  FROM_NAME: string;
}
