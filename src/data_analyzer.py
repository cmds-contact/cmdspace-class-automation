"""데이터 불일치 분석 모듈

Airtable과 publ CSV 간의 데이터 불일치를 분석하고 리포트 생성.
"""

import argparse
import csv
import glob
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from pyairtable import Api

from . import config


def get_airtable_api() -> Api:
    """Airtable API 클라이언트 생성"""
    return Api(config.AIRTABLE_API_KEY)


def load_airtable_members(api: Api) -> dict[str, dict[str, Any]]:
    """Airtable에서 모든 Members 레코드 조회

    Args:
        api: Airtable API 클라이언트

    Returns:
        member_code -> {id, fields} 매핑 딕셔너리
    """
    table = api.table(config.AIRTABLE_BASE_ID, config.AIRTABLE_TABLES['members'])

    result: dict[str, dict[str, Any]] = {}
    for record in table.all():
        member_code = record['fields'].get('Member Code')
        if member_code:
            result[member_code] = {
                'id': record['id'],
                'fields': record['fields']
            }

    return result


def load_csv_members(csv_path: str) -> dict[str, dict[str, Any]]:
    """CSV 파일에서 회원 데이터 로드

    Args:
        csv_path: CSV 파일 경로

    Returns:
        member_code -> {row_data} 매핑 딕셔너리
    """
    result: dict[str, dict[str, Any]] = {}

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            member_code = row.get('Member Code')
            if member_code:
                result[member_code] = dict(row)

    return result


def find_latest_csv(pattern: str = '*_members.csv') -> str | None:
    """최신 members CSV 파일 찾기

    downloads 폴더와 archive 폴더에서 검색

    Args:
        pattern: glob 패턴

    Returns:
        파일 경로 또는 None
    """
    # downloads 폴더에서 먼저 검색
    downloads_files = glob.glob(str(config.DOWNLOAD_DIR / pattern))

    # archive 폴더에서도 검색
    archive_files = glob.glob(str(config.ARCHIVE_DIR / '**' / pattern), recursive=True)

    all_files = downloads_files + archive_files

    if not all_files:
        return None

    # 파일명으로 정렬 (타임스탬프 기반)
    return sorted(all_files)[-1]


def find_airtable_duplicates(
    airtable_members: dict[str, dict[str, Any]]
) -> dict[str, list[str]]:
    """Airtable에서 중복 Member Code 찾기

    Note: load_airtable_members는 이미 중복을 덮어쓰므로,
    이 함수는 table.all()을 직접 호출하여 중복 검사

    Args:
        airtable_members: 사용하지 않음 (API 재호출 필요)

    Returns:
        member_code -> [record_id1, record_id2, ...] (2개 이상인 것만)
    """
    api = get_airtable_api()
    table = api.table(config.AIRTABLE_BASE_ID, config.AIRTABLE_TABLES['members'])

    member_code_records: dict[str, list[str]] = defaultdict(list)

    for record in table.all():
        member_code = record['fields'].get('Member Code')
        if member_code:
            member_code_records[member_code].append(record['id'])

    # 2개 이상인 것만 반환
    return {
        code: ids
        for code, ids in member_code_records.items()
        if len(ids) > 1
    }


def find_discrepancies(
    airtable_members: dict[str, dict[str, Any]],
    csv_members: dict[str, dict[str, Any]]
) -> dict[str, list]:
    """Airtable과 CSV 간 불일치 레코드 찾기

    Args:
        airtable_members: Airtable 회원 데이터
        csv_members: CSV 회원 데이터

    Returns:
        {
            'only_in_airtable': [...],  # Airtable에만 있음
            'only_in_csv': [...]         # CSV에만 있음
        }
    """
    airtable_codes = set(airtable_members.keys())
    csv_codes = set(csv_members.keys())

    only_in_airtable = airtable_codes - csv_codes
    only_in_csv = csv_codes - airtable_codes

    return {
        'only_in_airtable': list(only_in_airtable),
        'only_in_csv': list(only_in_csv)
    }


def identify_test_records(
    member_codes: list[str],
    airtable_members: dict[str, dict[str, Any]]
) -> dict[str, list[str]]:
    """테스트 레코드와 정상 레코드 분류

    테스트 레코드 판별 기준:
    - Member Code가 'SUB'로 시작하지 않음
    - 이름에 '테스트', 'test', 'TEST', '임시' 포함
    - 이메일 도메인이 test.com, example.com 등

    Args:
        member_codes: 분류할 Member Code 리스트
        airtable_members: Airtable 회원 데이터

    Returns:
        {'test': [...], 'normal': [...]}
    """
    test_patterns = {
        'name_keywords': ['테스트', 'test', 'TEST', '임시', 'temp', 'demo'],
        'email_domains': ['test.com', 'example.com', 'temp.com', 'fake.com']
    }

    test_records: list[str] = []
    normal_records: list[str] = []

    for code in member_codes:
        member_data = airtable_members.get(code)
        if not member_data:
            continue

        fields = member_data['fields']
        is_test = False

        # Member Code 패턴 검사 (SUB로 시작하지 않으면 의심)
        if not code.startswith('SUB'):
            is_test = True

        # 이름 검사
        name = fields.get('Name', '') or ''
        for keyword in test_patterns['name_keywords']:
            if keyword.lower() in name.lower():
                is_test = True
                break

        # 이메일 검사
        email = fields.get('E-mail', '') or ''
        for domain in test_patterns['email_domains']:
            if email.endswith(f'@{domain}'):
                is_test = True
                break

        if is_test:
            test_records.append(code)
        else:
            normal_records.append(code)

    return {'test': test_records, 'normal': normal_records}


def print_analysis_report(
    airtable_members: dict[str, dict[str, Any]],
    csv_members: dict[str, dict[str, Any]],
    duplicates: dict[str, list[str]],
    discrepancies: dict[str, list],
    record_classification: dict[str, list[str]],
    csv_path: str
) -> None:
    """분석 결과를 콘솔에 출력

    Args:
        airtable_members: Airtable 회원 데이터
        csv_members: CSV 회원 데이터
        duplicates: 중복 레코드
        discrepancies: 불일치 레코드
        record_classification: 테스트/정상 분류
        csv_path: 분석에 사용된 CSV 파일 경로
    """
    print("\n")
    print("=" * 60)
    print("        MEMBER DATA ANALYSIS REPORT")
    print("=" * 60)

    # 요약
    print("\n[요약]")
    print(f"  - Airtable Members: {len(airtable_members)}개")
    print(f"  - publ CSV Members: {len(csv_members)}개")
    diff = len(airtable_members) - len(csv_members)
    diff_str = f"+{diff}" if diff > 0 else str(diff)
    print(f"  - 차이: {diff_str}개 {'(Airtable에 더 많음)' if diff > 0 else '(CSV에 더 많음)' if diff < 0 else '(일치)'}")
    print(f"  - 분석 CSV: {Path(csv_path).name}")

    # 중복 분석
    print("\n[Airtable 내 중복 Member Code]")
    if duplicates:
        print(f"  - {len(duplicates)}개 중복 발견!")
        for code, record_ids in list(duplicates.items())[:5]:
            print(f"    • {code}: {len(record_ids)}개 레코드")
            for rid in record_ids:
                print(f"      - {rid}")
        if len(duplicates) > 5:
            print(f"    ... 외 {len(duplicates) - 5}개")
    else:
        print("  - 없음 ✓")

    # Airtable에만 있는 레코드 (orphan)
    only_in_airtable = discrepancies.get('only_in_airtable', [])
    print(f"\n[Orphan 레코드] (Airtable에만 있음: {len(only_in_airtable)}개)")

    if only_in_airtable:
        # 테스트/정상 분류
        test_records = record_classification.get('test', [])
        normal_records = record_classification.get('normal', [])

        if test_records:
            print(f"\n  테스트 레코드 추정: {len(test_records)}개")
            for code in test_records[:5]:
                member = airtable_members.get(code)
                if member:
                    fields = member['fields']
                    print(f"    {code}")
                    print(f"      - Name: {fields.get('Name', 'N/A')}")
                    print(f"      - Email: {fields.get('E-mail', 'N/A')}")
                    print(f"      - Sign-up Date: {fields.get('Sign-up Date', 'N/A')}")
                    print(f"      - Record ID: {member['id']}")
            if len(test_records) > 5:
                print(f"    ... 외 {len(test_records) - 5}개")

        if normal_records:
            print(f"\n  publ 삭제 회원 추정: {len(normal_records)}개")
            for code in normal_records[:5]:
                member = airtable_members.get(code)
                if member:
                    fields = member['fields']
                    print(f"    {code}")
                    print(f"      - Name: {fields.get('Name', 'N/A')}")
                    print(f"      - Email: {fields.get('E-mail', 'N/A')}")
                    print(f"      - Sign-up Date: {fields.get('Sign-up Date', 'N/A')}")
                    print(f"      - Record ID: {member['id']}")
            if len(normal_records) > 5:
                print(f"    ... 외 {len(normal_records) - 5}개")
    else:
        print("  - 없음 ✓")

    # CSV에만 있는 레코드 (동기화 누락)
    only_in_csv = discrepancies.get('only_in_csv', [])
    print(f"\n[동기화 누락 레코드] (CSV에만 있음: {len(only_in_csv)}개)")
    if only_in_csv:
        for code in only_in_csv[:5]:
            csv_data = csv_members.get(code, {})
            print(f"  {code}")
            print(f"    - Name: {csv_data.get('Name', 'N/A')}")
            print(f"    - Email: {csv_data.get('E-mail', 'N/A')}")
        if len(only_in_csv) > 5:
            print(f"  ... 외 {len(only_in_csv) - 5}개")
    else:
        print("  - 없음 ✓")

    # 권장 조치
    print("\n[권장 조치]")
    actions = []

    if duplicates:
        actions.append(f"• Airtable 중복 레코드 {len(duplicates)}건 정리 필요")

    if test_records:
        actions.append(f"• 테스트 레코드 {len(test_records)}건 삭제 권장")

    if normal_records:
        actions.append(f"• publ 삭제 회원 {len(normal_records)}건에 'Is Active' 필드 비활성화 권장")

    if only_in_csv:
        actions.append(f"• 동기화 누락 {len(only_in_csv)}건 재동기화 필요")

    if actions:
        for action in actions:
            print(f"  {action}")
    else:
        print("  - 조치 필요 없음 ✓")

    print("\n" + "=" * 60)


def run_analysis(csv_path: str | None = None) -> dict[str, Any]:
    """전체 분석 실행

    Args:
        csv_path: CSV 파일 경로 (None이면 최신 파일 자동 검색)

    Returns:
        분석 결과 딕셔너리
    """
    print("\n데이터 불일치 분석 시작...\n")

    # CSV 파일 찾기
    if csv_path is None:
        csv_path = find_latest_csv()
        if csv_path is None:
            print("ERROR: members CSV 파일을 찾을 수 없습니다.")
            return {'error': 'CSV file not found'}

    print(f"분석 CSV: {csv_path}")

    # API 연결
    print("Airtable 연결 중...")
    api = get_airtable_api()

    # 데이터 로드
    print("Airtable 데이터 로드 중...")
    airtable_members = load_airtable_members(api)
    print(f"  - Airtable: {len(airtable_members)}개")

    print("CSV 데이터 로드 중...")
    csv_members = load_csv_members(csv_path)
    print(f"  - CSV: {len(csv_members)}개")

    # 중복 검사
    print("중복 검사 중...")
    duplicates = find_airtable_duplicates(airtable_members)

    # 불일치 검사
    print("불일치 검사 중...")
    discrepancies = find_discrepancies(airtable_members, csv_members)

    # 테스트 레코드 분류
    only_in_airtable = discrepancies.get('only_in_airtable', [])
    record_classification = identify_test_records(only_in_airtable, airtable_members)

    # 리포트 출력
    print_analysis_report(
        airtable_members,
        csv_members,
        duplicates,
        discrepancies,
        record_classification,
        csv_path
    )

    return {
        'airtable_count': len(airtable_members),
        'csv_count': len(csv_members),
        'duplicates': duplicates,
        'discrepancies': discrepancies,
        'record_classification': record_classification,
        'csv_path': csv_path
    }


def main():
    """CLI 엔트리포인트"""
    parser = argparse.ArgumentParser(
        description='Airtable-publ 회원 데이터 불일치 분석'
    )
    parser.add_argument(
        '--csv',
        type=str,
        help='분석할 members CSV 파일 경로 (없으면 최신 파일 자동 검색)'
    )

    args = parser.parse_args()
    run_analysis(csv_path=args.csv)


if __name__ == '__main__':
    main()
