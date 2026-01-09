import { getLastDocumentNumber } from './airtable';

/**
 * 새로운 문서번호를 생성합니다.
 * 형식: CPC-YYYYMM-XXX (예: CPC-202601-001)
 */
export async function generateDocumentNumber(): Promise<string> {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const yearMonth = `${year}${month}`;

  // 해당 월의 마지막 문서번호 조회
  const lastNumber = await getLastDocumentNumber(yearMonth);
  const nextNumber = lastNumber + 1;

  // 3자리 숫자로 패딩
  const paddedNumber = String(nextNumber).padStart(3, '0');

  return `CPC-${yearMonth}-${paddedNumber}`;
}
