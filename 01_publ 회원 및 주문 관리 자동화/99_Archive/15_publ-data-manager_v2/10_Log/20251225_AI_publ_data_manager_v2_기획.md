---
created: 2025-12-25T17:00
modified: 2025-12-25T23:30
---

## Summary

publ-data-manager v1을 기반으로 두 가지 기능을 추가하는 v2 기획. (1) 주문목록에서 반품 여부 구별 기능, (2) Airtable 동기화 및 테이블 간 Relation 연동.

## Why (왜)

#### 배경

- 현재 v1은 Supabase에만 데이터를 동기화하고 있음
- 주문 데이터와 환불 데이터가 별개로 관리되어, 특정 주문이 반품되었는지 쉽게 파악하기 어려움
- Airtable의 직관적인 UI와 Relation 기능을 활용하면 데이터 관계를 시각적으로 확인 가능

#### 목적

1. **반품 구별**: 주문 목록에서 해당 주문이 반품되었는지 즉시 확인
2. **Airtable 연동**: Supabase와 병행하여 Airtable에도 데이터 동기화
3. **데이터 연결**: Member ↔ Order ↔ Refund 관계를 Linked Records로 연결하여 한눈에 파악

## What (무엇을)

#### 작업 항목

**Phase 1: 반품 구별 기능**
- [x] 주문 동기화 시 환불 테이블과 비교
- [x] 주문 레코드에 `is_refunded` (반품여부) 필드 추가
- [x] 기존 주문 데이터에 반품 여부 업데이트 로직

**Phase 2: Airtable 동기화 모듈**
- [x] Airtable API 설정 (PAT 토큰, Base ID)
- [x] `airtable_syncer.py` 모듈 신규 개발
- [x] pyairtable 라이브러리 활용
- [x] Supabase 동기화와 병행 실행

**Phase 3: Airtable Relation 설계**
- [x] 테이블 구조 설계 (Members, Orders, Refunds)
- [x] Linked Records 필드 구성
- [x] 동기화 시 Record ID 기반 연결 로직

#### 결과물

```
src/
├── config.py           # Airtable 설정 추가
├── syncer.py           # 반품 여부 필드 추가
├── airtable_syncer.py  # 신규: Airtable 동기화 모듈
└── main.py             # Airtable 동기화 호출 추가
```

## How (어떻게)

#### 기술 설계

---

### 1. 반품 구별 로직

#### 정의
- **반품 = `Refund Status`가 "Refunded"인 경우만**
- "Rejected"(거절)는 반품으로 처리하지 않음

#### Supabase 스키마 변경
- `publ-order-db` 테이블에 `is_refunded` (boolean) 컬럼 추가
- 기본값: `false`

#### 동기화 워크플로우

```
1. Orders 신규 업데이트
   → 새 주문 INSERT (is_refunded = false)

2. Refunds 신규 업데이트
   → 새 환불 INSERT
   → 신규 환불 중 status="Refunded"인 것:
      해당 Order Number의 주문을 is_refunded=true로 UPDATE

3. 정합성 체크 (자동, 매 10회 실행마다)
   → 누락된 환불 처리 복구
```

#### 상세 구현

**평상시: 증분 처리 (효율적)**
```python
# sync_refunds() 내에서
new_refunds = [...]  # 이번에 INSERT된 신규 환불들

for refund in new_refunds:
    if refund['Refund Status'] == 'Refunded':
        supabase.table('publ-order-db') \
            .update({'is_refunded': True}) \
            .eq('Order Number', refund['Order Number']) \
            .execute()
```

**정합성 체크: 전체 비교 (안전장치)**
```python
def check_integrity():
    """누락된 환불 처리 복구"""

    # Refunded인 모든 Order Number
    refunded = supabase.table('publ-refund-db') \
        .select('Order Number') \
        .eq('Refund Status', 'Refunded') \
        .execute()
    refunded_set = {r['Order Number'] for r in refunded.data}

    # is_refunded=false인 Order Number
    unmarked = supabase.table('publ-order-db') \
        .select('Order Number') \
        .eq('is_refunded', False) \
        .execute()
    unmarked_set = {r['Order Number'] for r in unmarked.data}

    # 교집합 = 누락된 것
    missing = refunded_set & unmarked_set

    if missing:
        print(f"누락 발견: {len(missing)}건")
        for order_num in missing:
            supabase.table('publ-order-db') \
                .update({'is_refunded': True}) \
                .eq('Order Number', order_num) \
                .execute()
        print("복구 완료")
    else:
        print("정합성 OK")
```

#### 정합성 체크 자동화

| 항목 | 설정 |
|------|------|
| **실행 주기** | 매 10회 실행마다 자동 |
| **구현 방식** | 실행 카운터를 파일에 저장, 10회마다 체크 실행 |
| **목적** | 동기화 중단/오류로 인한 누락 자동 복구 |

```python
# main.py 예시
INTEGRITY_CHECK_INTERVAL = 10
counter_file = BASE_DIR / '.run_counter'

def should_check_integrity():
    count = int(counter_file.read_text()) if counter_file.exists() else 0
    count += 1
    counter_file.write_text(str(count))
    return count % INTEGRITY_CHECK_INTERVAL == 0

# 메인 실행 흐름
if should_check_integrity():
    print("정합성 체크 실행...")
    check_integrity()
```

---

### 2. Airtable 테이블 구조

| 테이블 | 필드 | 타입 | 설명 |
|--------|------|------|------|
| **Members** | Member Code | Primary Field | 회원 고유 코드 |
| | (기타 회원 정보) | | |
| | Orders | Linked Record → Orders | 해당 회원의 주문 목록 |
| **Orders** | Order Number | Primary Field | 주문 고유 번호 |
| | Member | Linked Record → Members | 주문자 (Member Code로 연결) |
| | is_refunded | Checkbox | 반품 여부 |
| | Refund | Linked Record → Refunds | 연결된 환불 정보 |
| | (기타 주문 정보) | | |
| **Refunds** | Order Number | Primary Field | 환불 대상 주문번호 |
| | Order | Linked Record → Orders | 연결된 주문 |
| | Refund Status | Single Select | 환불 상태 |
| | (기타 환불 정보) | | |

---

### 3. Airtable Linked Records 연결 방식

**typecast 옵션 활용**:
- 레코드 생성 시 `typecast=True` 설정
- Linked Record 필드에 Record ID 대신 Primary Field 값(예: Member Code) 전달
- Airtable API가 자동으로 매칭하여 연결

```python
# airtable_syncer.py 예시
from pyairtable import Api

def sync_orders_to_airtable(api, orders_table, members_table, records):
    for record in records:
        member_code = record.get('Member Code')

        # Member 레코드 조회하여 Record ID 획득
        member_records = members_table.all(
            formula=f"{{Member Code}}='{member_code}'"
        )
        member_id = member_records[0]['id'] if member_records else None

        orders_table.create({
            'Order Number': record['Order Number'],
            'Member': [member_id] if member_id else [],  # Linked Record는 배열
            'is_refunded': record.get('is_refunded', False),
            # ... 기타 필드
        })
```

---

### 4. 동기화 흐름

```
1. 다운로드 (기존 유지)
   publ.biz → downloads/ (CSV)

2. Supabase 동기화 (기존 + 수정)
   - Members: INSERT (신규)
   - Orders: INSERT + is_refunded 필드 추가
   - Refunds: INSERT + UPDATE (상태 변경)

3. Airtable 동기화 (신규)
   - Members: Upsert (Member Code 기준)
   - Orders: Upsert + Member Linked Record 연결
   - Refunds: Upsert + Order Linked Record 연결

4. 아카이브 (기존 유지)
   downloads/ → archive/
```

---

### 5. 환경 설정 추가

**.env 추가 항목**:
```
# Airtable
AIRTABLE_API_KEY=patXXXXXXXXXXXXXX
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
```

**config.py 추가**:
```python
# Airtable 인증
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')

# Airtable 테이블 이름
AIRTABLE_TABLES = {
    'members': 'Members',
    'orders': 'Orders',
    'refunds': 'Refunds'
}
```

---

### 6. 의존성 추가

**requirements.txt**:
```
playwright>=1.40.0
python-dotenv>=1.0.0
supabase>=2.0.0
pyairtable>=2.0.0  # 추가
```

---

#### 진행 상태

**완료** (2025-12-25)

---

## 참고 자료

- [pyAirtable Documentation](https://pyairtable.readthedocs.io/en/stable/api.html)
- [Airtable Linked Records API](https://community.airtable.com/t5/development-apis/linked-records-in-api-call/m-p/200367)
- [Airtable typecast 옵션](https://community.airtable.com/t5/development-apis/how-to-i-insert-records-into-link-fields-with-api/td-p/121454)
