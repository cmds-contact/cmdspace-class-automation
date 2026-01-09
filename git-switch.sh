#!/bin/bash
# 폴더별 브랜치 전환 스크립트
# 사용법: ./git-switch.sh [01|02|03|04|05]

cd "$(dirname "$0")"

case "$1" in
  01) BRANCH="feature/01-publ-manager" ;;
  02) BRANCH="feature/02-payment-template" ;;
  03) BRANCH="feature/03-payment-site" ;;
  04) BRANCH="feature/04-payment-generator" ;;
  05) BRANCH="feature/05-email-sender" ;;
  main) BRANCH="main" ;;
  *)
    echo "사용법: ./git-switch.sh [01|02|03|04|05|main]"
    echo ""
    echo "브랜치 목록:"
    echo "  01 - feature/01-publ-manager"
    echo "  02 - feature/02-payment-template"
    echo "  03 - feature/03-payment-site"
    echo "  04 - feature/04-payment-generator"
    echo "  05 - feature/05-email-sender"
    echo "  main - main"
    exit 1
    ;;
esac

git checkout "$BRANCH"
echo "현재 브랜치: $BRANCH"
