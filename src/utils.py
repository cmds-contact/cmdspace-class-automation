"""공통 유틸리티 모듈

Airtable 동기화에서 공통으로 사용하는 함수들을 모아둔 모듈.
"""

import re
from datetime import datetime, timedelta
from typing import Any, Callable, Iterator


def extract_program_code(product_code: str) -> str:
    """Product Code에서 Program Code 추출

    Product Code의 처음 3개 세그먼트를 Program Code로 사용합니다.
    뒷부분은 구매 옵션(할인, 정가 등)을 나타냅니다.

    Args:
        product_code: 전체 Product Code (예: KM-CMDS-OBM-ME-1)

    Returns:
        Program Code (처음 3개 세그먼트) 또는 원본 (패턴 불일치 시)

    Examples:
        >>> extract_program_code('KM-CMDS-OBM-ME-1')
        'KM-CMDS-OBM'
        >>> extract_program_code('KM-CMDS-OBM-YE-2')
        'KM-CMDS-OBM'
        >>> extract_program_code('KM-CMDS-OBM')
        'KM-CMDS-OBM'
        >>> extract_program_code('SIMPLE')
        'SIMPLE'
    """
    # 처음 3개 세그먼트 추출: XX-YY-ZZ 형식
    match = re.match(r'^([^-]+(?:-[^-]+){2})', product_code)
    return match.group(1) if match else product_code


def batch_process(
    items: list[Any],
    processor: Callable[[list[Any]], int],
    batch_size: int = 100
) -> int:
    """리스트를 배치로 나누어 처리

    Args:
        items: 처리할 아이템 리스트
        processor: 배치를 받아 처리하고 처리된 수를 반환하는 함수
        batch_size: 배치 크기 (기본값: 100)

    Returns:
        총 처리된 아이템 수
    """
    total_processed = 0

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        processed = processor(batch)
        total_processed += processed

    return total_processed


def batch_iterator(items: list[Any], batch_size: int = 100) -> Iterator[list[Any]]:
    """리스트를 배치로 나누어 반환하는 제너레이터

    Args:
        items: 분할할 아이템 리스트
        batch_size: 배치 크기 (기본값: 100)

    Yields:
        배치 크기만큼의 아이템 리스트
    """
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def parse_price(price_value: str | int | float | None) -> int:
    """가격 문자열을 정수로 변환

    Args:
        price_value: 가격 값 (문자열, 정수, 또는 None)

    Returns:
        정수로 변환된 가격 (변환 실패시 0)

    Examples:
        >>> parse_price("1,000원")
        1000
        >>> parse_price("500")
        500
        >>> parse_price(None)
        0
    """
    if price_value is None:
        return 0

    if isinstance(price_value, (int, float)):
        return int(price_value)

    if isinstance(price_value, str):
        # 쉼표, '원', 공백 제거
        cleaned = price_value.replace(',', '').replace('원', '').strip()
        return int(cleaned) if cleaned else 0

    return 0


def safe_get(data: dict[str, Any], key: str, default: Any = '') -> Any:
    """딕셔너리에서 안전하게 값 조회

    Args:
        data: 조회할 딕셔너리
        key: 키
        default: 기본값 (기본: 빈 문자열)

    Returns:
        값 또는 기본값
    """
    value = data.get(key)
    return value if value is not None else default


def to_iso_datetime(date_str: str | None) -> str | None:
    """날짜 문자열을 ISO 8601 형식으로 변환 (KST 타임존)

    Args:
        date_str: 날짜 문자열 (YYYY-MM-DD HH:MM:SS 또는 YYYY-MM-DD HH:MM 형식)

    Returns:
        ISO 8601 형식 문자열 (예: 2024-12-27T15:30:45+09:00) 또는 None

    Examples:
        >>> to_iso_datetime("2024-12-27 15:30:45")
        '2024-12-27T15:30:45+09:00'
        >>> to_iso_datetime("2024-12-27 15:30")
        '2024-12-27T15:30:00+09:00'
        >>> to_iso_datetime(None)
        None
    """
    if not date_str or not date_str.strip():
        return None

    from datetime import datetime

    date_str = date_str.strip()

    # 여러 형식 시도
    formats = [
        '%Y-%m-%d %H:%M:%S',  # 초 포함
        '%Y-%m-%d %H:%M',     # 초 없음
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%dT%H:%M:%S') + '+09:00'
        except ValueError:
            continue

    return None


def parse_iso_datetime(iso_str: str | None) -> datetime | None:
    """ISO 8601 형식 문자열을 datetime 객체로 변환

    Args:
        iso_str: ISO 8601 형식 문자열 (예: 2024-12-27T15:30:45+09:00)

    Returns:
        datetime 객체 또는 None
    """
    if not iso_str:
        return None

    try:
        # +09:00 형식의 타임존 제거하고 파싱
        if '+' in iso_str:
            iso_str = iso_str.split('+')[0]
        elif iso_str.endswith('Z'):
            iso_str = iso_str[:-1]

        return datetime.fromisoformat(iso_str)
    except ValueError:
        return None


def calculate_subscription_status(
    last_payment_date: datetime | str | None,
    subscription_days: int | None,
    is_subscription: bool = True
) -> tuple[datetime | None, str]:
    """[DEPRECATED] 구독 만료일과 상태 계산

    NOTE: 이 함수는 더 이상 사용되지 않습니다.
    구독 상태 및 만료일은 Airtable Formula로 처리됩니다.
    향후 버전에서 제거될 예정입니다.

    Args:
        last_payment_date: 마지막 결제일 (datetime 또는 ISO 문자열)
        subscription_days: 구독 기간 (일수)
        is_subscription: 구독 상품 여부

    Returns:
        (만료일, 상태) 튜플
        상태: "Active" | "Expired" | "N/A"
    """
    import warnings
    warnings.warn(
        "calculate_subscription_status is deprecated. "
        "Use Airtable Formula instead.",
        DeprecationWarning,
        stacklevel=2
    )
    # 구독 상품이 아니면 N/A
    if not is_subscription:
        return None, "N/A"

    # 결제일 없으면 N/A
    if not last_payment_date:
        return None, "N/A"

    # 구독 기간 없으면 N/A
    if not subscription_days or subscription_days <= 0:
        return None, "N/A"

    # 문자열이면 datetime으로 변환
    if isinstance(last_payment_date, str):
        last_payment_date = parse_iso_datetime(last_payment_date)
        if not last_payment_date:
            return None, "N/A"

    # 만료일 계산
    expiry_date = last_payment_date + timedelta(days=subscription_days)
    today = datetime.now()

    # 상태 결정
    status = "Active" if expiry_date > today else "Expired"

    return expiry_date, status
