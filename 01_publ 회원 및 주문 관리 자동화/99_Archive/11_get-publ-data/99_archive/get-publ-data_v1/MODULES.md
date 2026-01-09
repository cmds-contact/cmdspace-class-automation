# 모듈화 구조 가이드

이 프로젝트는 각 단계를 독립적인 모듈로 분리하여 구성되었습니다.

## 📁 프로젝트 구조

```
publ 데이터 처리하기/
├── main.js                 # 전체 워크플로우 실행 파일
├── test-modules.js         # 개별 모듈 테스트 스크립트
├── login.js                # 기존 로그인 스크립트 (호환성 유지)
├── modules/                # 단계별 모듈
│   ├── browser-init.js     # 1단계: 브라우저 초기화 및 환경 설정
│   ├── login.js            # 2단계: 로그인 프로세스
│   ├── download-members.js # 3단계: 회원 정보 CSV 다운로드
│   ├── download-orders.js  # 4단계: 주문 목록 CSV 다운로드
│   └── keep-browser.js     # 마지막: 브라우저 유지
├── utils/                  # 유틸리티 함수
│   └── download-helpers.js # 다운로드 관련 헬퍼 함수
└── package.json            # 프로젝트 설정 및 스크립트
```

## 🚀 사용 방법

### 1. 전체 워크플로우 실행

모든 단계를 순차적으로 실행:

```bash
npm start
# 또는
node main.js
```

### 2. 개별 모듈 테스트

특정 모듈만 테스트하고 싶을 때:

```bash
# 브라우저 초기화 테스트
npm run test:browser
# 또는
node test-modules.js browser-init

# 로그인만 테스트
npm run test:login
# 또는
node test-modules.js login

# 회원 정보 다운로드 테스트 (로그인 후 실행)
npm run test:members
# 또는
node test-modules.js download-members

# 주문 목록 다운로드 테스트 (로그인 후 실행)
npm run test:orders
# 또는
node test-modules.js download-orders
```

## 📦 모듈 상세 설명

### 1. browser-init.js

**기능**: 브라우저 초기화 및 환경 설정

**Export 함수**:
- `initializeBrowser()`: 브라우저, 컨텍스트, 페이지, 다운로드 경로 반환

**사용 예시**:
```javascript
const { initializeBrowser } = require('./modules/browser-init');
const { browser, context, page, downloadPath } = await initializeBrowser();
```

### 2. login.js

**기능**: 로그인 프로세스 전체 관리

**Export 함수**:
- `getLoginCredentials()`: 환경변수 또는 명령줄 인자에서 로그인 정보 가져오기
- `performLogin(page, email, password)`: 로그인 프로세스 전체 실행
- `navigateToLoginPage(page)`: 로그인 페이지로 이동
- `fillLoginForm(page, email, password)`: 로그인 폼에 정보 입력
- `clickLoginButton(page)`: 로그인 버튼 클릭
- `verifyLoginResult(page)`: 로그인 결과 확인

**사용 예시**:
```javascript
const { getLoginCredentials, performLogin } = require('./modules/login');
const credentials = getLoginCredentials();
if (credentials) {
  const success = await performLogin(page, credentials.email, credentials.password);
}
```

### 3. download-members.js

**기능**: 회원 정보 CSV 파일 다운로드

**Export 함수**:
- `downloadMembersCSV(page, downloadPath)`: 회원 정보 다운로드 전체 프로세스
- `navigateToMembersPage(page)`: 회원 정보 페이지로 이동
- `findAndClickDownloadButton(page, downloadPath)`: 다운로드 버튼 찾기 및 클릭

**사용 예시**:
```javascript
const { downloadMembersCSV } = require('./modules/download-members');
await downloadMembersCSV(page, downloadPath);
```

### 4. download-orders.js

**기능**: 주문 목록 CSV 파일 다운로드 (첫번째/마지막 페이지)

**Export 함수**:
- `downloadOrdersCSV(page, downloadPath)`: 주문 목록 다운로드 전체 프로세스
- `navigateToFirstOrderPage(page)`: 첫번째 페이지로 이동
- `findLastPageNumber(page)`: 마지막 페이지 번호 찾기
- `navigateToLastOrderPage(page, lastPageNumber)`: 마지막 페이지로 이동

**사용 예시**:
```javascript
const { downloadOrdersCSV } = require('./modules/download-orders');
await downloadOrdersCSV(page, downloadPath);
```

### 5. keep-browser.js

**기능**: 브라우저를 열어두고 사용자가 수동으로 확인할 수 있도록 대기

**Export 함수**:
- `keepBrowserOpen()`: 무한 대기 (Ctrl+C로 종료)

**사용 예시**:
```javascript
const { keepBrowserOpen } = require('./modules/keep-browser');
await keepBrowserOpen();
```

### 6. utils/download-helpers.js

**기능**: 다운로드 관련 유틸리티 함수

**Export 함수**:
- `downloadCSVFromPage(page, downloadPath, pageLabel)`: CSV 다운로드 헬퍼 함수
- `getRecentDownloadedFiles(downloadPath, timeWindowMs)`: 최근 다운로드 파일 확인

**사용 예시**:
```javascript
const { downloadCSVFromPage } = require('./utils/download-helpers');
await downloadCSVFromPage(page, downloadPath, '첫번째');
```

## 🔧 커스터마이징

### 새로운 모듈 추가하기

1. `modules/` 디렉토리에 새 모듈 파일 생성
2. 필요한 함수 export
3. `main.js`에서 모듈 import 및 실행
4. `test-modules.js`에 테스트 케이스 추가

**예시**:
```javascript
// modules/my-new-module.js
async function myNewFunction(page, downloadPath) {
  // 새로운 기능 구현
}

module.exports = {
  myNewFunction
};

// main.js에 추가
const { myNewFunction } = require('./modules/my-new-module');
await myNewFunction(page, downloadPath);
```

### 모듈 실행 순서 변경하기

`main.js`에서 모듈 호출 순서를 변경하면 됩니다:

```javascript
// main.js
async function runWorkflow() {
  // ... 브라우저 초기화 및 로그인 ...
  
  // 모듈 실행 순서 변경 가능
  await downloadOrdersCSV(page, downloadPath);  // 주문 목록 먼저
  await downloadMembersCSV(page, downloadPath); // 회원 정보 나중에
}
```

## 🧪 테스트 전략

### 단위 테스트

각 모듈을 독립적으로 테스트:

```bash
# 각 모듈별로 테스트
node test-modules.js browser-init
node test-modules.js login
node test-modules.js download-members
node test-modules.js download-orders
```

### 통합 테스트

전체 워크플로우 테스트:

```bash
npm start
```

## 💡 장점

1. **모듈별 독립 테스트**: 각 단계를 개별적으로 테스트 가능
2. **코드 재사용성**: 모듈을 다른 프로젝트에서도 활용 가능
3. **유지보수 용이성**: 특정 기능만 수정 시 해당 모듈만 수정하면 됨
4. **확장성**: 새로운 단계 추가가 쉬움
5. **가독성**: 코드 구조가 명확하고 이해하기 쉬움

## 📝 주의사항

- 각 모듈은 독립적으로 실행 가능하지만, 일부 모듈은 로그인이 선행되어야 합니다
- `download-members`와 `download-orders` 모듈은 로그인 후에 실행해야 합니다
- 브라우저는 `browser-init` 모듈에서 생성되며, 다른 모듈에서 재사용됩니다

---

**마지막 업데이트**: 2024-11-22  
**버전**: 2.0.0 (모듈화)

