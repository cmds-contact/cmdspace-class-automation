# 결제 확인서 발급 사이트

## 프로젝트 개요

CMDSPACE 강의 사이트 회원 대상 결제 확인서 문서번호 발급 시스템 PoC

## 진행 상황

### 2026-01-09

#### 완료 항목

- [x] PoC 요구사항 분석
- [x] 기술 스택 결정 (Next.js 14 + Tailwind CSS + Airtable)
- [x] Airtable 테이블 구조 설계
- [x] DocumentIssuance 테이블 생성 (API로 자동 생성)
- [x] Orders 테이블에 valid_orders 뷰 추가 (사용자가 직접 생성)
- [x] Next.js 프로젝트 초기화
- [x] 타입 정의 구현
- [x] Airtable 클라이언트 구현
- [x] 문서번호 생성 로직 구현 (CPC-YYYYMM-XXX)
- [x] API Route 구현 (POST /api/issue-document)
- [x] 프론트엔드 폼 컴포넌트 구현
- [x] 로컬 테스트 완료

#### 테스트 결과

| 테스트 케이스 | 결과 |
|--------------|------|
| 유효한 주문 - 신규 발급 | 성공 (CPC-202601-001) |
| 동일 주문 재요청 | 성공 (기존 문서번호 반환) |
| 잘못된 정보 입력 | 성공 (에러 메시지 표시) |

### 미완료 항목

- [ ] Vercel 배포
- [ ] 도메인 연결
- [ ] UI/UX 개선 (필요시)

## 기술 스택

- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Airtable

## 주요 로직

```
사용자 입력 (이메일, 성함, 주문번호, 수령용 이메일)
    ↓
Orders 테이블 valid_orders 뷰에서 조회
    ↓
3개 필드 모두 일치 확인 (Order Number, E-mail, Name)
    ↓
기존 문서번호 있으면 → 기존 번호 반환
없으면 → 신규 문서번호 생성 (CPC-YYYYMM-XXX)
    ↓
DocumentIssuance 테이블에 기록
    ↓
결과 반환
```

## 실행 방법

```bash
# 의존성 설치
npm install

# 개발 서버 실행 (포트 3001)
npm run dev -- -p 3001

# 접속
http://localhost:3001
```

## 환경 변수

`.env` 파일에 설정됨:
- AIRTABLE_API_KEY
- AIRTABLE_BASE_ID

## 관련 문서

- README.md - 영문 개발 문서
- PoC 요구사항 문서 (사용자 제공)

## 비고

- PoC 범위: 입력 → 검증 → 문서번호 발급
- PDF 생성은 별도 프로젝트에서 처리
- 이메일 발송 기능 미포함
