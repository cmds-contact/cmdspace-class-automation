# Changelog

All notable changes to this project will be documented in this file.

---

## [2.2.0] - 2026-01-01

### Summary
Orders-MemberProducts Linked Record 연결 추가. 구독 상태 계산을 Airtable Formula로 이관.

### Added

#### New Functions (airtable_syncer.py)
- `get_existing_member_products()`: MemberProducts Code로 기존 레코드 조회
- `update_orders_member_products_link()`: Orders에 MemberProducts Linked Record 연결

#### New Field (Orders Table)
- **MemberProducts**: MemberProducts 테이블 Linked Record
  - 형식: `{Member Code}_{Product name}`으로 연결

### Changed

#### airtable_syncer.py
- `sync_member_products_to_airtable()`: 신규 레코드 생성만 담당
  - 구독 상태/만료일 계산 로직 제거 (Airtable Formula로 이관)
  - 기존 레코드 업데이트 로직 제거
  - 반환값: `{'new': int}` (기존: `{'new': int, 'updated': int}`)

- `sync_all_to_airtable()`: 동기화 순서 변경
  - 기존: Members → Orders → Products → MemberProducts → Refunds
  - 변경: Members → Orders → Products → MemberProducts → **Orders(연결)** → Refunds

#### utils.py
- `calculate_subscription_status()`: **[DEPRECATED]**
  - 호출 시 DeprecationWarning 발생
  - Airtable Formula 사용 권장

### Deprecated
- `calculate_subscription_status()` (utils.py)
  - Airtable Formula로 대체됨
  - 향후 버전에서 제거 예정

### Technical Details

#### MemberProducts Code 형식
```
{Member Code}_{Product name}
예: ABC123_KM-CMDS-OBM-ME-1
```

#### 동기화 순서 (변경 후)
```
1. Members
2. Orders (신규 추가, Member 연결)
3. Products
4. MemberProducts (신규 생성만)
5. Orders (MemberProducts 연결 업데이트)  ← 추가
6. Refunds
```

#### Airtable 수동 설정 필요
1. Orders 테이블: `MemberProducts` Linked Record 필드 추가
2. MemberProducts 테이블: Subscription Status, Expiry Date를 Formula로 변경

---

## [2.1.0] - 2024-12-30

### Summary
회원별 강의/구독 상태 관리 기능 추가. Products 및 MemberProducts 테이블을 통해 구독 상태 자동 계산 및 첫 구매 안내 관리 가능.

### Added

#### New Tables (Airtable)
- **Products**: 상품 마스터 테이블
  - Product Code (고유키)
  - Display Name (표시용 상품명)
  - Is Subscription (구독 상품 여부, 자동 판별)
  - Subscription Days (구독 기간, 수동 입력)

- **MemberProducts**: 회원별 상품 상태 관리 테이블
  - Member (Members 링크)
  - Product (Products 링크)
  - Subscription Status (Active/Expired/N/A, 자동 계산)
  - Last Payment Date (마지막 결제일)
  - Expiry Date (만료일, 자동 계산)
  - Welcome Sent (첫 구매 안내 완료 여부, 수동 관리)

#### New Functions (airtable_syncer.py)
- `ensure_tables_exist()`: Products/MemberProducts 테이블 자동 생성
- `sync_products_to_airtable()`: Orders에서 상품 추출 및 동기화
- `sync_member_products_to_airtable()`: 회원별 상품 상태 집계 및 동기화

#### New Utilities (utils.py)
- `parse_iso_datetime()`: ISO 8601 문자열 → datetime 변환
- `calculate_subscription_status()`: 구독 만료일 및 상태 계산

#### Documentation
- `docs/SYSTEM_DESIGN.md`: 전체 시스템 설계 문서 (신입 개발자용)
- `docs/CHANGELOG.md`: 변경 이력 문서

### Changed

#### config.py
- `AIRTABLE_TABLES`에 `products`, `member_products` 추가

#### airtable_syncer.py
- `sync_all_to_airtable()`: 동기화 순서 변경
  - 기존: Members → Orders → Refunds
  - 변경: Members → Orders → Products → MemberProducts → Refunds
- `record_sync_history()`: Products/MemberProducts 통계 필드 추가

#### main.py
- `print_summary()`: Products/MemberProducts 결과 출력 추가
- 히스토리 기록에 `products_new`, `member_products_new`, `member_products_updated` 추가

### Technical Details

#### 구독 상태 판단 로직
```
Payment Type = "Regular Payment" → 구독 상품
만료일 = 마지막 결제일 + Subscription Days
상태 = 만료일 > 오늘 ? "Active" : "Expired"
구독 상품이 아니면 → "N/A"
```

#### MemberProducts 업데이트 정책
- 신규: Welcome Sent = False, 나머지는 자동 계산
- 기존: Welcome Sent는 유지, 상태/날짜만 업데이트

---

## [2.0.0] - 2024-12-27

### Summary
프로젝트 통합 및 재구성. get-publ-data와 update-publ-data-to-database를 하나로 통합.

### Added
- 통합된 단일 실행 스크립트 (`main.py`)
- Airtable Linked Record 자동 연결
- 환불 상태 변경 추적 기능
- 동기화 히스토리 기록 (SyncHistory 테이블)
- ISO 8601 날짜 형식 지원

### Changed
- 프로젝트 구조 재설계
- 모듈화된 코드 구조 (config, utils, downloader, airtable_syncer)

---

## [1.0.0] - 2024-12-14

### Summary
초기 버전. 기본적인 데이터 다운로드 및 동기화 기능.

### Added
- publ.biz 데이터 다운로드 (Playwright)
- Airtable 동기화 (Members, Orders, Refunds)
