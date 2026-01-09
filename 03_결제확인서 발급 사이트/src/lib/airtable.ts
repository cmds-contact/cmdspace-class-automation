import { DocumentIssuanceRecord, AirtableRecord } from '@/types';

const AIRTABLE_API_KEY = process.env.AIRTABLE_API_KEY!;
const AIRTABLE_BASE_ID = process.env.AIRTABLE_BASE_ID!;
const ORDERS_TABLE = 'Orders';
const ORDERS_VIEW = 'valid_orders';
const DOCUMENT_ISSUANCE_TABLE = 'DocumentIssuance';

const BASE_URL = `https://api.airtable.com/v0/${AIRTABLE_BASE_ID}`;

interface OrderRecord extends AirtableRecord {
  fields: {
    'Order Number': string;
    'E-mail': string;
    'Name': string;
    [key: string]: unknown;
  };
}

async function airtableRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${AIRTABLE_API_KEY}`,
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.error?.message || `Airtable API error: ${response.status}`);
  }

  return response.json();
}

/**
 * Orders 테이블의 valid_orders 뷰에서 유효한 주문을 조회합니다.
 * Order Number, E-mail, Name이 모두 정확히 일치해야 합니다.
 */
export async function findValidOrder(
  email: string,
  name: string,
  orderNumber: string
): Promise<OrderRecord | null> {
  // Orders 테이블의 valid_orders 뷰에서 3개 필드 모두 일치하는 레코드 조회
  const filterFormula = `AND({Order Number} = '${escapeAirtableValue(orderNumber)}', {E-mail} = '${escapeAirtableValue(email)}', {Name} = '${escapeAirtableValue(name)}')`;

  const params = new URLSearchParams({
    filterByFormula: filterFormula,
    maxRecords: '1',
    view: ORDERS_VIEW,
  });

  const result = await airtableRequest<{ records: OrderRecord[] }>(
    `/${ORDERS_TABLE}?${params}`
  );

  return result.records[0] || null;
}

/**
 * 주문번호로 기존 문서번호를 조회합니다.
 */
export async function findExistingDocument(
  orderNumber: string
): Promise<DocumentIssuanceRecord | null> {
  const filterFormula = `{order_number} = '${escapeAirtableValue(orderNumber)}'`;

  const params = new URLSearchParams({
    filterByFormula: filterFormula,
    maxRecords: '1',
  });

  const result = await airtableRequest<{ records: DocumentIssuanceRecord[] }>(
    `/${DOCUMENT_ISSUANCE_TABLE}?${params}`
  );

  return result.records[0] || null;
}

/**
 * 해당 월의 마지막 문서번호를 조회합니다.
 */
export async function getLastDocumentNumber(yearMonth: string): Promise<number> {
  const prefix = `CPC-${yearMonth}-`;
  const filterFormula = `FIND('${prefix}', {document_number}) = 1`;

  const params = new URLSearchParams();
  params.append('filterByFormula', filterFormula);
  params.append('maxRecords', '1');
  params.append('sort[0][field]', 'document_number');
  params.append('sort[0][direction]', 'desc');
  params.append('fields[]', 'document_number');

  const result = await airtableRequest<{ records: DocumentIssuanceRecord[] }>(
    `/${DOCUMENT_ISSUANCE_TABLE}?${params}`
  );

  if (result.records.length === 0) {
    return 0;
  }

  const lastDocNumber = result.records[0].fields.document_number;
  const match = lastDocNumber.match(/CPC-\d{6}-(\d{3})/);
  return match ? parseInt(match[1], 10) : 0;
}

/**
 * 문서 발급 정보를 저장합니다.
 */
export async function createDocumentRecord(
  documentNumber: string,
  orderNumber: string,
  inputEmail: string,
  inputName: string,
  deliveryEmail: string
): Promise<DocumentIssuanceRecord> {
  const result = await airtableRequest<{ records: DocumentIssuanceRecord[] }>(
    `/${DOCUMENT_ISSUANCE_TABLE}`,
    {
      method: 'POST',
      body: JSON.stringify({
        records: [
          {
            fields: {
              document_number: documentNumber,
              order_number: orderNumber,
              input_email: inputEmail,
              input_name: inputName,
              delivery_email: deliveryEmail,
              issued_at: new Date().toISOString(),
            },
          },
        ],
      }),
    }
  );

  return result.records[0];
}

/**
 * Airtable filterByFormula에 사용할 값을 이스케이프합니다.
 */
function escapeAirtableValue(value: string): string {
  return value.replace(/'/g, "\\'");
}
