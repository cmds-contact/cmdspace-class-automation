# 데이터 동기화 SyncDataJob 오류 수정

- **작업일시**: 2025-12-16 11:26
- **작업자**: Claude AI
- **상태**: 완료

---

## 문제 현상

웹 대시보드에서 "데이터 동기화" 버튼 클릭 시 실패

### 에러 메시지 (로그에서 확인)
```
- undefined method `click' for nil
- Python 다운로드 실패
- 회원 CSV 파일을 찾을 수 없습니다
- 주문 CSV 파일을 찾을 수 없습니다
- 환불 CSV 파일을 찾을 수 없습니다
```

---

## 원인 분석

### 근본 원인
`SyncDataJob`에서 Python 스크립트를 실행할 때 shell 호환성 문제 발생

### 상세 원인
- Ruby의 백틱(`) 명령은 기본적으로 `/bin/sh`를 사용
- `source` 명령어는 bash 전용 명령어로 `/bin/sh`에서 작동하지 않음
- Python 가상환경 활성화 실패 → Python 스크립트 실행 실패 → CSV 다운로드 실패

### 문제 코드 위치
`app/jobs/sync_data_job.rb:79`

---

## 수정 내용

### 변경 파일
- `app/jobs/sync_data_job.rb`

### 변경 내용

**수정 전:**
```ruby
command = "cd #{escaped_dir} && source .venv/bin/activate && python -m src.main 2>&1"
```

**수정 후:**
```ruby
command = "/bin/bash -c 'cd #{escaped_dir} && source .venv/bin/activate && python -m src.main 2>&1'"
```

### 변경 이유
- `/bin/bash -c`를 명시적으로 사용하여 bash 셸에서 명령어 실행
- `source` 명령어가 정상적으로 작동하도록 보장

---

## 테스트 결과

### 수동 테스트 (Python 다운로드)
```
다운로드 결과:
  members: 251216_112403_members.csv
  orders: 251216_112403_orders_latest.csv
  refunds: 251216_112403_refunds.csv
소요 시간: 9.9초
```

### SyncDataJob 실행 테스트
```
STEP 1: 데이터 다운로드 (Python) - 성공
STEP 2: 데이터베이스 동기화 - 성공
  - 회원: 1933건 (신규 0)
  - 주문: 300건 (신규 0)
  - 환불: 65건 (신규 0)
STEP 3: 파일 아카이브 - 성공 (6개 파일 이동)
총 소요 시간: 11.8초
```

---

## 영향 범위

- 웹 대시보드의 "데이터 동기화" 버튼 정상 작동
- 예약된 동기화 작업(있다면) 정상 작동

---

## 관련 파일

| 파일 | 역할 |
|------|------|
| `app/jobs/sync_data_job.rb` | 동기화 작업 실행 (수정됨) |
| `app/services/data_syncer.rb` | CSV → DB 동기화 |
| `app/services/file_archiver.rb` | CSV 파일 아카이브 |
| `python/src/main.py` | Python 다운로드 진입점 |
| `python/src/downloader.py` | Playwright 기반 다운로더 |
| `python/src/config.py` | Python 설정 |
