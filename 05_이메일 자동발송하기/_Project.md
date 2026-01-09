# 이메일 자동발송 시스템

## 프로젝트 개요

CMDSPACE 수강생 대상 이메일 자동 발송 시스템

## 현재 상태: ✅ 기본 세팅 완료

## 진행 상황

### 2025-01-09: 초기 세팅 완료

- [x] Resend 서비스 선정 및 계정 설정
- [x] Node.js + TypeScript 프로젝트 초기화
- [x] 도메인 인증 완료 (`cmdspace.kr`)
- [x] 이메일 발송 함수 구현 (`sendEmail`, `sendBulkEmails`)
- [x] 테스트 이메일 발송 성공

### 설정 정보

| 항목 | 값 |
|------|-----|
| 서비스 | Resend |
| 발신 도메인 | cmdspace.kr |
| 발신자명 | CMDSPACE |
| 발신 이메일 | noreply@cmdspace.kr |

## 파일 구조

```
05_이메일 자동발송하기/
├── src/
│   ├── index.ts          # 테스트 실행
│   ├── send-email.ts     # 발송 함수
│   └── types.ts          # 타입 정의
├── docs/research/        # 리서치 문서
├── .env                  # 환경변수 (Git 제외)
├── .env.example          # 환경변수 템플릿
├── package.json
├── tsconfig.json
└── README.md             # 개발 문서 (영문)
```

## 다음 단계 (예정)

- [ ] 이메일 템플릿 시스템 구축
- [ ] 수강생 데이터 연동 (Airtable/Supabase)
- [ ] 자동 발송 스케줄링
- [ ] 발송 로그 및 통계

## 참고 자료

- [Resend 공식 문서](https://resend.com/docs)
- `docs/research/` 폴더 내 리서치 문서
