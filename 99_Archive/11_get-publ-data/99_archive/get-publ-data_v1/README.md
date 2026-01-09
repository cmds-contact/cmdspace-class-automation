# publ.biz 로그인 자동화

Playwright를 사용하여 publ.biz 콘솔에 자동으로 로그인하는 스크립트입니다.

## 📋 목차

- [기능](#-기능)
- [요구사항](#-요구사항)
- [설치 방법](#-설치-방법)
- [사용 방법](#-사용-방법)
- [환경변수 설정](#-환경변수-설정)
- [문제 해결](#-문제-해결)
- [개발 정보](#-개발-정보)

## ✨ 기능

- ✅ **자동 로그인**: publ.biz 콘솔에 자동으로 로그인
- ✅ **환경변수 지원**: `.env` 파일 또는 명령줄 인자로 로그인 정보 관리
- ✅ **에러 감지**: 로그인 실패 시 에러 메시지 자동 감지 및 출력
- ✅ **빠른 실행**: 최적화된 대기 시간으로 약 8초 내 로그인 완료
- ✅ **상세 로그**: 각 단계별 진행 상황 실시간 출력
- ✅ **스크린샷**: 오류 발생 시 자동으로 스크린샷 저장
- ✅ **브라우저 확인**: 로그인 후 30초간 브라우저를 열어두어 수동 확인 가능
- ✅ **자동 다운로드**: 멤버 목록 CSV 파일 자동 다운로드
- ✅ **중복 방지**: 다운로드 파일명에 타임스탬프 자동 추가로 덮어쓰기 방지

## 📦 요구사항

- **Node.js**: v14 이상
- **npm**: v6 이상
- **운영체제**: macOS (테스트 완료), Windows/Linux (미테스트)

## 🚀 설치 방법

### 1. 의존성 설치

```bash
npm install
```

### 2. Playwright 브라우저 설치

```bash
npm run install-playwright
```

또는

```bash
npx playwright install chromium
```

## 💻 사용 방법

### 방법 1: 환경 변수 파일 사용 (권장)

#### 1단계: `.env` 파일 생성

`.env.example` 파일을 `.env`로 복사:

```bash
cp .env.example .env
```

#### 2단계: `.env` 파일에 로그인 정보 입력

```env
PUBL_EMAIL=your-email@example.com
PUBL_PASSWORD="your-password"
```

**⚠️ 중요**: 비밀번호에 특수문자(`#`, `!`, `$` 등)가 포함된 경우 반드시 따옴표로 감싸야 합니다.

**올바른 예시:**
```env
PUBL_PASSWORD="YaxBA#W#C!8Oz1"
```

**잘못된 예시:**
```env
PUBL_PASSWORD=YaxBA#W#C!8Oz1  # '#' 이후 값이 주석으로 처리됨
```

#### 3단계: 스크립트 실행

```bash
npm run login
```

또는

```bash
node login.js
```

### 방법 2: 명령줄 인자 사용

```bash
node login.js your-email@example.com "your-password"
```

**⚠️ 주의**: 비밀번호에 특수문자가 있으면 따옴표로 감싸야 합니다.

## ⚙️ 환경변수 설정

### `.env` 파일 구조

```env
# publ.biz 로그인 정보
PUBL_EMAIL=cmdspace.official@gmail.com
PUBL_PASSWORD="YaxBA#W#C!8Oz1"
```

### 환경변수 설명

| 변수명 | 설명 | 필수 | 예시 |
|--------|------|------|------|
| `PUBL_EMAIL` | publ.biz 로그인 이메일 | ✅ | `user@example.com` |
| `PUBL_PASSWORD` | publ.biz 로그인 비밀번호 | ✅ | `"Pass#123!"` |

### 특수문자가 포함된 비밀번호 처리

비밀번호에 다음 특수문자가 포함된 경우 **반드시 따옴표**로 감싸야 합니다:

- `#` (해시/샵)
- `!` (느낌표)
- `$` (달러)
- `&` (앰퍼샌드)
- `'` (작은따옴표)
- `"` (큰따옴표)
- 공백

**예시:**
```env
PUBL_PASSWORD="MyP@ss#123!"  # 올바름
PUBL_PASSWORD='MyP@ss#123!'  # 올바름
PUBL_PASSWORD=MyP@ss#123!    # 잘못됨 - '#' 이후 주석 처리됨
```

## 🔍 실행 결과

### 성공 시

```
브라우저 시작 중...
✓ 브라우저가 시작되었습니다.
🔍 환경변수 확인:
  - EMAIL: ✓ 설정됨 (26자)
  - EMAIL 값: cmd***com
  - PASSWORD: ✓ 설정됨 (14자)
  - PASSWORD 값: Ya***z1
✓ 새 페이지가 생성되었습니다.
publ.biz 로그인 페이지로 이동 중...
✓ 페이지 이동 완료
페이지 로드 대기 중...
✓ 로그인 폼이 로드되었습니다.
로그인 정보 입력 중...
  - 이메일 필드 찾기 시도: input[name="email"]
✓ 이메일 입력 완료 (26자 입력됨)
  입력된 값: cmd***com
  - 비밀번호 필드 찾기 시도: input[name="password"][type="password"]
✓ 비밀번호 입력 완료 (14자 입력됨)
  입력된 값: Ya***z1
  - 로그인 버튼 찾기 시도: button[type="submit"]:has-text("Login")
  - 버튼 활성화 상태: true
✓ 로그인 버튼 클릭 완료
로그인 처리 중...
초기 URL: https://console.publ.biz/?type=enter
현재 URL: https://console.publ.biz/all-channels?page=1&limit=15&markChannelAs=RUNNING
✅ 로그인 성공!

지정된 페이지로 이동 중...
목표 URL: https://console.publ.biz/channels/L2NoYW5uZWxzLzE3Njkx/members/registered-users
현재 페이지: https://console.publ.biz/channels/L2NoYW5uZWxzLzE3Njkx/members/registered-users
✓ 목표 페이지에 성공적으로 도달했습니다.
✓ 목표 페이지 확인 완료. 다운로드 버튼을 찾습니다.

다운로드 버튼 찾는 중...
✓ 다운로드 버튼 발견: "All Member download (CSV)" (선택자: button:has-text("CSV"))
✓ 다운로드 버튼 클릭 완료
✅ 파일 다운로드 완료: /path/to/downloads/All member list_251122_2024-11-22T13-45-30.csv

브라우저를 열어둡니다. 수동으로 닫아주세요.
작업을 계속하려면 Ctrl+C를 눌러 스크립트를 종료하세요.
```

### 실패 시

```
❌ 로그인 실패: Your e-mail and/or password is incorrect. Please try again. (401)
```

## 🛠 문제 해결

### 1. 비밀번호가 제대로 입력되지 않음

**증상:**
```
PASSWORD: ✓ 설정됨 (5자)  # 실제로는 14자여야 함
```

**원인:** `.env` 파일에서 `#` 문자가 주석으로 인식됨

**해결:**
```env
# 잘못된 예시
PUBL_PASSWORD=YaxBA#W#C!8Oz1

# 올바른 예시
PUBL_PASSWORD="YaxBA#W#C!8Oz1"
```

### 2. 브라우저가 실행되지 않음

**증상:**
```
❌ 오류 발생: browserType.launch: Target page, context or browser has been closed
```

**해결:**
1. Playwright 브라우저 재설치:
```bash
npx playwright install chromium
```

2. 권한 문제 확인 (macOS):
```bash
# 터미널에 전체 디스크 접근 권한 부여
시스템 환경설정 > 보안 및 개인 정보 보호 > 개인 정보 보호 > 전체 디스크 접근 권한
```

### 3. 페이지 로딩 타임아웃

**증상:**
```
❌ 오류 발생: page.goto: Timeout 30000ms exceeded.
```

**해결:**
- 인터넷 연결 확인
- 방화벽 설정 확인
- VPN 사용 시 비활성화 후 재시도

### 4. 로그인 실패 (401 오류)

**증상:**
```
❌ 로그인 실패: Your e-mail and/or password is incorrect. Please try again. (401)
```

**해결:**
1. `.env` 파일의 이메일/비밀번호 확인
2. 비밀번호 특수문자 처리 확인 (따옴표로 감싸기)
3. publ.biz 웹사이트에서 직접 로그인하여 계정 정보 확인

### 5. 환경변수가 로드되지 않음

**증상:**
```
❌ 이메일과 비밀번호가 필요합니다.
```

**해결:**
1. `.env` 파일이 프로젝트 루트에 있는지 확인
2. `.env` 파일 저장 확인 (Ctrl+S / Cmd+S)
3. 파일 이름이 정확히 `.env`인지 확인 (`.env.txt` 아님)

### 6. 다운로드 파일이 덮어쓰기됨

**증상:**
- "All Member download (CSV)" 버튼을 여러 번 클릭해도 새로운 파일이 생성되지 않음
- 기존 파일만 업데이트됨

**원인:**
- 서버에서 제공하는 파일명(`All member list_251122.csv`)을 그대로 사용하여 같은 경로에 저장
- `download.saveAs()` 메서드가 기존 파일을 덮어쓰기함

**해결:**
- 파일명에 타임스탬프를 자동으로 추가하여 중복 방지
- 예: `All member list_251122_2024-11-22T13-45-30.csv` 형식으로 저장
- 각 다운로드마다 고유한 파일명 생성

**참고:**
- 다운로드된 파일은 `./downloads/` 폴더에 저장됩니다
- 파일명 형식: `[원본파일명]_[YYYY-MM-DDTHH-MM-SS].[확장자]`

## 📁 프로젝트 구조

```
publ 데이터 처리하기/
├── login.js              # 메인 로그인 스크립트
├── package.json          # 프로젝트 의존성 및 스크립트
├── package-lock.json     # 의존성 잠금 파일
├── .env                  # 환경변수 파일 (git에 포함되지 않음)
├── .env.example          # 환경변수 예시 파일
├── .gitignore            # Git 무시 파일 목록
├── README.md             # 프로젝트 문서 (이 파일)
├── CHANGELOG.md          # 변경 이력
├── downloads/            # 다운로드된 파일 저장 폴더
│   └── All member list_*.csv  # 다운로드된 멤버 목록 CSV 파일들
└── node_modules/         # 설치된 패키지 (git에 포함되지 않음)
```

## 🔒 보안

- `.env` 파일은 `.gitignore`에 포함되어 Git에 커밋되지 않습니다
- 로그 출력 시 이메일/비밀번호는 일부만 표시됩니다 (마스킹 처리)
- 환경변수는 프로세스 메모리에만 존재하며 파일로 저장되지 않습니다

**⚠️ 주의사항:**
- `.env` 파일을 절대 공유하거나 Git에 커밋하지 마세요
- 명령줄 인자로 비밀번호를 입력하면 쉘 히스토리에 남을 수 있으므로 `.env` 파일 사용을 권장합니다

## 🎯 성능

- **로그인 시간**: 약 8초
- **브라우저 시작**: 약 2초
- **페이지 로딩**: 약 3초
- **로그인 처리**: 약 3초

## 🐛 디버깅

### 상세 로그 확인

스크립트는 기본적으로 상세한 로그를 출력합니다:
- ✓ 성공 단계
- ⚠️ 경고 메시지
- ❌ 오류 메시지

### 스크린샷 확인

오류 발생 시 자동으로 스크린샷이 저장됩니다:
- `error-screenshot.png`: 오류 발생 시점의 화면
- `page-load-screenshot.png`: 페이지 로드 실패 시 화면

## 📝 개발 정보

### 기술 스택

- **Playwright** v1.40.0: 브라우저 자동화
- **Node.js**: JavaScript 런타임
- **dotenv** v16.3.1: 환경변수 관리

### 브라우저 설정

- **브라우저**: Chromium
- **헤드리스 모드**: 비활성화 (브라우저 창 표시)
- **slowMo**: 100ms (각 동작 사이 지연)
- **뷰포트**: 1920x1080

### 선택자 정보

스크립트에서 사용하는 CSS 선택자:

| 요소 | 선택자 | 설명 |
|------|--------|------|
| 이메일 입력 | `input[name="email"]` | 이메일 입력 필드 |
| 비밀번호 입력 | `input[name="password"][type="password"]` | 비밀번호 입력 필드 |
| 로그인 버튼 | `button[type="submit"]:has-text("Login")` | 로그인 제출 버튼 |

## 📄 라이선스

이 프로젝트는 내부 사용을 위한 것입니다.

## 👥 기여

CMDSPACE Automation Project

## 📞 지원

문제가 발생하거나 질문이 있으시면:
1. [CHANGELOG.md](./CHANGELOG.md)에서 알려진 문제 확인
2. 문제 해결 섹션 참조
3. 개발팀에 문의

---

**마지막 업데이트**: 2024-11-22  
**버전**: 1.1.0
