#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "PUBL DATA MANAGER"
echo "========================================"
echo ""

# 가상환경 경로 (절대 경로)
VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON="$VENV_DIR/bin/python3"
PIP="$VENV_DIR/bin/pip"

# 가상환경이 깨져있으면 .trash로 이동
if [ -d "$VENV_DIR" ] && [ ! -x "$PYTHON" ]; then
    echo "가상환경이 손상되었습니다. 재생성합니다..."
    mkdir -p "$SCRIPT_DIR/.trash"
    mv "$VENV_DIR" "$SCRIPT_DIR/.trash/.venv_$(date +%Y%m%d_%H%M%S)"
fi

# 가상환경 생성 (없는 경우)
if [ ! -d "$VENV_DIR" ]; then
    echo "가상환경을 생성합니다..."
    python3 -m venv "$VENV_DIR"
fi

# 가상환경 python 확인
if [ ! -x "$PYTHON" ]; then
    echo "오류: 가상환경 생성 실패"
    exit 1
fi

# 의존성 확인 및 설치
"$PYTHON" -c "import dotenv" 2>/dev/null || {
    echo "필요한 패키지를 설치합니다..."
    "$PIP" install -r requirements.txt --quiet
    "$PYTHON" -m playwright install chromium
}

# 실행
"$PYTHON" -m src.main

echo ""
echo "========================================"
echo "완료!"
echo "========================================"
