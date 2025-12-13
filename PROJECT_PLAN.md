# publ-data-manager Project Plan

## Executive Summary

두 개의 기존 프로젝트를 통합하여 publ 데이터를 자동으로 가져와 Supabase에 동기화하는 단일 자동화 솔루션을 구축합니다.

---

## Source Projects Analysis

### Project 1: get-publ-data_v5

**목적**: publ.biz 콘솔에서 데이터 다운로드

| 항목 | 내용 |
|------|------|
| 기술 스택 | Python, Playwright (브라우저 자동화) |
| 필요 인증 | `PUBL_ID`, `PUBL_PW` |
| 출력 | CSV 파일 (`YYMMDD_HHMMSS_*.csv`) |
| 출력 위치 | `downloads/` 폴더 |

**다운로드 데이터**:
- `*_members.csv` - 회원 목록
- `*_orders_latest.csv` - 주문 목록 (최신)
- `*_refunds.csv` - 환불 목록

**주요 기능**:
- 세션 저장/재사용 (`.session.json`)
- 헤드리스 브라우저 지원
- 불필요한 리소스 차단 (이미지, 폰트, 미디어)

---

### Project 2: update-publ-data-to-database_v1

**목적**: CSV 데이터를 Supabase에 동기화

| 항목 | 내용 |
|------|------|
| 기술 스택 | Python, Supabase Python SDK |
| 필요 인증 | `SUPABASE_URL`, `SUPABASE_KEY` |
| 입력 | CSV 파일 (`publ-data/` 폴더) |
| 출력 | Supabase 테이블 업데이트 |

**Supabase 테이블**:

| 테이블 | 고유 키 | 동작 |
|--------|---------|------|
| `publ-member-db` | Member Code | 신규만 INSERT |
| `publ-order-db` | Order Number | 신규만 INSERT |
| `publ-refund-db` | Order Number | INSERT + 상태변경 UPDATE |

---

## Merged Project Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    publ-data-manager                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [1] 데이터 다운로드                                             │
│  ┌──────────────┐      Playwright       ┌──────────────────┐   │
│  │  publ.biz    │  ─────────────────▶   │  downloads/      │   │
│  │  콘솔 로그인  │    (자동 로그인)       │  - members.csv   │   │
│  └──────────────┘                       │  - orders.csv    │   │
│                                         │  - refunds.csv   │   │
│                                         └────────┬─────────┘   │
│                                                  │              │
│  [2] 데이터 동기화                                │              │
│                                                  ▼              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     sync_to_supabase()                   │  │
│  │  - 새 레코드만 INSERT (중복 방지)                         │  │
│  │  - 환불 상태 변경 UPDATE                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                  │              │
│                                                  ▼              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                       Supabase                           │  │
│  │  - publ-member-db                                        │  │
│  │  - publ-order-db                                         │  │
│  │  - publ-refund-db                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Project Structure Setup

```
publ-data-manager/
├── .claude/                  # Claude 설정
├── .env                      # 통합 환경변수 (PUBL + Supabase)
├── .gitignore
├── .session.json             # 로그인 세션 저장
├── 01_Log/                   # 작업 로그
├── downloads/                # 다운로드된 CSV 파일
├── archive/                  # 과거 CSV 파일 보관
├── src/
│   ├── __init__.py
│   ├── config.py             # 설정 관리
│   ├── downloader.py         # publ 데이터 다운로드 모듈
│   ├── syncer.py             # Supabase 동기화 모듈
│   └── main.py               # 통합 실행 스크립트
├── requirements.txt          # Python 패키지 목록
├── run.command               # macOS 더블클릭 실행 스크립트
├── PROJECT_PLAN.md           # 프로젝트 계획서
└── README.md                 # 사용 설명서
```

### Phase 2: Core Modules

#### 2.1 config.py
- 환경변수 로드 및 검증
- 경로 상수 정의
- 테이블 설정 관리

#### 2.2 downloader.py
- `download_all()`: 전체 데이터 다운로드
- `download_members()`: 회원 데이터 다운로드
- `download_orders()`: 주문 데이터 다운로드
- `download_refunds()`: 환불 데이터 다운로드
- 세션 관리 (저장/로드/검증)

#### 2.3 syncer.py
- `sync_all()`: 전체 데이터 동기화
- `sync_members()`: 회원 데이터 동기화
- `sync_orders()`: 주문 데이터 동기화
- `sync_refunds()`: 환불 데이터 동기화 (상태 업데이트 포함)

#### 2.4 main.py
- 전체 워크플로우 오케스트레이션
- 에러 핸들링 및 로깅
- 실행 결과 요약 출력

### Phase 3: Environment Setup

#### .env 파일 (통합)
```
# Publ Console
PUBL_ID=your_email@example.com
PUBL_PW=your_password

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
```

#### requirements.txt
```
playwright>=1.40.0
python-dotenv>=1.0.0
supabase>=2.0.0
```

### Phase 4: Execution Script

#### run.command (macOS)
```bash
#!/bin/bash
cd "$(dirname "$0")"
.venv/bin/python -m src.main
```

---

## Key Features

### 1. 통합 실행
- 단일 스크립트로 다운로드 → 동기화 자동 실행
- 더블클릭으로 실행 가능한 `.command` 파일

### 2. 증분 동기화
- 기존 데이터와 비교하여 새 레코드만 추가
- 환불 상태 변경 자동 감지 및 업데이트

### 3. 세션 관리
- 로그인 세션 저장으로 재로그인 최소화
- 세션 만료 시 자동 재로그인

### 4. 에러 핸들링
- 네트워크 오류 재시도
- 상세 에러 로깅

### 5. 파일 관리
- 처리 완료된 CSV 파일 자동 아카이브
- 타임스탬프 기반 파일 명명

---

## Execution Flow

```
1. 실행 시작
   ↓
2. 환경변수 로드 및 검증
   ↓
3. [다운로드] publ.biz 로그인
   - 저장된 세션 확인
   - 세션 만료 시 재로그인
   ↓
4. [다운로드] 데이터 다운로드
   - 회원 목록
   - 주문 목록
   - 환불 목록
   ↓
5. [동기화] Supabase 연결
   ↓
6. [동기화] 데이터 동기화
   - 회원 → publ-member-db
   - 주문 → publ-order-db
   - 환불 → publ-refund-db (상태 업데이트 포함)
   ↓
7. [정리] CSV 파일 아카이브
   ↓
8. 결과 요약 출력
   ↓
9. 완료
```

---

## Dependencies

| 패키지 | 용도 |
|--------|------|
| `playwright` | 브라우저 자동화 (publ.biz 로그인 및 다운로드) |
| `python-dotenv` | 환경변수 관리 |
| `supabase` | Supabase 데이터베이스 연동 |

---

## Testing Checklist

- [ ] 환경변수 로드 확인
- [ ] publ.biz 로그인 성공
- [ ] 회원 데이터 다운로드 성공
- [ ] 주문 데이터 다운로드 성공
- [ ] 환불 데이터 다운로드 성공
- [ ] Supabase 연결 성공
- [ ] 회원 데이터 동기화 (신규 INSERT)
- [ ] 주문 데이터 동기화 (신규 INSERT)
- [ ] 환불 데이터 동기화 (INSERT + UPDATE)
- [ ] CSV 파일 아카이브

---

## Notes

- 브라우저는 기본적으로 헤드리스 모드로 실행 (디버깅 시 `HEADLESS=False` 설정)
- CSV 파일은 UTF-8 BOM 인코딩으로 처리
- Supabase 배치 삽입은 100개 단위로 수행
