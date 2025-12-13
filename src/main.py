"""publ-data-manager 메인 실행 스크립트

워크플로우:
1. publ.biz에서 데이터 다운로드 (회원, 주문, 환불)
2. 다운로드한 데이터를 Supabase에 동기화
3. 처리 완료된 CSV 파일 아카이브
"""

import shutil
from datetime import datetime
from pathlib import Path

from . import config
from .downloader import download_all
from .syncer import sync_all


def archive_files():
    """다운로드 폴더의 CSV 파일을 아카이브로 이동"""
    csv_files = list(config.DOWNLOAD_DIR.glob('*.csv'))
    if not csv_files:
        return 0

    # 오늘 날짜 폴더 생성
    today = datetime.now().strftime("%Y%m%d")
    archive_subdir = config.ARCHIVE_DIR / today
    archive_subdir.mkdir(exist_ok=True)

    moved = 0
    for csv_file in csv_files:
        dest = archive_subdir / csv_file.name
        # 동일 파일명 존재 시 덮어쓰기 방지
        if dest.exists():
            timestamp = datetime.now().strftime("%H%M%S")
            dest = archive_subdir / f"{csv_file.stem}_{timestamp}{csv_file.suffix}"
        shutil.move(str(csv_file), str(dest))
        moved += 1

    return moved


def print_summary(download_files, sync_results, archived_count):
    """실행 결과 요약 출력"""
    print("\n" + "=" * 60)
    print("실행 결과 요약")
    print("=" * 60)

    # 다운로드 결과
    print("\n[다운로드]")
    for data_type, file_path in download_files.items():
        filename = Path(file_path).name if file_path else "실패"
        print(f"  {data_type}: {filename}")

    # 동기화 결과
    print("\n[동기화]")
    for data_type, result in sync_results.items():
        if 'error' in result:
            print(f"  {data_type.upper()}: 오류 - {result['error']}")
        elif 'updated' in result:
            print(f"  {data_type.upper()}: {result['new']}개 신규, {result['updated']}개 업데이트")
        else:
            print(f"  {data_type.upper()}: {result['new']}개 신규")

    # 아카이브 결과
    print(f"\n[아카이브]")
    print(f"  {archived_count}개 파일 이동")


def main():
    """메인 실행 함수"""
    start_time = datetime.now()

    print("\n" + "=" * 60)
    print("PUBL DATA MANAGER")
    print(f"시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 환경변수 검증
    try:
        config.validate_config()
    except ValueError as e:
        print(f"\n설정 오류:\n{e}")
        print("\n.env 파일을 확인해주세요.")
        return

    # 디렉토리 생성
    config.ensure_directories()

    # 1. 데이터 다운로드
    print("\n" + "#" * 60)
    print("# STEP 1: 데이터 다운로드")
    print("#" * 60)

    try:
        download_files = download_all()
    except Exception as e:
        print(f"\n다운로드 오류: {e}")
        return

    # 2. Supabase 동기화
    print("\n" + "#" * 60)
    print("# STEP 2: Supabase 동기화")
    print("#" * 60)

    try:
        sync_results = sync_all()
    except Exception as e:
        print(f"\n동기화 오류: {e}")
        sync_results = {
            'members': {'error': str(e)},
            'orders': {'error': str(e)},
            'refunds': {'error': str(e)}
        }

    # 3. 파일 아카이브
    print("\n" + "#" * 60)
    print("# STEP 3: 파일 아카이브")
    print("#" * 60)

    archived_count = archive_files()
    print(f"\n{archived_count}개 파일을 archive 폴더로 이동")

    # 결과 요약
    print_summary(download_files, sync_results, archived_count)

    # 완료
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n" + "=" * 60)
    print(f"완료 시간: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"소요 시간: {duration:.1f}초")
    print("=" * 60)


if __name__ == '__main__':
    main()
