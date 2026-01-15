# Publ Data Manager 시스템 설계 문서

> 이 문서는 Publ Data Manager 시스템의 전체 구조와 동작 방식을 설명합니다.
> 신입 개발자도 쉽게 이해할 수 있도록 작성되었습니다.

---

## 목차

1. [시스템 개요](#1-시스템-개요)
2. [전체 아키텍처](#2-전체-아키텍처)
3. [데이터 흐름](#3-데이터-흐름)
4. [Airtable 테이블 구조](#4-airtable-테이블-구조)
5. [모듈별 상세 설명](#5-모듈별-상세-설명)
6. [핵심 로직 설명](#6-핵심-로직-설명)
7. [실행 방법](#7-실행-방법)
8. [자주 묻는 질문 (FAQ)](#8-자주-묻는-질문-faq)

---

## 1. 시스템 개요

### 1.1 이 시스템은 무엇인가요?

**Publ Data Manager**는 [publ.biz](https://console.publ.biz) 플랫폼의 데이터를 자동으로 수집하여 Airtable에 동기화하는 자동화 도구입니다.

### 1.2 왜 필요한가요?

| 문제 | 해결책 |
|------|--------|
| publ.biz에서 데이터를 일일이 다운로드하기 번거로움 | 자동으로 다운로드 |
| 회원/주문 데이터를 한눈에 보기 어려움 | Airtable에서 통합 관리 |
| 구독 상태를 일일이 계산해야 함 | 자동으로 구독 상태 계산 |
| 신규 주문에 안내를 보냈는지 기억하기 어려움 | Welcome Sent 체크박스로 관리 |

### 1.3 주요 기능

```
1. 데이터 자동 다운로드
   - 회원 목록 (Members)
   - 주문 목록 (Orders)
   - 환불 목록 (Refunds)

2. Airtable 자동 동기화
   - 신규 데이터만 추가 (중복 방지)
   - 테이블 간 자동 연결 (Linked Record)

3. 구독 상태 자동 관리
   - 결제일 + 구독기간으로 만료일 계산
   - Active(진행중) / Expired(만료) 자동 판별

4. 첫 구매 안내 관리
   - 신규 회원+상품 조합 자동 감지
   - 안내 완료 여부 체크박스 제공
```

---

## 2. 전체 아키텍처

### 2.1 시스템 구성도

```
┌─────────────────────────────────────────────────────────────────┐
│                        Publ Data Manager                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│   │  Downloader  │ ──▶  │    Syncer    │ ──▶  │   Airtable   │  │
│   │  (Playwright)│      │  (pyairtable)│      │   (Cloud)    │  │
│   └──────────────┘      └──────────────┘      └──────────────┘  │
│          │                     │                                 │
│          ▼                     ▼                                 │
│   ┌──────────────┐      ┌──────────────┐                        │
│   │  CSV Files   │      │   Archive    │                        │
│   │  (downloads/)│      │  (archive/)  │                        │
│   └──────────────┘      └──────────────┘                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
         │
         │ 데이터 수집
         ▼
┌─────────────────┐
│   publ.biz      │
│   (웹사이트)     │
└─────────────────┘
```

### 2.2 기술 스택

| 구성요소 | 기술 | 역할 |
|---------|------|------|
| 웹 자동화 | Playwright | publ.biz에서 데이터 다운로드 |
| 데이터 저장 | Airtable | 클라우드 데이터베이스 |
| API 연동 | pyairtable | Airtable API 클라이언트 |
| 언어 | Python 3.11+ | 전체 시스템 개발 |

### 2.3 폴더 구조

```
20_Codebase_v2/
├── src/                    # 소스 코드
│   ├── __init__.py
│   ├── config.py          # 설정 관리
│   ├── utils.py           # 유틸리티 함수
│   ├── downloader.py      # 데이터 다운로드
│   ├── airtable_syncer.py # Airtable 동기화
│   └── main.py            # 메인 실행
│
├── downloads/             # 다운로드된 CSV 파일 (임시)
├── archive/               # 처리 완료된 CSV 파일
│   └── YYYYMMDD/         # 날짜별 폴더
│
├── docs/                  # 문서
├── .env                   # 환경변수 (비밀번호 등)
├── .session.json          # 로그인 세션 저장
├── requirements.txt       # 패키지 의존성
└── run.command           # 실행 스크립트 (macOS)
```

---

## 3. 데이터 흐름

### 3.1 전체 프로세스

```
[STEP 1] 데이터 다운로드
         │
         │  Playwright가 publ.biz에 로그인
         │  회원/주문/환불 CSV 파일 다운로드
         ▼
┌─────────────────────────────────────┐
│  downloads/                          │
│  ├── 251230_143022_members.csv      │
│  ├── 251230_143025_orders_latest.csv│
│  └── 251230_143030_refunds.csv      │
└─────────────────────────────────────┘
         │
         │
[STEP 2] Airtable 동기화
         │
         │  CSV 파일 읽기
         │  기존 데이터와 비교
         │  신규 데이터만 추가
         ▼
┌─────────────────────────────────────┐
│  Airtable Tables                     │
│  ├── Members (회원)                  │
│  ├── Orders (주문)                   │
│  ├── Products (상품)                 │
│  ├── MemberPrograms (회원별 프로그램)│
│  ├── Refunds (환불)                  │
│  └── SyncHistory (동기화 이력)       │
└─────────────────────────────────────┘
         │
         │
[STEP 3] 파일 아카이브
         │
         │  처리 완료된 CSV 파일을
         │  archive/YYYYMMDD/ 폴더로 이동
         ▼
┌─────────────────────────────────────┐
│  archive/20251230/                   │
│  └── (처리된 CSV 파일들)             │
└─────────────────────────────────────┘
```

### 3.2 동기화 순서와 이유

동기화는 아래 순서로 진행됩니다. **순서가 중요합니다!**

```
1. Members (회원)
   └─▶ 다른 테이블에서 참조하므로 가장 먼저

2. Orders (주문) - 신규 추가, Member 연결
   └─▶ Members와 연결 필요
   └─▶ Products 추출의 데이터 소스

3. Products (상품)
   └─▶ Orders에서 상품명 추출
   └─▶ MemberPrograms에서 참조

4. MemberPrograms (회원별 프로그램) - 신규만
   └─▶ Members, Products, Orders 모두 필요
   └─▶ 구독 상태/만료일은 Airtable Formula가 처리

5. Orders - MemberPrograms 연결 업데이트
   └─▶ MemberPrograms 생성 후 Orders와 연결

6. Refunds (환불)
   └─▶ Orders와 연결 필요
```

---

## 4. Airtable 테이블 구조

### 4.1 테이블 관계도

```
┌─────────────┐          ┌──────────────────┐          ┌─────────────┐
│   Members   │◀────────▶│  MemberPrograms  │◀────────▶│  Products   │
│   (회원)    │  1:N     │ (회원별 프로그램) │   N:1    │   (상품)    │
└─────────────┘          └──────────────────┘          └─────────────┘
       │                          ▲
       │ 1:N                      │ N:1
       ▼                          │
┌─────────────┐                   │
│   Orders    │───────────────────┘
│   (주문)    │   MemberPrograms 연결 (Member Code + Program Code)
└─────────────┘
       │
       │ 1:1
       ▼
┌─────────────┐
│   Refunds   │
│   (환불)    │
└─────────────┘


┌─────────────┐
│ SyncHistory │  ← 동기화 이력 (다른 테이블과 연결 없음)
│ (동기화이력)│
└─────────────┘
```

### 4.2 각 테이블 상세 설명

#### Members (회원)

회원 기본 정보를 저장합니다.

| 필드명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| Member Code | Text | **고유 키** - 회원 식별자 | `ABC123` |
| Username | Text | 사용자명 | `john_doe` |
| E-mail | Email | 이메일 주소 | `john@example.com` |
| Name | Text | 실명 | `홍길동` |
| Country | Text | 국가 | `Korea` |
| Gender | Text | 성별 | `Male` |
| Birth year | Text | 출생년도 | `1990` |
| Sign-up Date | Text | 가입일 (원본) | `2024-12-27 15:30` |
| Sign-up Date (ISO) | DateTime | 가입일 (표준형식) | `2024-12-27T15:30:00+09:00` |

---

#### Orders (주문)

주문/결제 정보를 저장합니다.

| 필드명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| Order Number | Text | **고유 키** - 주문번호 | `ORD-20241227-001` |
| Product name | Text | 상품명 | `KM-CMDS-OBM-ME-1` |
| Type | Text | 상품 유형 | `Membership plan` |
| Price | Number | 결제 금액 | `50000` |
| Name | Text | 구매자 이름 | `홍길동` |
| E-mail | Email | 구매자 이메일 | `hong@example.com` |
| Member Code | Text | 회원 코드 | `ABC123` |
| Payment Type | Text | 결제 유형 | `Regular Payment` 또는 `One-time Payment` |
| Payment Method | Text | 결제 수단 | `Credit Card` |
| Date and Time of Payment | Text | 결제일시 (원본) | `2024-12-27 15:30:45` |
| Date and Time of Payment (ISO) | DateTime | 결제일시 (표준형식) | `2024-12-27T15:30:45+09:00` |
| Member | Link | Members 테이블 연결 | (자동 연결) |
| MemberPrograms | Link | MemberPrograms 테이블 연결 | (자동 연결) |

**중요**: `Payment Type`이 `Regular Payment`면 **구독 상품**입니다.
**연결 방식**: MemberPrograms는 `{Member Code}_{Program Code}` 형식의 코드로 연결됩니다.

---

#### Products (상품)

상품 마스터 정보를 저장합니다.

| 필드명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| Product Code | Text | **고유 키** - 상품 코드 | `KM-CMDS-OBM-ME-1` |
| Display Name | Text | 표시용 상품명 (수동 입력) | `CMDS 온라인 멤버십` |
| Is Subscription | Checkbox | 구독 상품 여부 | ✅ (체크됨) |
| Subscription Days | Number | 구독 기간 (일수) **수동 입력** | `30` |

**중요**: `Subscription Days`는 반드시 수동으로 입력해야 합니다!

---

#### MemberPrograms (회원별 프로그램 상태) ⭐ 핵심 테이블

회원이 구매한 각 프로그램의 상태를 관리합니다.

> **Program Code란?**
> Product Code의 처음 3개 세그먼트를 Program Code로 사용합니다.
> - 예: `KM-CMDS-OBM-ME-1` → Program Code: `KM-CMDS-OBM`
> - 뒷부분(`ME-1`, `YE-2` 등)은 **구매 옵션**(할인, 정가, 연간 등)을 나타냅니다.
> - 같은 프로그램의 다른 옵션을 구매해도 하나의 MemberPrograms 레코드로 관리됩니다.

| 필드명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| MemberPrograms Code | Text | **고유 키** - 회원+프로그램 식별자 | `ABC123_KM-CMDS-OBM` |
| Member | Link | Members 테이블 연결 | (자동 연결) |
| Product | Link | Products 테이블 연결 | (자동 연결) |
| Subscription Status | Formula | 구독 상태 **(Airtable Formula)** | `Active` / `Expired` / `N/A` |
| Last Payment Date | Rollup | 마지막 결제일 **(Airtable Rollup)** | `2024-12-27` |
| Expiry Date | Formula | 만료일 **(Airtable Formula)** | `2025-01-26` |
| Welcome Sent | Checkbox | 첫 구매 안내 완료 여부 | ☐ (미완료) / ✅ (완료) |

**Program Code 추출 규칙** (REGEX):
```
REGEX: ^([^-]+(-[^-]+){2})
예시:
  KM-CMDS-OBM-ME-1  → KM-CMDS-OBM
  KM-CMDS-OBM-YE-2  → KM-CMDS-OBM
  KM-CMDS-OBM       → KM-CMDS-OBM (세그먼트가 3개면 그대로)
```

**Subscription Status 설명** (Airtable Formula로 자동 계산):
- `Active`: 구독 진행 중 (만료일이 오늘 이후)
- `Expired`: 구독 만료됨 (만료일이 오늘 이전)
- `N/A`: 일회성 구매 (구독 상품이 아님)

**Welcome Sent 사용법**:
- 새로운 레코드가 생기면 자동으로 `False`(미체크)
- 안내를 보낸 후 수동으로 체크 ✅
- 시스템이 이 값을 자동으로 변경하지 않음

**참고**: 구독 상태 및 만료일은 Python 코드가 아닌 Airtable Formula로 처리됩니다.

---

#### Refunds (환불)

환불 요청 정보를 저장합니다.

| 필드명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| Order Number | Text | **고유 키** - 주문번호 | `ORD-20241227-001` |
| Refund Status | Text | 환불 상태 | `Requested` / `Refunded` / `Rejected` |
| Refund Request Price | Number | 환불 요청 금액 | `50000` |
| Username | Text | 요청자 | `john_doe` |
| Member Code | Text | 회원 코드 | `ABC123` |
| Refund Request Date | Text | 요청일 (원본) | `2024-12-27` |
| Orders | Link | Orders 테이블 연결 | (자동 연결) |

---

#### SyncHistory (동기화 이력)

동기화 실행 기록을 저장합니다.

| 필드명 | 타입 | 설명 |
|--------|------|------|
| [Sync DateTime] | DateTime | 동기화 실행 시간 |
| Duration (sec) | Number | 소요 시간 (초) |
| Status | Text | 성공/실패 |
| Members New | Number | 신규 회원 수 |
| Orders New | Number | 신규 주문 수 |
| Products New | Number | 신규 상품 수 |
| MemberProducts New | Number | 신규 회원상품 수 |
| MemberProducts Updated | Number | 업데이트된 회원상품 수 |
| Refunds New | Number | 신규 환불 수 |
| Refunds Updated | Number | 업데이트된 환불 수 |
| Downloaded Files | Text | 다운로드된 파일명 |
| Error Message | Text | 오류 메시지 (실패 시) |

---

## 5. 모듈별 상세 설명

### 5.1 config.py (설정 관리)

환경변수와 상수를 관리합니다.

```python
# 주요 설정값
PUBL_ID          # publ.biz 로그인 아이디
PUBL_PW          # publ.biz 로그인 비밀번호
AIRTABLE_API_KEY # Airtable API 키
AIRTABLE_BASE_ID # Airtable Base ID

# 폴더 경로
DOWNLOAD_DIR = ./downloads/  # CSV 다운로드 폴더
ARCHIVE_DIR  = ./archive/    # 아카이브 폴더

# Airtable 테이블 이름 매핑
AIRTABLE_TABLES = {
    'members': 'Members',
    'orders': 'Orders',
    'products': 'Products',
    'member_programs': 'MemberPrograms',
    'refunds': 'Refunds',
    'sync_history': 'SyncHistory'
}
```

### 5.2 utils.py (유틸리티 함수)

자주 사용하는 헬퍼 함수들입니다.

| 함수명 | 역할 | 예시 |
|--------|------|------|
| `extract_program_code(product_code)` | Product Code에서 Program Code 추출 | `KM-CMDS-OBM-ME-1` → `KM-CMDS-OBM` |
| `batch_iterator(items, size)` | 리스트를 배치로 나눔 | 100개씩 나눠서 처리 |
| `parse_price("1,000원")` | 가격 문자열 → 숫자 | `1000` |
| `safe_get(dict, key)` | 딕셔너리 안전 조회 | 키가 없으면 빈 문자열 |
| `to_iso_datetime(date_str)` | 날짜 → ISO 형식 | `2024-12-27T15:30:00+09:00` |
| ~~`calculate_subscription_status(...)`~~ | ~~구독 상태 계산~~ | **[DEPRECATED]** Airtable Formula로 대체됨 |

### 5.3 downloader.py (데이터 다운로드)

Playwright를 사용해 publ.biz에서 데이터를 다운로드합니다.

```
주요 함수:
├── login()                    # 로그인 (세션 재사용)
├── download_members()         # 회원 목록 다운로드
├── download_orders()          # 주문 목록 다운로드 (최신 1페이지)
├── download_orders_all_pages() # 주문 전체 다운로드
├── download_refunds()         # 환불 목록 다운로드
└── download_all()             # 전체 다운로드
```

**세션 관리**: `.session.json`에 로그인 세션을 저장하여 매번 로그인하지 않아도 됩니다.

### 5.4 airtable_syncer.py (Airtable 동기화)

CSV 데이터를 Airtable로 동기화합니다.

```
주요 함수:
├── ensure_tables_exist()               # 테이블 존재 확인 및 생성
├── sync_members_to_airtable()          # 회원 동기화
├── sync_orders_to_airtable()           # 주문 동기화
├── sync_products_to_airtable()         # 상품 동기화
├── sync_member_programs_to_airtable()  # 회원별 프로그램 동기화 (신규만)
├── update_orders_member_programs_link() # Orders-MemberPrograms 연결
├── sync_refunds_to_airtable()          # 환불 동기화
├── sync_all_to_airtable()              # 전체 동기화
└── record_sync_history()               # 동기화 이력 기록

헬퍼 함수:
├── get_existing_records()              # 테이블에서 기존 레코드 조회
├── get_existing_orders()               # 주문 레코드 조회
├── get_existing_member_programs()      # MemberPrograms 레코드 조회
└── get_pending_refunds()               # 미결정 환불 조회
```

### 5.5 main.py (메인 실행)

전체 워크플로우를 실행합니다.

```python
def main():
    # 1. 환경변수 검증
    config.validate_config()

    # 2. 데이터 다운로드
    download_files = download_all()

    # 3. Airtable 동기화
    airtable_results = sync_all_to_airtable()

    # 4. 파일 아카이브
    archive_files()

    # 5. 동기화 히스토리 기록
    record_sync_history(...)
```

---

## 6. 핵심 로직 설명

### 6.1 구독 상태 계산 로직 (Airtable Formula)

> **Note**: v2.2.0부터 구독 상태 계산은 Airtable Formula로 처리됩니다.
> Python의 `calculate_subscription_status()` 함수는 deprecated 되었습니다.

**Airtable Formula 예시:**

```
Expiry Date:
IF(
  {Is Subscription} (from Product),
  DATEADD({Last Payment Date}, {Subscription Days} (from Product), 'days'),
  BLANK()
)

Subscription Status:
IF(
  NOT({Is Subscription} (from Product)),
  "N/A",
  IF(
    IS_AFTER({Expiry Date}, TODAY()),
    "Active",
    "Expired"
  )
)
```

**계산 로직:**
```
1. 구독 상품이 아니면 → "N/A"
2. 만료일 = 마지막 결제일 + 구독 기간 (일수)
3. 만료일 > 오늘 → "Active"
4. 만료일 <= 오늘 → "Expired"
```

### 6.2 MemberPrograms 생성 로직

```
신규 레코드 (회원+프로그램 조합이 처음인 경우):
├── MemberPrograms Code = {Member Code}_{Program Code}
│   └── Program Code = extract_program_code(Product name)
│       예: KM-CMDS-OBM-ME-1 → KM-CMDS-OBM
├── Member = [member_id] (Linked Record)
├── Product = [product_id] (Linked Record)
├── Welcome Sent = False (체크 안 됨)
└── 나머지 필드는 Airtable Formula/Rollup이 처리

기존 레코드:
└── Python에서 업데이트하지 않음 (Airtable이 자동 계산)

중복 방지:
└── 같은 프로그램의 다른 옵션(ME-1, YE-2)을 구매해도 하나의 레코드만 존재
```

**중요**:
- `Welcome Sent`는 시스템이 절대 자동으로 변경하지 않습니다.
- 관리자가 안내를 보낸 후 수동으로 체크해야 합니다.
- 구독 상태/만료일은 Airtable Formula가 실시간으로 계산합니다.

### 6.3 상품 구독 여부 판단 로직

```python
# Orders CSV에서 Payment Type 분석
for order in orders:
    product_name = order['Product name']
    payment_type = order['Payment Type']

    # "Regular Payment"가 있으면 구독 상품
    if payment_type == "Regular Payment":
        is_subscription = True
    else:
        is_subscription = False  # "One-time Payment" 등
```

---

## 7. 실행 방법

### 7.1 환경 설정

1. **Python 가상환경 생성 및 활성화**
```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
```

2. **패키지 설치**
```bash
pip install -r requirements.txt
```

3. **.env 파일 설정**
```bash
# .env 파일 내용
PUBL_ID=your_publ_id
PUBL_PW=your_publ_password
AIRTABLE_API_KEY=your_airtable_api_key
AIRTABLE_BASE_ID=your_airtable_base_id
```

### 7.2 일반 실행

```bash
# 방법 1: 직접 실행
source .venv/bin/activate
python -m src.main

# 방법 2: run.command 더블클릭 (macOS)
```

### 7.3 주문 전체 다운로드 (초기화)

처음 사용하거나 모든 주문을 다시 가져올 때:

```bash
python -m src.main --init-orders
```

### 7.4 실행 후 해야 할 일

1. **Products 테이블**에서 `Subscription Days` 입력
   - 각 상품의 구독 기간(일수)을 수동으로 입력

2. **MemberPrograms 테이블**에서 `Welcome Sent` 관리
   - 신규 레코드 확인 (Welcome Sent = 미체크)
   - 안내 발송 후 체크

---

## 8. 자주 묻는 질문 (FAQ)

### Q1. Products 테이블이 비어있어요

**A**: 정상입니다. Products는 Orders 데이터에서 자동으로 생성됩니다.
1. 먼저 주문 데이터가 있어야 합니다
2. 동기화를 실행하면 Orders의 Product name을 기반으로 Products가 생성됩니다

### Q2. Subscription Days를 입력했는데 상태가 N/A예요

**A**: Products 테이블에서 해당 상품의 `Is Subscription`이 체크되어 있는지 확인하세요.
- 체크 안 됨 → N/A
- 체크 됨 + Subscription Days 입력됨 → Active 또는 Expired

### Q3. MemberPrograms에 레코드가 없어요

**A**: 다음을 확인하세요:
1. Members 테이블에 해당 회원이 있는지
2. Products 테이블에 해당 상품이 있는지
3. Orders에 해당 주문이 있는지

세 테이블 모두 데이터가 있어야 MemberPrograms가 생성됩니다.

### Q4. 동기화가 실패했어요

**A**: SyncHistory 테이블에서 Error Message를 확인하세요.
흔한 원인:
- publ.biz 로그인 실패 → 비밀번호 확인
- Airtable API 오류 → API 키 확인
- 네트워크 오류 → 인터넷 연결 확인

### Q5. 이미 동기화한 데이터가 중복 추가되나요?

**A**: 아니요. 각 테이블마다 고유 키로 중복을 방지합니다:
- Members: Member Code
- Orders: Order Number
- Products: Product Code
- MemberPrograms: Member + Program 조합 (같은 프로그램의 다른 옵션은 하나의 레코드)
- Refunds: Order Number

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2026-01-15 | 2.3 | **MemberProducts → MemberPrograms 리네이밍**, Program Code 기반 레코드 관리 도입 |
| 2026-01-01 | 2.2 | Orders-MemberProducts Linked Record 추가, 구독 상태 계산을 Airtable Formula로 이관 |
| 2024-12-30 | 2.1 | Products, MemberProducts 테이블 추가 |
| 2024-12-27 | 2.0 | 프로젝트 통합 및 재구성 |
| 2024-12-14 | 1.0 | 초기 버전 (Members, Orders, Refunds) |

---

*문서 작성: Claude Code*
*최종 업데이트: 2026-01-15*
