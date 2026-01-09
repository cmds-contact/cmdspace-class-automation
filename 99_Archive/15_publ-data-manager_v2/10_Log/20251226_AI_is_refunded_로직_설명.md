---
created: 2025-12-26T1710
modified: 2025-12-26T1710
---
## Summary

주문의 환불 여부를 즉시 파악하기 위한 `is_refunded` 필드의 기능과 동작 논리를 설명.

## Why (왜)

#### 배경

기존 v1 시스템의 문제점:
- 주문 테이블(Orders)과 환불 테이블(Refunds)이 분리되어 있음
- 특정 주문이 환불되었는지 확인하려면 Refunds 테이블을 별도로 조회해야 함
- 대량의 주문 목록에서 환불 건을 빠르게 식별하기 어려움

#### 목적

1. 주문 목록에서 환불 여부를 **즉시 확인** 가능하게 함
2. Refunds 테이블 조인 없이 단일 쿼리로 환불 주문 필터링
3. Airtable에서 체크박스로 환불 상태 시각화

## What (무엇을)

#### is_refunded 필드 정의

| 속성 | 값 |
|------|-----|
| 필드명 | is_refunded |
| 위치 | publ-order-db (Supabase), Orders (Airtable) |
| 타입 | Boolean (Supabase) / Checkbox (Airtable) |
| 기본값 | false |
| 의미 | true = 환불 완료됨, false = 환불 안됨 |

#### 결과물

**주문 목록 조회 시:**
```
Order Number | Product | Price | is_refunded
-------------|---------|-------|-------------
ORD-001      | 상품A   | 10000 | false
ORD-002      | 상품B   | 20000 | true  ← 환불됨
ORD-003      | 상품C   | 15000 | false
```

## How (어떻게)

#### 동작 논리

### 1. 신규 주문 삽입 시

```
[syncer.py:sync_orders() - 라인 114-119]

새 주문 → is_refunded = False 로 삽입
```

모든 신규 주문은 환불되지 않은 상태로 시작.

---

### 2. 신규 환불 발생 시

```
[syncer.py:sync_refunds() - 라인 186-229]

1. Refunds 테이블에 새 환불 레코드 삽입
2. 해당 환불의 상태가 "Refunded"인지 확인
3. "Refunded"인 경우:
   → Orders 테이블에서 해당 Order Number 찾기
   → is_refunded = True 로 업데이트
```

**코드 흐름:**
```python
# 1. 신규 환불 중 Refunded인 주문번호 수집
new_refunded_orders = []
for record in new_records:
    if record.get('Refund Status') == 'Refunded':
        new_refunded_orders.append(record['Order Number'])

# 2. 해당 주문들의 is_refunded 업데이트
for order_number in new_refunded_orders:
    supabase.table('publ-order-db').update({
        'is_refunded': True
    }).eq('Order Number', order_number).execute()
```

---

### 3. 정합성 체크 (10회 실행마다)

```
[syncer.py:check_integrity() - 라인 234-292]

누락된 환불 처리를 복구하는 안전장치
```

**체크 로직:**
```
1. Refunds 테이블에서 "Refunded" 상태인 모든 Order Number 조회
2. Orders 테이블에서 is_refunded = False인 모든 Order Number 조회
3. 두 집합의 교집합 = 누락된 환불
4. 누락된 건에 대해 is_refunded = True로 업데이트
```

**다이어그램:**
```
Refunds (Refunded)     Orders (is_refunded=False)
    ┌───────┐              ┌───────┐
    │ORD-001│              │ORD-003│
    │ORD-002│              │ORD-004│
    │ORD-005│              │ORD-005│ ← 교집합 = 누락!
    └───────┘              └───────┘
                               │
                               ▼
                    is_refunded = True 로 복구
```

---

### 4. Airtable 동기화 시

```
[airtable_syncer.py:sync_orders_to_airtable() - 라인 95-178]

1. Supabase에서 모든 Orders 데이터 조회
2. 각 주문의 is_refunded 값을 Airtable에 동기화
3. 기존 레코드는 is_refunded 변경 시에만 업데이트
```

**업데이트 조건:**
```python
# 기존 Airtable 값과 Supabase 값 비교
if existing_data['is_refunded'] != new_refunded:
    # 변경된 경우에만 업데이트
    update_records.append({
        'id': existing_data['id'],
        'fields': {'is_refunded': new_refunded}
    })
```

---

#### 전체 흐름도

```
┌─────────────────────────────────────────────────────────────┐
│                        동기화 실행                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Members 동기화 (신규만 INSERT)                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Orders 동기화                                             │
│    - 신규 주문: is_refunded = False                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Refunds 동기화                                            │
│    - 신규 환불 INSERT                                        │
│    - 상태 변경 UPDATE                                        │
│    - Refunded인 경우 → Orders.is_refunded = True            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. 정합성 체크 (10회마다)                                     │
│    - 누락된 환불 탐지                                         │
│    - is_refunded 복구                                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Airtable 동기화                                           │
│    - Supabase → Airtable 데이터 복제                         │
│    - is_refunded 상태 동기화                                 │
└─────────────────────────────────────────────────────────────┘
```

---

#### 왜 이 방식인가?

| 대안 | 문제점 |
|------|--------|
| 매번 Refunds 조인 | 쿼리 복잡도 증가, 성능 저하 |
| 뷰(View) 사용 | Supabase 무료 플랜 제한 |
| 매번 전체 스캔 | 데이터 증가 시 비효율적 |

**현재 방식의 장점:**
1. 증분 처리 - 신규 환불만 체크
2. 정합성 보장 - 10회마다 전체 검증
3. 단순 쿼리 - is_refunded로 필터링 가능

#### 진행 상태

완료
