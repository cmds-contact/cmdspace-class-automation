#!/bin/bash
cd "$(dirname "$0")"

# 가상환경의 Python을 직접 사용
.venv/bin/python download_all.py

echo ""
echo "downloads 폴더를 확인하세요"
echo ""
sleep 2

# 터미널 창 자동 닫기
osascript -e 'tell application "Terminal" to close front window' &
exit 0
