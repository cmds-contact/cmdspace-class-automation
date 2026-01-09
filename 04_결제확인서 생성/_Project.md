# 결제확인서 생성 프로젝트

## 개요

커맨드스페이스 결제확인서를 PDF로 생성하고 Cloudflare R2에 업로드하여 고객에게 이메일로 발송하는 시스템

## 진행 상황

### 완료된 작업

- [x] **HTML 템플릿 제작** - 한영 병기 결제확인서 템플릿 (`payment_confirmation_bilingual_v1.html`)
- [x] **PDF 변환** - HTML을 PDF로 변환 완료
- [x] **Cloudflare R2 설정**
  - [x] wrangler CLI 설치
  - [x] Cloudflare 로그인
  - [x] `payment-confirmations` 버킷 생성
  - [x] Public Access 활성화
- [x] **PDF 업로드** - 랜덤 UUID 파일명으로 업로드 완료

### 미완료 작업

- [ ] 주문 데이터 기반 PDF 자동 생성
- [ ] 이메일 발송 연동
- [ ] 커스텀 도메인 연결 (선택사항)

## 기술 스택

| 구분 | 기술 |
|------|------|
| 스토리지 | Cloudflare R2 |
| CLI 도구 | wrangler |
| 템플릿 | HTML/CSS (A4 규격) |

## R2 버킷 정보

| 항목 | 값 |
|------|-----|
| 버킷 이름 | `payment-confirmations` |
| 공개 URL | `https://pub-71bab14911324382a16a4f5cb2a8c58a.r2.dev` |
| 접근 방식 | Public (UUID 기반 보안) |

## 파일 구조

```
04_결제확인서 생성/
├── .claude/
│   └── CLAUDE.md
├── payment_confirmation_bilingual_v1.html  # HTML 템플릿
├── payment_confirmation_bilingual_v1.pdf   # 생성된 PDF
├── DEVELOPMENT.md                          # 개발 문서 (영어)
└── _Project.md                             # 프로젝트 현황 (한국어)
```

## 업로드된 파일

| 파일명 | URL | 날짜 |
|--------|-----|------|
| eddf24c7-2bbe-46a4-8bd4-b90731cbb59b.pdf | [링크](https://pub-71bab14911324382a16a4f5cb2a8c58a.r2.dev/eddf24c7-2bbe-46a4-8bd4-b90731cbb59b.pdf) | 2026-01-09 |

## 다음 단계

1. **PDF 자동 생성** - 주문 데이터를 받아 템플릿에 채워 PDF 생성
2. **이메일 발송** - 생성된 PDF URL을 고객 이메일로 발송
3. **(선택) 커스텀 도메인** - `files.cmdspace.kr` 등으로 URL 브랜딩

## 관련 명령어

```bash
# PDF 업로드
UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')
wrangler r2 object put "payment-confirmations/${UUID}.pdf" \
  --file="파일경로.pdf" \
  --content-type="application/pdf" \
  --remote
```

---

*마지막 업데이트: 2026-01-09*
