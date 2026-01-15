"""Airtable 마이그레이션 패키지

데이터 마이그레이션 스크립트를 제공합니다.
"""

from .migrate_to_member_programs import migrate_to_member_programs

__all__ = ['migrate_to_member_programs']
