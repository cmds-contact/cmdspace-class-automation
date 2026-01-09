import { NextRequest, NextResponse } from 'next/server';
import { IssueDocumentRequest, ApiResponse } from '@/types';
import { findValidOrder, findExistingDocument, createDocumentRecord } from '@/lib/airtable';
import { generateDocumentNumber } from '@/lib/document-number';

export async function POST(request: NextRequest): Promise<NextResponse<ApiResponse>> {
  try {
    // 1. 요청 본문 파싱
    const body: IssueDocumentRequest = await request.json();
    const { email, name, orderNumber, deliveryEmail } = body;

    // 2. 입력값 검증
    if (!email || !name || !orderNumber || !deliveryEmail) {
      return NextResponse.json(
        {
          success: false,
          error: '입력 정보를 확인해 주세요.',
          code: 'VALIDATION_ERROR',
        },
        { status: 400 }
      );
    }

    // 이메일 형식 검증
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email) || !emailRegex.test(deliveryEmail)) {
      return NextResponse.json(
        {
          success: false,
          error: '올바른 이메일 형식을 입력해 주세요.',
          code: 'VALIDATION_ERROR',
        },
        { status: 400 }
      );
    }

    // 3. Airtable에서 유효한 주문 조회
    const validOrder = await findValidOrder(email, name, orderNumber);

    if (!validOrder) {
      return NextResponse.json(
        {
          success: false,
          error: '일치하는 주문을 찾지 못했습니다. 입력 정보를 다시 확인해 주세요.',
          code: 'NOT_FOUND',
        },
        { status: 404 }
      );
    }

    // 4. 기존 문서번호 확인
    const existingDocument = await findExistingDocument(orderNumber);

    if (existingDocument) {
      // 기존 문서번호 재사용
      return NextResponse.json({
        success: true,
        documentNumber: existingDocument.fields.document_number,
        issuedAt: existingDocument.fields.issued_at,
        isNewlyIssued: false,
      });
    }

    // 5. 새 문서번호 생성
    const documentNumber = await generateDocumentNumber();
    const issuedAt = new Date().toISOString();

    // 6. 문서 발급 정보 저장
    await createDocumentRecord(
      documentNumber,
      orderNumber,
      email,
      name,
      deliveryEmail
    );

    // 7. 성공 응답
    return NextResponse.json({
      success: true,
      documentNumber,
      issuedAt,
      isNewlyIssued: true,
    });

  } catch (error) {
    console.error('Document issuance error:', error);

    // Airtable 관련 에러인지 확인
    const isAirtableError = error instanceof Error &&
      error.message.includes('Airtable');

    return NextResponse.json(
      {
        success: false,
        error: isAirtableError
          ? '서비스 연결에 문제가 발생했습니다. 잠시 후 다시 시도해 주세요.'
          : '서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.',
        code: isAirtableError ? 'AIRTABLE_ERROR' : 'INTERNAL_ERROR',
      },
      { status: 500 }
    );
  }
}
