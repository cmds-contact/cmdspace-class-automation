#!/usr/bin/env python3
"""
HTML 파일을 PDF로 변환하는 스크립트
"""
import os
from pathlib import Path

try:
    from weasyprint import HTML
except ImportError:
    print("weasyprint이 설치되어 있지 않습니다.")
    print("설치 명령: pip3 install weasyprint")
    exit(1)

def convert_html_to_pdf():
    # 현재 스크립트의 디렉토리
    script_dir = Path(__file__).parent
    html_file = script_dir / 'payment_confirmation_bilingual_v0.5.html'
    output_file = script_dir / 'payment_confirmation_bilingual_v0.5.pdf'
    
    # HTML 파일 존재 확인
    if not html_file.exists():
        print(f'HTML 파일을 찾을 수 없습니다: {html_file}')
        exit(1)
    
    print('PDF 변환을 시작합니다...')
    
    try:
        # HTML을 PDF로 변환
        HTML(filename=str(html_file)).write_pdf(str(output_file))
        print(f'PDF 변환이 완료되었습니다: {output_file}')
    except Exception as e:
        print(f'PDF 변환 중 오류가 발생했습니다: {e}')
        exit(1)

if __name__ == '__main__':
    convert_html_to_pdf()

