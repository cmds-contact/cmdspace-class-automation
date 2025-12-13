"""Supabase 동기화 모듈"""

import csv
import glob
from supabase import create_client

from . import config


def get_supabase_client():
    """Supabase 클라이언트 생성"""
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


def read_csv_file(file_path):
    """CSV 파일 읽기 (UTF-8 BOM 인코딩)"""
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        return list(reader)


def find_csv_file(pattern):
    """패턴에 맞는 CSV 파일 찾기"""
    files = glob.glob(str(config.DOWNLOAD_DIR / pattern))
    if not files:
        raise FileNotFoundError(f"패턴에 맞는 파일 없음: {pattern}")
    # 가장 최근 파일 반환 (타임스탬프 기준 정렬)
    return sorted(files)[-1]


def get_existing_keys(supabase, table_name, key_column):
    """Supabase 테이블에서 기존 키 조회"""
    all_keys = set()
    page_size = 1000
    offset = 0

    while True:
        result = supabase.table(table_name).select('*').range(offset, offset + page_size - 1).execute()
        if not result.data:
            break
        for row in result.data:
            key_value = row.get(key_column)
            if key_value is not None:
                all_keys.add(key_value)
        if len(result.data) < page_size:
            break
        offset += page_size

    return all_keys


def sync_members(supabase):
    """회원 데이터 동기화 - 신규만 INSERT"""
    table_config = config.TABLES['members']
    file_path = find_csv_file(table_config['file_pattern'])

    print(f"\n{'='*50}")
    print(f"회원 동기화: {file_path.split('/')[-1]}")
    print(f"{'='*50}")

    # CSV 읽기
    csv_data = read_csv_file(file_path)
    print(f"CSV 레코드: {len(csv_data)}")

    # 기존 키 조회
    existing_keys = get_existing_keys(supabase, table_config['name'], table_config['unique_key'])
    print(f"기존 레코드: {len(existing_keys)}")

    # 새 레코드 필터링
    new_records = [row for row in csv_data if row[table_config['unique_key']] not in existing_keys]
    print(f"새 레코드: {len(new_records)}")

    # 삽입
    if new_records:
        for record in new_records:
            if 'Number' in record:
                del record['Number']

        inserted = 0
        for i in range(0, len(new_records), config.BATCH_SIZE):
            batch = new_records[i:i + config.BATCH_SIZE]
            result = supabase.table(table_config['name']).insert(batch).execute()
            inserted += len(result.data)

        print(f"삽입 완료: {inserted}개")
    else:
        print("새 레코드 없음")

    return len(new_records)


def sync_orders(supabase):
    """주문 데이터 동기화 - 신규만 INSERT"""
    table_config = config.TABLES['orders']
    file_path = find_csv_file(table_config['file_pattern'])

    print(f"\n{'='*50}")
    print(f"주문 동기화: {file_path.split('/')[-1]}")
    print(f"{'='*50}")

    # CSV 읽기
    csv_data = read_csv_file(file_path)
    print(f"CSV 레코드: {len(csv_data)}")

    # 기존 키 조회
    existing_keys = get_existing_keys(supabase, table_config['name'], table_config['unique_key'])
    print(f"기존 레코드: {len(existing_keys)}")

    # 새 레코드 필터링
    new_records = [row for row in csv_data if row[table_config['unique_key']] not in existing_keys]
    print(f"새 레코드: {len(new_records)}")

    # 삽입
    if new_records:
        for record in new_records:
            if 'Number' in record:
                del record['Number']

        inserted = 0
        for i in range(0, len(new_records), config.BATCH_SIZE):
            batch = new_records[i:i + config.BATCH_SIZE]
            result = supabase.table(table_config['name']).insert(batch).execute()
            inserted += len(result.data)

        print(f"삽입 완료: {inserted}개")
    else:
        print("새 레코드 없음")

    return len(new_records)


def sync_refunds(supabase):
    """환불 데이터 동기화 - 신규 INSERT + 상태 UPDATE"""
    table_config = config.TABLES['refunds']
    file_path = find_csv_file(table_config['file_pattern'])

    print(f"\n{'='*50}")
    print(f"환불 동기화: {file_path.split('/')[-1]}")
    print(f"{'='*50}")

    # CSV 읽기
    csv_data = read_csv_file(file_path)
    print(f"CSV 레코드: {len(csv_data)}")

    # 기존 데이터 전체 조회 (상태 비교용)
    existing_data = {}
    page_size = 1000
    offset = 0

    while True:
        result = supabase.table(table_config['name']).select('*').range(offset, offset + page_size - 1).execute()
        if not result.data:
            break
        for row in result.data:
            existing_data[row[table_config['unique_key']]] = row
        if len(result.data) < page_size:
            break
        offset += page_size

    print(f"기존 레코드: {len(existing_data)}")

    new_records = []
    update_records = []

    for row in csv_data:
        order_number = row[table_config['unique_key']]
        if order_number not in existing_data:
            new_records.append(row)
        else:
            # 상태 변경 확인
            existing_status = existing_data[order_number].get('Refund Status')
            new_status = row.get('Refund Status')
            if existing_status != new_status:
                update_records.append({
                    'order_number': order_number,
                    'new_status': new_status,
                    'old_status': existing_status
                })

    print(f"새 레코드: {len(new_records)}")
    print(f"상태 변경: {len(update_records)}")

    # 신규 삽입
    if new_records:
        for record in new_records:
            if 'Number' in record:
                del record['Number']

        inserted = 0
        for i in range(0, len(new_records), config.BATCH_SIZE):
            batch = new_records[i:i + config.BATCH_SIZE]
            result = supabase.table(table_config['name']).insert(batch).execute()
            inserted += len(result.data)

        print(f"삽입 완료: {inserted}개")

    # 상태 업데이트
    if update_records:
        updated = 0
        for update in update_records:
            result = supabase.table(table_config['name']).update({
                'Refund Status': update['new_status']
            }).eq(table_config['unique_key'], update['order_number']).execute()
            if result.data:
                updated += 1
                print(f"  업데이트: {update['order_number']}: {update['old_status']} -> {update['new_status']}")

        print(f"업데이트 완료: {updated}개")

    return len(new_records), len(update_records)


def sync_all():
    """전체 데이터 동기화"""
    print("\n" + "=" * 60)
    print("SUPABASE 동기화 시작")
    print("=" * 60)

    supabase = get_supabase_client()
    results = {}

    for data_type in config.PROCESSING_ORDER:
        try:
            if data_type == 'members':
                results['members'] = {'new': sync_members(supabase)}
            elif data_type == 'orders':
                results['orders'] = {'new': sync_orders(supabase)}
            elif data_type == 'refunds':
                new_count, update_count = sync_refunds(supabase)
                results['refunds'] = {'new': new_count, 'updated': update_count}
        except Exception as e:
            print(f"\n오류 ({data_type}): {e}")
            results[data_type] = {'error': str(e)}

    return results


if __name__ == '__main__':
    sync_all()
