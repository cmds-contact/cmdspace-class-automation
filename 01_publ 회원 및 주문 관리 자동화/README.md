# publ-data-manager

publ.biz 데이터를 자동으로 다운로드하여 Airtable에 동기화하는 통합 솔루션입니다.

## 기능

- publ.biz 콘솔에서 회원/주문/환불 데이터 자동 다운로드
- Airtable에 데이터 동기화 (Linked Record 자동 연결)
- 환불 상태 변경 자동 감지 및 업데이트
- 세션 관리로 재로그인 최소화
- 실행 로그 파일 저장 (`logs/` 폴더)

> **운영자 가이드**: 비개발자용 사용 설명서는 [docs/OPERATION_GUIDE.md](docs/OPERATION_GUIDE.md)를 참조하세요.

## 빠른 시작

### 1. 더블클릭 실행

`run.command` 파일을 더블클릭하면 자동으로 실행됩니다.

### 2. 터미널에서 실행

```bash
# 가상환경 활성화
source .venv/bin/activate

# 실행
python -m src.main
```

## 설치

### 최초 설치

```bash
# 가상환경 생성
python3 -m venv .venv

# 가상환경 활성화
source .venv/bin/activate

# 패키지 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

### 환경변수 설정

`.env` 파일에 인증 정보를 설정합니다:

```
# Publ Console
PUBL_ID=your_email@example.com
PUBL_PW=your_password

# Airtable
AIRTABLE_API_KEY=your-api-key
AIRTABLE_BASE_ID=your-base-id
```

## 데이터 흐름

```
publ.biz 콘솔
    │
    ▼ (Playwright 자동화)
downloads/
    ├── YYMMDD_HHMMSS_members.csv
    ├── YYMMDD_HHMMSS_orders_latest.csv
    └── YYMMDD_HHMMSS_refunds.csv
    │
    ▼ (pyairtable)
Airtable
    ├── Members
    ├── Orders (→ Member 연결)
    └── Refunds (→ Orders 연결)
    │
    ▼ (완료 후)
archive/YYYYMMDD/
    └── (처리된 CSV 파일)
```

## 프로젝트 구조

```
publ-data-manager/
├── src/
│   ├── __init__.py
│   ├── config.py          # 설정 관리
│   ├── logger.py          # 로깅 설정
│   ├── utils.py           # 공통 유틸리티
│   ├── downloader.py      # 데이터 다운로드
│   ├── airtable_syncer.py # Airtable 동기화
│   ├── data_analyzer.py   # 데이터 분석
│   └── main.py            # 메인 실행
├── docs/
│   ├── OPERATION_GUIDE.md # 운영 가이드
│   └── SYSTEM_DESIGN.md   # 시스템 설계
├── downloads/             # 다운로드된 CSV
├── archive/               # 아카이브된 CSV
├── logs/                  # 실행 로그
├── .env                   # 환경변수 (git 제외)
├── .session.json          # 로그인 세션 (git 제외)
├── settings.yaml          # 운영 설정
├── requirements.txt       # Python 패키지
├── run.command            # macOS 실행 스크립트
└── README.md
```

## 모듈 설명

| 모듈 | 설명 |
|------|------|
| `config.py` | 환경변수, 경로, 테이블 설정 중앙 관리 |
| `utils.py` | 배치 처리, 가격 파싱 등 공통 함수 |
| `downloader.py` | Playwright로 publ.biz 로그인 및 CSV 다운로드 |
| `airtable_syncer.py` | Airtable 동기화 + Linked Record 연결 |
| `main.py` | 전체 워크플로우 실행 및 결과 요약 |

## Airtable 테이블

| 테이블 | 고유 키 | 동작 |
|--------|---------|------|
| `Members` | Member Code | 신규만 INSERT |
| `Orders` | Order Number | 신규만 INSERT + is_refunded 플래그 |
| `Refunds` | Order Number | INSERT + Orders is_refunded 업데이트 |

## 설정 옵션

설정은 두 파일로 분리되어 있습니다:

### .env (민감 정보)

```bash
PUBL_ID=your_email@example.com
PUBL_PW=your_password
AIRTABLE_API_KEY=your-api-key
AIRTABLE_BASE_ID=your-base-id
```

### settings.yaml (운영 설정)

```yaml
# 브라우저 설정
browser:
  headless: true          # true: 창 숨김, false: 창 표시
  timeout_seconds: 30     # 페이지 로딩 대기

# 동기화 설정
sync:
  batch_size: 100         # 한 번에 처리할 레코드 수
  timezone: "+09:00"      # 타임존 (한국)

# Airtable 테이블 이름
airtable_tables:
  members: "Members"
  orders: "Orders"
  # ...
```

## 로그 파일

실행 로그는 `logs/` 폴더에 일별로 저장됩니다:

```
logs/
├── sync_20260108.log
├── sync_20260107.log
└── ...
```
