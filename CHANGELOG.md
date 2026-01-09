# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.3.0] - 2026-01-09

### Added
- **필수 필드 자동 검증 및 복구 기능**
  - `validate_required_fields()`: 필수 필드 누락 감지 및 자동 복구
  - `backfill_is_active()`: 기존 회원의 Is Active 필드 일괄 업데이트
  - `backfill_refunds_orders_link()`: Refunds → Orders 링크 복구
  - 동기화 완료 후 자동 검증 실행 (auto_fix=True)
  - `config.py`에 `REQUIRED_FIELDS` 설정 추가

- **Members 동기화 개선**
  - 새 회원 추가 시 'Is Active' 필드 자동 설정 (True)

- **문서화**
  - `docs/OPERATION_GUIDE.md` 운영 가이드 추가
  - `settings.yaml.example` 설정 파일 예시 추가
  - README.md 업데이트

- **테스트**
  - `tests/` 유닛 테스트 추가 (validators, csv_reader, records, utils)

### Changed
- Airtable 모듈 리팩토링 (`src/airtable/` 패키지로 분리)
- 로거 통합 (`src/logger.py`)

## [0.2.0] - 2026-01-08

### Added
- **데이터 불일치 분석 기능** (`data_analyzer.py`)
  - Airtable과 CSV 간 데이터 비교
  - 중복 레코드 감지
  - 테스트 레코드 분류

- **중복 방지 로직**
  - Airtable 기존 중복 검사
  - CSV 내 중복 검사
  - 삽입 후 카운트 검증

## [0.1.0] - 2026-01-07

### Added
- **초기 릴리스**
  - publ.biz 데이터 자동 다운로드 (Members, Orders, Refunds)
  - Airtable 동기화 (신규 레코드 추가)
  - Linked Record 자동 연결 (Member, Orders, Products, MemberProducts)
  - 동기화 히스토리 기록 (SyncHistory 테이블)
  - 파일 아카이브 기능
