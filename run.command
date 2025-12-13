#!/bin/bash
cd "$(dirname "$0")"

echo "========================================"
echo "PUBL DATA MANAGER"
echo "========================================"
echo ""

# 가상환경 확인 및 활성화
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "가상환경이 없습니다. 설치를 진행합니다..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    playwright install chromium
fi

# 실행
python -m src.main

echo ""
echo "========================================"
echo "완료! 3초 후 창이 닫힙니다..."
echo "========================================"
sleep 3

# 터미널 창 자동 닫기
osascript -e 'tell application "Terminal" to close front window' &
exit 0
