"""Airtable 동기화 모듈

CSV 데이터를 Airtable로 직접 동기화.
- Members/Orders/Refunds 테이블 지원
- Linked Record 자동 연결
"""

from typing import Any

from .logger import logger

# airtable 패키지에서 공통 기능 import
from .airtable import (
    get_api as get_airtable_api,
    # Sync functions
    sync_members as sync_members_to_airtable,
    sync_orders as sync_orders_to_airtable,
    sync_refunds as sync_refunds_to_airtable,
    sync_products as sync_products_to_airtable,
    sync_member_programs as sync_member_programs_to_airtable,
    update_orders_member_programs_link,
    # Schema, History, Maintenance
    ensure_tables_exist,
    record_sync_history,
    backfill_iso_dates,
    fix_member_programs_codes,
    validate_required_fields,
    backfill_refunds_orders_link,
    # Member management
    count_active_members,
    count_csv_members,
    deactivate_withdrawn_members,
)


def sync_all_to_airtable() -> dict[str, dict[str, Any]]:
    """CSV 데이터를 Airtable로 전체 동기화

    동기화 순서:
    1. Members - 회원 데이터
    2. Orders - 주문 데이터 (신규 추가, Member 연결)
    3. Products - 상품 마스터 (Orders에서 추출)
    4. MemberPrograms - 회원별 프로그램 (신규만)
    5. Orders - MemberPrograms 연결 업데이트
    6. Refunds - 환불 데이터

    Returns:
        각 테이블별 동기화 결과 딕셔너리
    """
    logger.info("\n" + "=" * 60)
    logger.info("AIRTABLE 동기화 시작")
    logger.info("=" * 60)

    api = get_airtable_api()
    results: dict[str, dict[str, Any]] = {}

    try:
        # 테이블 존재 확인 및 생성
        ensure_tables_exist(api)

        # Members 동기화
        results['members'] = {'new': sync_members_to_airtable(api)}

        # 회원 수 비교 (효율적 탈퇴 회원 관리)
        try:
            airtable_active_count = count_active_members(api)
            csv_member_count = count_csv_members()

            if airtable_active_count != csv_member_count:
                logger.info(f"회원 수 불일치 감지: Airtable 활성 {airtable_active_count}명 ≠ CSV {csv_member_count}명")
                withdrawn_result = deactivate_withdrawn_members(api)
                results['members']['withdrawn'] = withdrawn_result
            else:
                logger.info(f"회원 수 일치: {airtable_active_count}명 (탈퇴 회원 체크 생략)")
                results['members']['withdrawn'] = {'skipped': True, 'reason': 'count_match'}
        except Exception as e:
            logger.warning(f"탈퇴 회원 처리 건너뜀: {e}")
            results['members']['withdrawn'] = {'error': str(e)}

        # Orders 동기화 (신규 추가, Member 연결)
        results['orders'] = {'new': sync_orders_to_airtable(api)}

        # Products 동기화 (Orders CSV에서 상품 추출)
        try:
            results['products'] = {'new': sync_products_to_airtable(api)}
        except Exception as e:
            logger.warning(f"Products 동기화 건너뜀: {e}")
            results['products'] = {'new': 0, 'error': str(e)}

        # MemberPrograms 동기화 (신규만)
        try:
            member_programs_result = sync_member_programs_to_airtable(api)
            results['member_programs'] = member_programs_result
        except Exception as e:
            logger.warning(f"MemberPrograms 동기화 건너뜀: {e}")
            results['member_programs'] = {'new': 0, 'error': str(e)}

        # Orders → MemberPrograms 연결 업데이트
        try:
            orders_linked = update_orders_member_programs_link(api)
            results['orders']['member_programs_linked'] = orders_linked
        except Exception as e:
            logger.warning(f"Orders-MemberPrograms 연결 건너뜀: {e}")
            results['orders']['member_programs_linked'] = 0

        # Refunds 동기화 (상태 변경 업데이트 포함)
        try:
            new_count, update_count = sync_refunds_to_airtable(api)
            results['refunds'] = {'new': new_count, 'updated': update_count}
        except Exception as e:
            logger.error(f"Refunds 동기화 오류: {e}")
            results['refunds'] = {'new': 0, 'updated': 0, 'error': str(e)}

        # Refunds → Orders Linked Record 복구 (빈 연결 자동 채우기)
        try:
            refunds_linked = backfill_refunds_orders_link(api)
            results['refunds']['orders_linked'] = refunds_linked
        except Exception as e:
            logger.warning(f"Refunds-Orders 연결 복구 건너뜀: {e}")
            results['refunds']['orders_linked'] = 0

        # 필수 필드 검증 및 자동 복구
        try:
            validation_results = validate_required_fields(api, auto_fix=True)
            results['validation'] = validation_results
        except Exception as e:
            logger.warning(f"필수 필드 검증 건너뜀: {e}")
            results['validation'] = {'error': str(e)}

    except Exception as e:
        logger.error(f"오류 (Airtable 동기화): {e}")
        results['error'] = str(e)

    return results


if __name__ == '__main__':
    sync_all_to_airtable()
