"""Airtable 동기화 모듈

CSV 데이터를 Airtable로 직접 동기화.
- Members/Orders/Refunds 테이블 지원
- Linked Record 자동 연결
"""

import csv
import glob
from typing import Any

from pyairtable import Api, Table

from . import config
from .utils import (
    parse_price, safe_get, batch_iterator, to_iso_datetime
)


# Airtable 배치 크기 (API 제한)
AIRTABLE_BATCH_SIZE = 10


def get_airtable_api() -> Api:
    """Airtable API 클라이언트 생성"""
    return Api(config.AIRTABLE_API_KEY)


def get_table(api: Api, table_name: str) -> Table:
    """Airtable 테이블 객체 가져오기"""
    return api.table(config.AIRTABLE_BASE_ID, table_name)


def read_csv_file(file_path: str) -> list[dict[str, Any]]:
    """CSV 파일 읽기 (UTF-8 BOM 인코딩)

    Args:
        file_path: CSV 파일 경로

    Returns:
        레코드 딕셔너리 리스트
    """
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        return list(reader)


def find_csv_file(pattern: str) -> str:
    """패턴에 맞는 CSV 파일 찾기

    Args:
        pattern: glob 패턴

    Returns:
        가장 최근 파일 경로

    Raises:
        FileNotFoundError: 패턴에 맞는 파일이 없을 때
    """
    files = glob.glob(str(config.DOWNLOAD_DIR / pattern))
    if not files:
        raise FileNotFoundError(f"패턴에 맞는 파일 없음: {pattern}")
    return sorted(files)[-1]


def get_existing_records(table: Table, key_field: str) -> dict[str, str]:
    """Airtable 테이블에서 기존 레코드 조회

    Args:
        table: Airtable 테이블 객체
        key_field: 고유 키 필드명

    Returns:
        key_value -> record_id 매핑 딕셔너리
    """
    return {
        record['fields'].get(key_field): record['id']
        for record in table.all()
        if record['fields'].get(key_field)
    }


def get_existing_orders(table: Table) -> dict[str, str]:
    """Airtable에서 기존 주문 레코드 조회

    Args:
        table: Airtable 테이블 객체

    Returns:
        order_number -> record_id 매핑 딕셔너리
    """
    return {
        record['fields'].get('Order Number'): record['id']
        for record in table.all()
        if record['fields'].get('Order Number')
    }


def get_existing_member_products(table: Table) -> dict[str, str]:
    """Airtable에서 기존 MemberProducts 레코드 조회

    Args:
        table: Airtable 테이블 객체

    Returns:
        MemberProducts Code -> record_id 매핑 딕셔너리
    """
    return {
        record['fields'].get('MemberProducts Code'): record['id']
        for record in table.all()
        if record['fields'].get('MemberProducts Code')
    }


def get_pending_refunds(table: Table) -> dict[str, dict[str, Any]]:
    """Airtable에서 미결정 상태 환불 레코드 조회

    Refunded, Rejected가 아닌 환불만 조회 (상태 변경 추적용)

    Args:
        table: Airtable 테이블 객체

    Returns:
        order_number -> {id, status} 매핑 딕셔너리
    """
    final_statuses = {'Refunded', 'Rejected'}
    result = {}
    for record in table.all():
        order_number = record['fields'].get('Order Number')
        status = record['fields'].get('Refund Status')
        if order_number and status not in final_statuses:
            result[order_number] = {
                'id': record['id'],
                'status': status
            }
    return result


def sync_members_to_airtable(api: Api) -> int:
    """회원 데이터를 CSV에서 읽어 Airtable로 동기화

    Args:
        api: Airtable API 클라이언트

    Returns:
        삽입된 레코드 수
    """
    table_config = config.TABLES['members']
    file_path = find_csv_file(table_config['file_pattern'])
    table = get_table(api, config.AIRTABLE_TABLES['members'])

    print(f"\n{'='*50}")
    print(f"Airtable 회원 동기화: {file_path.split('/')[-1]}")
    print(f"{'='*50}")

    csv_data = read_csv_file(file_path)
    print(f"CSV 레코드: {len(csv_data)}")

    existing = get_existing_records(table, 'Member Code')
    print(f"Airtable 기존 레코드: {len(existing)}")

    new_records = []
    for row in csv_data:
        member_code = row.get('Member Code')
        if not member_code or member_code in existing:
            continue

        # Birth year 처리
        birth_year = row.get('Birth year')
        birth_year_str = str(birth_year) if birth_year else ''

        # Sign-up Date를 ISO dateTime으로 변환
        signup_date_str = safe_get(row, 'Sign-up Date')
        signup_datetime = to_iso_datetime(signup_date_str)

        record_fields = {
            'Member Code': member_code,
            'Username': safe_get(row, 'Username'),
            'E-mail': safe_get(row, 'E-mail'),
            'Country': safe_get(row, 'Country'),
            'Name': safe_get(row, 'Name'),
            'Gender': safe_get(row, 'Gender'),
            'Birth year': birth_year_str,
            'Personal email address': safe_get(row, 'Personal email address'),
            'Mobile number': safe_get(row, 'Mobile number'),
            'Sign-up Date': signup_date_str,  # 원본 텍스트
        }

        # Sign-up Date (ISO) - dateTime 형식
        if signup_datetime:
            record_fields['Sign-up Date (ISO)'] = signup_datetime

        new_records.append(record_fields)

    print(f"새 레코드: {len(new_records)}")

    if not new_records:
        return 0

    inserted = 0
    for batch in batch_iterator(new_records, AIRTABLE_BATCH_SIZE):
        table.batch_create(batch)
        inserted += len(batch)

    print(f"삽입 완료: {inserted}개")
    return inserted


def sync_orders_to_airtable(api: Api) -> int:
    """주문 데이터를 CSV에서 읽어 Airtable로 동기화 (Member Linked Record 포함)

    Args:
        api: Airtable API 클라이언트

    Returns:
        삽입된 레코드 수
    """
    table_config = config.TABLES['orders']
    file_path = find_csv_file(table_config['file_pattern'])
    orders_table = get_table(api, config.AIRTABLE_TABLES['orders'])
    members_table = get_table(api, config.AIRTABLE_TABLES['members'])

    print(f"\n{'='*50}")
    print(f"Airtable 주문 동기화: {file_path.split('/')[-1]}")
    print(f"{'='*50}")

    csv_data = read_csv_file(file_path)
    print(f"CSV 레코드: {len(csv_data)}")

    existing_orders = get_existing_orders(orders_table)
    existing_members = get_existing_records(members_table, 'Member Code')

    print(f"Airtable 기존 주문: {len(existing_orders)}")

    new_records: list[dict[str, Any]] = []

    for row in csv_data:
        order_number = row.get('Order Number')
        if not order_number:
            continue

        # 이미 존재하는 주문은 건너뛰기 (신규만 추가)
        if order_number in existing_orders:
            continue

        member_code = safe_get(row, 'Member Code')
        member_id = existing_members.get(member_code)

        # Date and Time of Payment를 ISO dateTime으로 변환
        payment_date_str = safe_get(row, 'Date and Time of Payment')
        payment_datetime = to_iso_datetime(payment_date_str)

        record_fields = {
            'Order Number': order_number,
            'Product name': safe_get(row, 'Product name'),
            'Type': safe_get(row, 'Type'),
            'Price': parse_price(row.get('Price')),
            'Name': safe_get(row, 'Name'),
            'E-mail': safe_get(row, 'E-mail'),
            'Member Code': member_code,
            'Payment Type': safe_get(row, 'Payment Type'),
            'Payment Method': safe_get(row, 'Payment Method'),
            'Date and Time of Payment': payment_date_str,  # 원본 텍스트
        }

        # Date and Time of Payment (ISO) - dateTime 형식
        if payment_datetime:
            record_fields['Date and Time of Payment (ISO)'] = payment_datetime

        # Member Linked Record 추가
        if member_id:
            record_fields['Member'] = [member_id]

        new_records.append(record_fields)

    print(f"새 레코드: {len(new_records)}")

    inserted = 0
    if new_records:
        for batch in batch_iterator(new_records, AIRTABLE_BATCH_SIZE):
            orders_table.batch_create(batch)
            inserted += len(batch)
        print(f"삽입 완료: {inserted}개")

    return inserted


def sync_refunds_to_airtable(api: Api) -> tuple[int, int]:
    """환불 데이터를 CSV에서 읽어 Airtable로 동기화

    - 신규 환불 추가 (Orders Linked Record 포함)
    - 미결정 상태 환불의 상태 변경 추적 및 업데이트

    Args:
        api: Airtable API 클라이언트

    Returns:
        (삽입된 수, 업데이트된 수) 튜플
    """
    table_config = config.TABLES['refunds']
    file_path = find_csv_file(table_config['file_pattern'])
    refunds_table = get_table(api, config.AIRTABLE_TABLES['refunds'])
    orders_table = get_table(api, config.AIRTABLE_TABLES['orders'])

    print(f"\n{'='*50}")
    print(f"Airtable 환불 동기화: {file_path.split('/')[-1]}")
    print(f"{'='*50}")

    csv_data = read_csv_file(file_path)
    print(f"CSV 레코드: {len(csv_data)}")

    # 기존 환불 조회
    existing_refunds = get_existing_records(refunds_table, 'Order Number')
    existing_orders = get_existing_orders(orders_table)

    # 미결정 상태 환불만 조회 (상태 변경 추적용)
    pending_refunds = get_pending_refunds(refunds_table)

    print(f"Airtable 기존 환불: {len(existing_refunds)}")
    print(f"미결정 상태 환불: {len(pending_refunds)}")

    # CSV를 Order Number로 인덱싱 (빠른 조회용)
    csv_by_order = {row.get('Order Number'): row for row in csv_data if row.get('Order Number')}

    new_records: list[dict[str, Any]] = []
    refunds_to_update: list[dict[str, Any]] = []

    # 1. 신규 환불 추가
    for row in csv_data:
        order_number = row.get('Order Number')
        if not order_number or order_number in existing_refunds:
            continue

        order_id = existing_orders.get(order_number)

        # Refund Request Date를 ISO dateTime으로 변환
        refund_date_str = safe_get(row, 'Refund Request Date')
        refund_datetime = to_iso_datetime(refund_date_str)

        record_fields = {
            'Order Number': order_number,
            'Refund Status': safe_get(row, 'Refund Status'),
            'Refund Request Price': parse_price(row.get('Refund Request Price')),
            'Username': safe_get(row, 'Username'),
            'Member Code': safe_get(row, 'Member Code'),
            'Refund Request Date': refund_date_str,  # 원본 텍스트
        }

        # Refund Request Date (ISO) - dateTime 형식
        if refund_datetime:
            record_fields['Refund Request Date (ISO)'] = refund_datetime

        # Orders Linked Record 추가
        if order_id:
            record_fields['Orders'] = [order_id]

        new_records.append(record_fields)

    # 2. 미결정 상태 환불의 상태 변경 확인
    for order_number, pending_data in pending_refunds.items():
        csv_row = csv_by_order.get(order_number)
        if not csv_row:
            continue

        csv_status = csv_row.get('Refund Status')
        airtable_status = pending_data['status']

        # 상태가 변경되었으면 업데이트 대상에 추가
        if csv_status and csv_status != airtable_status:
            refunds_to_update.append({
                'id': pending_data['id'],
                'fields': {'Refund Status': csv_status}
            })

    print(f"새 환불 레코드: {len(new_records)}")
    print(f"상태 업데이트 대상: {len(refunds_to_update)}")

    # 환불 레코드 삽입
    inserted = 0
    failed_records: list[dict[str, Any]] = []

    if new_records:
        for batch in batch_iterator(new_records, AIRTABLE_BATCH_SIZE):
            try:
                refunds_table.batch_create(batch)
                inserted += len(batch)
            except Exception as e:
                error_msg = str(e)
                # Single Select 옵션 누락 에러 처리
                if 'INVALID_MULTIPLE_CHOICE_OPTIONS' in error_msg:
                    print(f"\n⚠️  Airtable 'Refund Status' 필드에 새 옵션 추가 필요!")
                    # 실패한 레코드들의 상태값 수집
                    statuses = set(r.get('Refund Status', '') for r in batch)
                    print(f"   누락된 옵션: {statuses}")
                    print("   해결 방법: Airtable에서 Refunds 테이블의 'Refund Status' 필드에")
                    print(f"   '{', '.join(statuses)}' 옵션을 수동으로 추가하세요.")
                    failed_records.extend(batch)
                else:
                    raise

        if inserted > 0:
            print(f"환불 삽입 완료: {inserted}개")
        if failed_records:
            print(f"환불 삽입 실패: {len(failed_records)}개 (상태 옵션 누락)")

    # 환불 상태 업데이트
    updated = 0
    if refunds_to_update:
        for batch in batch_iterator(refunds_to_update, AIRTABLE_BATCH_SIZE):
            try:
                refunds_table.batch_update(batch)
                updated += len(batch)
            except Exception as e:
                error_msg = str(e)
                if 'INVALID_MULTIPLE_CHOICE_OPTIONS' in error_msg:
                    print(f"⚠️  환불 상태 업데이트 실패: 상태 옵션 누락")
                else:
                    raise
        if updated > 0:
            print(f"환불 상태 업데이트 완료: {updated}개")

    return inserted, updated


def ensure_tables_exist(api: Api) -> dict[str, bool]:
    """Products와 MemberProducts 테이블이 존재하는지 확인하고 없으면 생성

    pyairtable 3.x의 Base.schema() API를 사용하여 테이블 생성

    Args:
        api: Airtable API 클라이언트

    Returns:
        테이블별 생성 여부 딕셔너리
    """
    print(f"\n{'='*50}")
    print("테이블 존재 확인")
    print(f"{'='*50}")

    results = {'products': False, 'member_products': False}

    # 기존 테이블 목록 조회
    try:
        base = api.base(config.AIRTABLE_BASE_ID)
        schema = base.schema()
        existing_tables = {table.name for table in schema.tables}
        print(f"기존 테이블: {', '.join(existing_tables)}")
    except Exception as e:
        print(f"스키마 조회 실패: {e}")
        return results

    # Products 테이블 확인/생성
    products_name = config.AIRTABLE_TABLES['products']
    if products_name not in existing_tables:
        print(f"\n{products_name} 테이블 생성 중...")
        try:
            base.create_table(
                products_name,
                fields=[
                    {"name": "Product Code", "type": "singleLineText"},
                    {"name": "Display Name", "type": "singleLineText"},
                    {"name": "Is Subscription", "type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},
                    {"name": "Subscription Days", "type": "number", "options": {"precision": 0}},
                ]
            )
            results['products'] = True
            print(f"{products_name} 테이블 생성 완료")
        except Exception as e:
            print(f"{products_name} 테이블 생성 실패: {e}")
    else:
        print(f"{products_name} 테이블 이미 존재")

    # MemberProducts 테이블 확인/생성
    member_products_name = config.AIRTABLE_TABLES['member_products']
    if member_products_name not in existing_tables:
        print(f"\n{member_products_name} 테이블 생성 중...")

        # Members와 Products 테이블 ID 조회
        members_table_id = None
        products_table_id = None

        # 다시 스키마 조회 (Products가 방금 생성됐을 수 있음)
        schema = base.schema()
        for table in schema.tables:
            if table.name == config.AIRTABLE_TABLES['members']:
                members_table_id = table.id
            elif table.name == products_name:
                products_table_id = table.id

        # Primary field는 반드시 text 타입이어야 함
        fields = [
            {"name": "MemberProducts Code", "type": "singleLineText"},  # Primary field (MemberCode_ProductCode)
            {"name": "Subscription Status", "type": "singleSelect", "options": {
                "choices": [
                    {"name": "Active", "color": "greenBright"},
                    {"name": "Expired", "color": "redBright"},
                    {"name": "N/A", "color": "grayBright"}
                ]
            }},
            {"name": "Last Payment Date", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
            {"name": "Expiry Date", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
            {"name": "Welcome Sent", "type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},
        ]

        # Linked Record 필드 추가 (Primary field 이후에)
        if members_table_id:
            fields.insert(1, {
                "name": "Member",
                "type": "multipleRecordLinks",
                "options": {"linkedTableId": members_table_id}
            })

        if products_table_id:
            fields.insert(2 if members_table_id else 1, {
                "name": "Product",
                "type": "multipleRecordLinks",
                "options": {"linkedTableId": products_table_id}
            })

        try:
            base.create_table(
                member_products_name,
                fields=fields
            )
            results['member_products'] = True
            print(f"{member_products_name} 테이블 생성 완료")
        except Exception as e:
            print(f"{member_products_name} 테이블 생성 실패: {e}")
    else:
        print(f"{member_products_name} 테이블 이미 존재")

    return results


def sync_products_to_airtable(api: Api) -> int:
    """Orders 데이터에서 상품 정보를 추출하여 Products 테이블에 동기화

    Args:
        api: Airtable API 클라이언트

    Returns:
        삽입된 레코드 수
    """
    table_config = config.TABLES['orders']
    file_path = find_csv_file(table_config['file_pattern'])
    products_table = get_table(api, config.AIRTABLE_TABLES['products'])

    print(f"\n{'='*50}")
    print(f"Airtable 상품 동기화")
    print(f"{'='*50}")

    csv_data = read_csv_file(file_path)

    # 상품별 Payment Type 수집 (구독 여부 판단용)
    product_payment_types: dict[str, set[str]] = {}
    for row in csv_data:
        product_name = row.get('Product name', '').strip()
        payment_type = row.get('Payment Type', '').strip()
        if product_name:
            if product_name not in product_payment_types:
                product_payment_types[product_name] = set()
            if payment_type:
                product_payment_types[product_name].add(payment_type)

    print(f"CSV에서 발견된 상품: {len(product_payment_types)}종")

    # 기존 상품 조회
    existing_products = get_existing_records(products_table, 'Product Code')
    print(f"Airtable 기존 상품: {len(existing_products)}")

    # 신규 상품만 추가
    new_records = []
    for product_name, payment_types in product_payment_types.items():
        if product_name in existing_products:
            continue

        # Payment Type이 "Regular Payment"를 포함하면 구독 상품
        is_subscription = 'Regular Payment' in payment_types

        record_fields = {
            'Product Code': product_name,
            'Display Name': '',  # 수동 입력용
            'Is Subscription': is_subscription,
            # Subscription Days는 수동 입력
        }
        new_records.append(record_fields)

    print(f"새 상품: {len(new_records)}")

    if not new_records:
        return 0

    inserted = 0
    for batch in batch_iterator(new_records, AIRTABLE_BATCH_SIZE):
        products_table.batch_create(batch)
        inserted += len(batch)

    print(f"상품 삽입 완료: {inserted}개")
    return inserted


def sync_member_products_to_airtable(api: Api) -> dict[str, int]:
    """회원별 상품 조합을 MemberProducts 테이블에 동기화 (신규만)

    구독 상태 및 만료일은 Airtable Formula가 처리.
    이 함수는 신규 MemberProducts 레코드 생성만 담당.

    Args:
        api: Airtable API 클라이언트

    Returns:
        {'new': int} 딕셔너리
    """
    print(f"\n{'='*50}")
    print(f"Airtable 회원별 상품 동기화 (신규만)")
    print(f"{'='*50}")

    # 테이블 객체
    orders_table = get_table(api, config.AIRTABLE_TABLES['orders'])
    members_table = get_table(api, config.AIRTABLE_TABLES['members'])
    products_table = get_table(api, config.AIRTABLE_TABLES['products'])
    member_products_table = get_table(api, config.AIRTABLE_TABLES['member_products'])

    # 기존 데이터 조회
    print("데이터 조회 중...")

    # Members: Member Code -> record_id
    existing_members = get_existing_records(members_table, 'Member Code')

    # Products: Product Code -> record_id
    products_data: dict[str, str] = {}
    for record in products_table.all():
        product_code = record['fields'].get('Product Code')
        if product_code:
            products_data[product_code] = record['id']

    # MemberProducts: MemberProducts Code -> record_id
    existing_member_products = get_existing_member_products(member_products_table)

    print(f"  Members: {len(existing_members)}개")
    print(f"  Products: {len(products_data)}개")
    print(f"  MemberProducts 기존: {len(existing_member_products)}개")

    # Orders에서 (Member Code, Product name) 조합 수집
    print("Orders 집계 중...")
    member_product_combos: set[tuple[str, str]] = set()

    for record in orders_table.all():
        member_code = record['fields'].get('Member Code')
        product_name = record['fields'].get('Product name')
        if member_code and product_name:
            member_product_combos.add((member_code, product_name))

    print(f"  회원+상품 조합: {len(member_product_combos)}개")

    # 신규 레코드 생성
    new_records = []
    for member_code, product_name in member_product_combos:
        member_products_code = f"{member_code}_{product_name}"

        # 이미 존재하면 건너뛰기
        if member_products_code in existing_member_products:
            continue

        member_id = existing_members.get(member_code)
        product_id = products_data.get(product_name)

        if not member_id or not product_id:
            continue

        record_fields = {
            'MemberProducts Code': member_products_code,
            'Member': [member_id],
            'Product': [product_id],
            'Welcome Sent': False,
        }
        new_records.append(record_fields)

    print(f"새 레코드: {len(new_records)}")

    # 레코드 삽입
    inserted = 0
    if new_records:
        for batch in batch_iterator(new_records, AIRTABLE_BATCH_SIZE):
            member_products_table.batch_create(batch)
            inserted += len(batch)
        print(f"삽입 완료: {inserted}개")

    return {'new': inserted}


def update_orders_member_products_link(api: Api) -> int:
    """Orders 테이블의 MemberProducts Linked Record 업데이트

    MemberProducts 동기화 후 호출하여 Orders에 Linked Record 연결.
    이미 연결된 Orders는 건너뜀.

    Args:
        api: Airtable API 클라이언트

    Returns:
        업데이트된 레코드 수
    """
    print(f"\n{'='*50}")
    print(f"Orders → MemberProducts 연결 업데이트")
    print(f"{'='*50}")

    orders_table = get_table(api, config.AIRTABLE_TABLES['orders'])
    member_products_table = get_table(api, config.AIRTABLE_TABLES['member_products'])

    # MemberProducts: MemberProducts Code -> record_id
    existing_member_products = get_existing_member_products(member_products_table)
    print(f"MemberProducts: {len(existing_member_products)}개")

    # Orders 순회하여 연결되지 않은 레코드 찾기
    records_to_update = []
    orders_all = orders_table.all()
    print(f"Orders 전체: {len(orders_all)}개")

    for record in orders_all:
        # 이미 MemberProducts가 연결되어 있으면 건너뛰기
        if record['fields'].get('MemberProducts'):
            continue

        member_code = record['fields'].get('Member Code')
        product_name = record['fields'].get('Product name')

        if not member_code or not product_name:
            continue

        member_products_code = f"{member_code}_{product_name}"
        member_products_id = existing_member_products.get(member_products_code)

        if member_products_id:
            records_to_update.append({
                'id': record['id'],
                'fields': {'MemberProducts': [member_products_id]}
            })

    print(f"연결 대상: {len(records_to_update)}개")

    # 배치 업데이트
    updated = 0
    if records_to_update:
        for batch in batch_iterator(records_to_update, AIRTABLE_BATCH_SIZE):
            orders_table.batch_update(batch)
            updated += len(batch)
        print(f"연결 완료: {updated}개")

    return updated


def sync_all_to_airtable() -> dict[str, dict[str, Any]]:
    """CSV 데이터를 Airtable로 전체 동기화

    동기화 순서:
    1. Members - 회원 데이터
    2. Orders - 주문 데이터 (신규 추가, Member 연결)
    3. Products - 상품 마스터 (Orders에서 추출)
    4. MemberProducts - 회원별 상품 (신규만)
    5. Orders - MemberProducts 연결 업데이트
    6. Refunds - 환불 데이터

    Returns:
        각 테이블별 동기화 결과 딕셔너리
    """
    print("\n" + "=" * 60)
    print("AIRTABLE 동기화 시작")
    print("=" * 60)

    api = get_airtable_api()
    results: dict[str, dict[str, Any]] = {}

    try:
        # 테이블 존재 확인 및 생성
        ensure_tables_exist(api)

        # Members 동기화
        results['members'] = {'new': sync_members_to_airtable(api)}

        # Orders 동기화 (신규 추가, Member 연결)
        results['orders'] = {'new': sync_orders_to_airtable(api)}

        # Products 동기화 (Orders CSV에서 상품 추출)
        try:
            results['products'] = {'new': sync_products_to_airtable(api)}
        except Exception as e:
            print(f"Products 동기화 건너뜀: {e}")
            results['products'] = {'new': 0, 'error': str(e)}

        # MemberProducts 동기화 (신규만)
        try:
            member_products_result = sync_member_products_to_airtable(api)
            results['member_products'] = member_products_result
        except Exception as e:
            print(f"MemberProducts 동기화 건너뜀: {e}")
            results['member_products'] = {'new': 0, 'error': str(e)}

        # Orders → MemberProducts 연결 업데이트
        try:
            orders_linked = update_orders_member_products_link(api)
            results['orders']['member_products_linked'] = orders_linked
        except Exception as e:
            print(f"Orders-MemberProducts 연결 건너뜀: {e}")
            results['orders']['member_products_linked'] = 0

        # Refunds 동기화 (상태 변경 업데이트 포함)
        try:
            new_count, update_count = sync_refunds_to_airtable(api)
            results['refunds'] = {'new': new_count, 'updated': update_count}
        except Exception as e:
            print(f"Refunds 동기화 오류: {e}")
            results['refunds'] = {'new': 0, 'updated': 0, 'error': str(e)}

    except Exception as e:
        print(f"\n오류 (Airtable 동기화): {e}")
        results['error'] = str(e)

    return results


def backfill_iso_dates(api: Api = None) -> dict[str, int]:
    """기존 레코드의 (ISO) 날짜 필드를 채우는 백필 함수

    각 테이블에서 원본 날짜 필드는 있지만 (ISO) 필드가 비어있는 레코드를 찾아
    ISO 8601 형식으로 변환하여 업데이트

    Args:
        api: Airtable API 클라이언트 (없으면 새로 생성)

    Returns:
        테이블별 업데이트된 레코드 수
    """
    if api is None:
        api = get_airtable_api()

    print(f"\n{'='*60}")
    print("ISO 날짜 필드 백필 시작")
    print("=" * 60)

    results = {}

    # 테이블별 필드 매핑: (테이블명, 원본필드, ISO필드)
    table_fields = [
        ('Members', 'Sign-up Date', 'Sign-up Date (ISO)'),
        ('Orders', 'Date and Time of Payment', 'Date and Time of Payment (ISO)'),
        ('Refunds', 'Refund Request Date', 'Refund Request Date (ISO)'),
    ]

    for table_name, original_field, iso_field in table_fields:
        print(f"\n{'='*50}")
        print(f"{table_name} 테이블 백필")
        print(f"{'='*50}")

        table = get_table(api, table_name)
        all_records = table.all()
        print(f"전체 레코드: {len(all_records)}")

        records_to_update = []

        for record in all_records:
            fields = record['fields']
            original_value = fields.get(original_field)
            iso_value = fields.get(iso_field)

            # 원본은 있는데 ISO가 없는 경우만 처리
            if original_value and not iso_value:
                # 먼저 표준 변환 시도 (YYYY-MM-DD HH:MM:SS 형식)
                iso_converted = to_iso_datetime(original_value)

                # 변환 실패 시, 이미 ISO 형식인지 확인 (T와 +/- 포함)
                if not iso_converted and 'T' in original_value:
                    # 이미 ISO 형식이면 그대로 사용
                    iso_converted = original_value

                if iso_converted:
                    records_to_update.append({
                        'id': record['id'],
                        'fields': {iso_field: iso_converted}
                    })

        print(f"업데이트 대상: {len(records_to_update)}")

        if records_to_update:
            updated = 0
            for batch in batch_iterator(records_to_update, AIRTABLE_BATCH_SIZE):
                table.batch_update(batch)
                updated += len(batch)
            print(f"업데이트 완료: {updated}개")
            results[table_name] = updated
        else:
            results[table_name] = 0

    print(f"\n{'='*60}")
    print("백필 완료")
    print("=" * 60)

    return results


def record_sync_history(
    sync_date: str,
    duration: float,
    status: str,
    members_new: int = 0,
    orders_new: int = 0,
    refunds_new: int = 0,
    refunds_updated: int = 0,
    downloaded_files: str = ''
) -> bool:
    """동기화 히스토리를 Airtable에 기록

    Args:
        sync_date: 동기화 실행 시간 (YYYY-MM-DD HH:MM:SS 형식)
        duration: 소요 시간 (초)
        status: 상태 (Success/Failed)
        members_new: 신규 회원 수
        orders_new: 신규 주문 수
        refunds_new: 신규 환불 수
        refunds_updated: 업데이트된 환불 수
        downloaded_files: 다운로드된 파일명 목록

    Returns:
        True면 기록 성공
    """
    from datetime import datetime

    print(f"\n{'='*50}")
    print("동기화 히스토리 기록")
    print(f"{'='*50}")

    try:
        api = get_airtable_api()
        table = get_table(api, config.AIRTABLE_TABLES['sync_history'])

        # sync_date를 ISO 8601 형식으로 변환 (Airtable dateTime 필드용)
        # 입력: "2024-12-27 15:30:45" (KST) -> 출력: "2024-12-27T15:30:45+09:00"
        dt = datetime.strptime(sync_date, '%Y-%m-%d %H:%M:%S')
        iso_datetime = dt.strftime('%Y-%m-%dT%H:%M:%S') + '+09:00'

        record = {
            'Sync DateTime': iso_datetime,
            'Duration (sec)': round(duration, 1),
            'Status': status,
            'Members New': members_new,
            'Orders New': orders_new,
            'Refunds New': refunds_new,
            'Refunds Updated': refunds_updated,
            'Downloaded Files': downloaded_files,
        }

        table.create(record)
        print(f"히스토리 기록 완료: {status}")
        return True

    except Exception as e:
        print(f"히스토리 기록 실패: {e}")
        return False


def fix_member_products_codes(api: Api = None) -> int:
    """MemberProducts 테이블의 잘못된 MemberProducts Code 필드를 수정

    MemberProducts Code 형식: MemberCode_ProductCode
    예: SUBIJIML5JEDXC7HCAK-JKWV2_KM-CMDS-OBM-ME-1

    Args:
        api: Airtable API 클라이언트 (없으면 새로 생성)

    Returns:
        수정된 레코드 수
    """
    if api is None:
        api = get_airtable_api()

    print(f"\n{'='*60}")
    print("MemberProducts Code 필드 수정")
    print("=" * 60)

    member_products_table = get_table(api, config.AIRTABLE_TABLES['member_products'])
    members_table = get_table(api, config.AIRTABLE_TABLES['members'])
    products_table = get_table(api, config.AIRTABLE_TABLES['products'])

    # Members: record_id -> Member Code
    members_by_id: dict[str, str] = {}
    for record in members_table.all():
        member_code = record['fields'].get('Member Code')
        if member_code:
            members_by_id[record['id']] = member_code

    # Products: record_id -> Product Code
    products_by_id: dict[str, str] = {}
    for record in products_table.all():
        product_code = record['fields'].get('Product Code')
        if product_code:
            products_by_id[record['id']] = product_code

    print(f"Members: {len(members_by_id)}개")
    print(f"Products: {len(products_by_id)}개")

    # MemberProducts에서 잘못된 코드 찾기
    all_records = member_products_table.all()
    records_to_update = []

    for record in all_records:
        code = record['fields'].get('MemberProducts Code', '')

        # 코드에 '_'가 없으면 잘못된 형식
        if '_' not in code:
            member_links = record['fields'].get('Member', [])
            product_links = record['fields'].get('Product', [])

            if member_links and product_links:
                member_id = member_links[0]
                product_id = product_links[0]

                member_code = members_by_id.get(member_id)
                product_code = products_by_id.get(product_id)

                if member_code and product_code:
                    new_code = f"{member_code}_{product_code}"
                    records_to_update.append({
                        'id': record['id'],
                        'fields': {'MemberProducts Code': new_code}
                    })

    print(f"수정 대상: {len(records_to_update)}개")

    if not records_to_update:
        print("수정할 레코드가 없습니다.")
        return 0

    # 배치 업데이트
    updated = 0
    for batch in batch_iterator(records_to_update, AIRTABLE_BATCH_SIZE):
        member_products_table.batch_update(batch)
        updated += len(batch)

    print(f"수정 완료: {updated}개")
    return updated


if __name__ == '__main__':
    sync_all_to_airtable()
