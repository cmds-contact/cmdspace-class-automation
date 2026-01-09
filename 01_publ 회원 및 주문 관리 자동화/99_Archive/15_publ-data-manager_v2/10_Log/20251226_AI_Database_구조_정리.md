---
created: 2025-12-26T1700
modified: 2025-12-26T1700
---
## Summary

publ-data-manager v2 프로젝트의 Supabase와 Airtable 데이터베이스 구조를 분석하고 문서화함.

## Why (왜)

#### 배경
- 프로젝트가 두 개의 데이터베이스(Supabase, Airtable)를 사용
- 테이블 구조와 관계가 코드 내에 분산되어 있어 전체 파악이 어려움
- 향후 유지보수와 확장을 위한 명확한 문서 필요

#### 목적
1. 전체 데이터베이스 구조를 한눈에 파악할 수 있는 문서 생성
2. 테이블 간 관계 및 데이터 흐름 명시
3. 필드별 타입과 용도 정리

## What (무엇을)

#### 작업 항목

- [x] src/config.py 분석 - 테이블 설정 확인
- [x] src/syncer.py 분석 - Supabase 테이블 구조 파악
- [x] src/airtable_syncer.py 분석 - Airtable 테이블 구조 파악
- [x] 데이터베이스 구조 문서화

#### 결과물

### 1. Supabase 테이블 구조

**publ-member-db (회원)**
| 필드명 | 타입 | 설명 |
|--------|------|------|
| Member Code | text (PK) | 회원 고유 코드 |
| Username | text | 사용자명 |
| E-mail | text | 이메일 |
| Country | text | 국가 |
| Name | text | 이름 |
| Gender | text | 성별 |
| Birth year | text | 출생년도 |
| Personal email address | text | 개인 이메일 |
| Mobile number | text | 전화번호 |
| Sign-up Date | text | 가입일 |

**publ-order-db (주문)**
| 필드명 | 타입 | 설명 |
|--------|------|------|
| Order Number | text (PK) | 주문번호 |
| Product name | text | 상품명 |
| Type | text | 상품 타입 |
| Price | text | 가격 |
| Name | text | 주문자명 |
| E-mail | text | 주문자 이메일 |
| Member Code | text | 회원 코드 (FK) |
| Date and Time of Payment | text | 결제일시 |
| Payment Type | text | 결제 유형 |
| Payment Method | text | 결제 방법 |
| **is_refunded** | boolean | 환불 여부 (v2 신규) |

**publ-refund-db (환불)**
| 필드명 | 타입 | 설명 |
|--------|------|------|
| Order Number | text (PK) | 환불 주문번호 |
| Refund Status | text | 환불 상태 (Refunded/Rejected) |
| Refund Request Price | text | 환불 요청 금액 |
| Username | text | 사용자명 |
| Member Code | text | 회원 코드 |
| Refund Request Date | text | 환불 요청일 |

---

### 2. Airtable 테이블 구조

**Members (회원)**
| 필드명 | 타입 | 설명 |
|--------|------|------|
| Member Code | Single line text (PK) | 회원 고유 코드 |
| Username | Single line text | 사용자명 |
| E-mail | Email | 이메일 |
| Country | Single line text | 국가 |
| Name | Single line text | 이름 |
| Gender | Single line text | 성별 |
| Birth year | Single line text | 출생년도 |
| Personal email address | Email | 개인 이메일 |
| Mobile number | Phone | 전화번호 |
| Sign-up Date | Date | 가입일 |
| **Orders** | Link to Orders | 주문 연결 |

**Orders (주문)**
| 필드명 | 타입 | 설명 |
|--------|------|------|
| Order Number | Single line text (PK) | 주문번호 |
| Product name | Single line text | 상품명 |
| Type | Single line text | 상품 타입 |
| Price | Number (currency) | 가격 |
| Name | Single line text | 주문자명 |
| E-mail | Email | 주문자 이메일 |
| Member Code | Single line text | 회원 코드 |
| Date and Time of Payment | Date | 결제일시 |
| Payment Type | Single line text | 결제 유형 |
| Payment Method | Single line text | 결제 방법 |
| **is_refunded** | Checkbox | 환불 여부 |
| **Member** | Link to Members | 회원 연결 |
| **Refund** | Link to Refunds | 환불 연결 |

**Refunds (환불)**
| 필드명 | 타입 | 설명 |
|--------|------|------|
| Order Number | Single line text (PK) | 환불 주문번호 |
| Refund Status | Single select | 환불 상태 |
| Refund Request Price | Number (currency) | 환불 요청 금액 |
| Username | Single line text | 사용자명 |
| Member Code | Single line text | 회원 코드 |
| Refund Request Date | Date | 환불 요청일 |
| **Orders** | Link to Orders | 주문 연결 |

---

### 3. 데이터 흐름

```
CSV 파일 (다운로드)
    │
    ▼
┌──────────────────────────────────────────────────────┐
│                    Supabase                          │
│  (Single Source of Truth)                            │
│                                                      │
│  publ-member-db ◄────────────────────┐               │
│       │                              │               │
│       │ Member Code                  │               │
│       ▼                              │               │
│  publ-order-db ──────────────────────┤               │
│       │         is_refunded          │               │
│       │ Order Number                 │               │
│       ▼                              │               │
│  publ-refund-db ─────────────────────┘               │
│                                                      │
└──────────────────────────────────────────────────────┘
    │
    │ 동기화
    ▼
┌──────────────────────────────────────────────────────┐
│                    Airtable                          │
│  (시각화 & 관계 표현)                                 │
│                                                      │
│  Members ◄──────── Linked ────────► Orders          │
│                                        │             │
│                                   Linked             │
│                                        ▼             │
│                                    Refunds           │
└──────────────────────────────────────────────────────┘
```

---

### 4. 주요 관계

| 관계 | 설명 |
|------|------|
| Members → Orders | 1:N (한 회원이 여러 주문 가능) |
| Orders → Refunds | 1:1 (한 주문당 하나의 환불) |
| Orders.is_refunded | Refunds에 Refunded 레코드 존재 시 true |

---

### 5. 연결 정보

**Supabase**
- Project: publ-order-db (환경변수로 관리)
- Tables: publ-member-db, publ-order-db, publ-refund-db

**Airtable**
- Base ID: appEMKRma7uMq1ioU
- Base Name: publ Data Manager
- Tables: Members, Orders, Refunds

## How (어떻게)

#### 진행 방법
1. src/ 폴더의 핵심 파일 분석 (config.py, syncer.py, airtable_syncer.py)
2. 테이블별 필드 추출 및 타입 확인
3. Linked Records 관계 파악
4. 데이터 흐름도 작성

#### 진행 상태
완료
