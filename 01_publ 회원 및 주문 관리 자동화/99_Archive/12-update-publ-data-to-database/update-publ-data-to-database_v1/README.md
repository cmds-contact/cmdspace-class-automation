# Publ Data to Supabase Sync

Publ 플랫폼 데이터를 Supabase 데이터베이스에 동기화하는 스크립트입니다.

## Overview

- **목적**: Publ에서 추출한 CSV 데이터를 Supabase에 추가/업데이트
- **방식**: 증분 동기화 (새로운 데이터만 추가, 기존 데이터 유지)
- **대상 데이터**: 회원, 주문, 환불

## Data Flow

```
publ-data/
├── *_members.csv      →  publ-member-db (Member Code 기준)
├── *_orders_latest.csv →  publ-order-db  (Order Number 기준)
└── *_refunds.csv      →  publ-refund-db (Order Number 기준, 상태 업데이트 포함)
```

## Setup

### 1. Python 가상환경 활성화

```bash
source venv/bin/activate
```

### 2. 환경변수 설정

`.env` 파일에 Supabase 인증 정보가 설정되어 있어야 합니다:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
```

## Usage

### 실행

```bash
source venv/bin/activate
python sync_publ_data.py
```

### 출력 예시

```
============================================================
PUBL DATA TO SUPABASE SYNC
Started at: 2025-12-13 23:59:20
============================================================

==================================================
Syncing MEMBERS from: 251213_232121_members.csv
==================================================
CSV records: 1928
Existing records in Supabase: 1928
New records to insert: 0
No new records to insert

==================================================
Syncing ORDERS from: 251213_232125_orders_latest.csv
==================================================
CSV records: 300
Existing records in Supabase: 2801
New records to insert: 0
No new records to insert

==================================================
Syncing REFUNDS from: 251213_232132_refunds.csv
==================================================
CSV records: 65
Existing records in Supabase: 65
New records to insert: 0
Records to update (status changed): 0

============================================================
SYNC SUMMARY
============================================================
MEMBERS: 0 new
ORDERS: 0 new
REFUNDS: 0 new, 0 updated

Completed at: 2025-12-13 23:59:22
============================================================
```

## Processing Logic

| 데이터 | 고유 키 | 동작 |
|--------|---------|------|
| Members | Member Code | 신규만 INSERT |
| Orders | Order Number | 신규만 INSERT |
| Refunds | Order Number | 신규 INSERT + 상태변경 UPDATE |

### 처리 순서

1. `members.csv` → `publ-member-db`
2. `orders_latest.csv` → `publ-order-db`
3. `refunds.csv` → `publ-refund-db`

## Project Structure

```
update-publ-data-to-database_v1/
├── README.md              # 프로젝트 문서
├── sync_publ_data.py      # 메인 동기화 스크립트
├── .env                   # Supabase 인증 정보 (git 제외)
├── .gitignore             # git 제외 파일 목록
├── venv/                  # Python 가상환경
├── publ-data/             # CSV 데이터 폴더
│   ├── *_members.csv
│   ├── *_orders_latest.csv
│   └── *_refunds.csv
└── 01_Log/                # 작업 로그
```

## Supabase Tables

| Table | Columns |
|-------|---------|
| `publ-member-db` | Number, Username, Member Code, E-mail, Country, Name, Gender, Birth year, Personal email address, Mobile number, Sign-up Date |
| `publ-order-db` | Number, Order Number, Product name, Type, Price, Name, E-mail, Member Code, Date and Time of Payment, Payment Type, Payment Method |
| `publ-refund-db` | Number, Order Number, Refund Status, Refund Request Price, Username, Member Code, Refund Request Date |

## Notes

- CSV 파일은 UTF-8 BOM 인코딩으로 처리됩니다
- 새 CSV 파일을 `publ-data/` 폴더에 넣고 스크립트를 실행하면 자동으로 새 데이터만 동기화됩니다
- 환불 데이터의 경우, 상태 변경(예: "Refunded" → "Rejected")도 감지하여 업데이트합니다
