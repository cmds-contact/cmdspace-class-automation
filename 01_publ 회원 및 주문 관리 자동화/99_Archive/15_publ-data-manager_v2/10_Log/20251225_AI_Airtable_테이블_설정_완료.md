---
created: 2025-12-25T17:45
modified: 2025-12-25T17:45
---

## Summary

publ-data-manager v2 프로젝트의 Airtable 테이블 구조를 API로 자동 생성하고, 전체 기획을 수립함.

## Why (왜)

#### 배경

- v1은 Supabase에만 데이터 동기화
- 주문/환불 데이터가 분리되어 반품 여부 파악 어려움
- Airtable의 Linked Records로 데이터 관계 시각화 필요

#### 목적

1. 주문 목록에서 반품 여부 즉시 확인 (is_refunded 필드)
2. Supabase → Airtable 동기화
3. Member ↔ Order ↔ Refund 관계 연결

## What (무엇을)

#### 작업 항목

**완료된 작업:**
- [x] v1 코드베이스 분석
- [x] 반품 구별 로직 상세 설계
- [x] 정합성 체크 자동화 설계 (10회 실행마다)
- [x] Airtable Base 연결 (publ Data Manager)
- [x] Airtable 테이블 3개 생성 (Members, Orders, Refunds)
- [x] 모든 CSV 필드 매핑 완료
- [x] Linked Records 연결 완료

**대기 중인 작업:**
- [ ] Supabase `publ-order-db`에 `is_refunded` 컬럼 추가
- [ ] `syncer.py` 수정 - 신규 환불 시 Orders 업데이트
- [ ] `check_integrity()` 함수 추가
- [ ] `main.py` 정합성 체크 자동화
- [ ] `.env`, `config.py` Airtable 설정 추가
- [ ] `airtable_syncer.py` 모듈 개발
- [ ] 초기 데이터 마이그레이션

#### 결과물

**Airtable 테이블 구조:**

```
Members (11 fields)
├── Member Code (Primary)
├── Username
├── E-mail
├── Country
├── Name
├── Gender
├── Birth year
├── Personal email address
├── Mobile number
├── Sign-up Date
└── Orders (Link → Orders)

Orders (13 fields)
├── Order Number (Primary)
├── Product name
├── Type
├── Price (₩)
├── Name
├── E-mail
├── Member Code
├── Date and Time of Payment
├── Payment Type
├── Payment Method
├── is_refunded (checkbox)
├── Member (Link → Members)
└── Refund (Link → Refunds)

Refunds (7 fields)
├── Order Number (Primary)
├── Refund Status (Refunded/Rejected)
├── Refund Request Price (₩)
├── Username
├── Member Code
├── Refund Request Date
└── Orders (Link → Orders)
```

**Airtable 연결 정보:**
- Base ID: `appEMKRma7uMq1ioU`
- Base Name: publ Data Manager
- Tables: Members, Orders, Refunds

## How (어떻게)

#### 진행 방법

1. **기획 단계**
   - v1 코드 분석 (downloader.py, syncer.py, config.py)
   - CSV 필드 구조 파악
   - 반품 구별 워크플로우 설계
   - 효율적인 증분 처리 방식 결정

2. **Airtable 설정**
   - Airtable Web API로 테이블 자동 생성
   - Create table / Create field 엔드포인트 활용
   - Linked Records (multipleRecordLinks) 자동 연결

3. **동기화 흐름 설계**
   ```
   CSV → Supabase (처리) → Airtable (동기화)
   ```
   - Supabase가 Single Source of Truth
   - is_refunded 처리 후 Airtable로 동기화

#### 핵심 설계 결정

**반품 처리 워크플로우:**
```
1. Orders 신규 업데이트 (is_refunded = false)
2. Refunds 신규 업데이트
3. 신규 Refunded → 해당 Order is_refunded = true
4. 정합성 체크 (10회마다 자동)
```

**정합성 체크:**
- 누락 방지를 위한 안전장치
- 매 10회 실행마다 전체 비교
- `.run_counter` 파일로 실행 횟수 추적

#### 진행 상태

진행중 (Airtable 설정 완료, 코드 구현 대기)

---

## 참고

- 기획 문서: `10_Log/20251225_AI_publ_data_manager_v2_기획.md`
- 코드베이스: `20_Codebase/`
