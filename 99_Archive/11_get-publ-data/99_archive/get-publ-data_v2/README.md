# PUBL 콘솔 자동화 프로젝트

PUBL 콘솔(https://console.publ.biz)에 자동으로 로그인하는 Python 스크립트입니다.

## 📋 요구사항

- Python 3.7 이상
- Chrome 브라우저

## 🚀 설치 방법

1. **필요한 패키지 설치**
```bash
pip install -r requirements.txt
```

2. **환경변수 설정**
`.env` 파일이 이미 생성되어 있으며, 로그인 정보가 포함되어 있습니다.

## 💻 사용 방법

```bash
python publ_login.py
```

## 📁 파일 구조

- `publ_login.py` - 메인 자동화 스크립트
- `.env` - 환경변수 (이메일, 비밀번호)
- `requirements.txt` - 필요한 Python 패키지 목록
- `.gitignore` - Git 버전 관리 제외 파일 목록

## 🔒 보안

- `.env` 파일은 `.gitignore`에 포함되어 있어 Git에 커밋되지 않습니다.
- 민감한 정보는 절대 코드에 직접 작성하지 마세요.

## 📝 작동 방식

1. Chrome 드라이버 자동 설치 및 설정
2. PUBL 콘솔 페이지로 이동
3. 이메일 입력
4. 비밀번호 입력
5. 로그인 버튼 클릭
6. 로그인 완료 확인

## ⚠️ 주의사항

- 첫 실행 시 Chrome 드라이버가 자동으로 다운로드됩니다.
- 네트워크 상태에 따라 로딩 시간이 달라질 수 있습니다.

