"""csv_reader 모듈 테스트"""

import pytest
from pathlib import Path

from src.airtable.csv_reader import read_csv, find_csv


class TestReadCsv:
    """read_csv 함수 테스트"""

    def test_parses_utf8_bom_file(self, tmp_path):
        """UTF-8 BOM 인코딩 파일 파싱"""
        # UTF-8 BOM으로 CSV 파일 생성
        csv_content = "Member Code,Name\nM001,Test1\nM002,Test2"
        csv_file = tmp_path / "test.csv"
        csv_file.write_bytes(b'\xef\xbb\xbf' + csv_content.encode('utf-8'))

        result = read_csv(str(csv_file))

        assert len(result) == 2
        assert result[0]['Member Code'] == 'M001'
        assert result[0]['Name'] == 'Test1'
        assert result[1]['Member Code'] == 'M002'

    def test_parses_regular_utf8_file(self, tmp_path):
        """일반 UTF-8 파일 파싱"""
        csv_content = "Member Code,Name\nM001,Test1"
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content, encoding='utf-8')

        result = read_csv(str(csv_file))

        assert len(result) == 1
        assert result[0]['Member Code'] == 'M001'

    def test_empty_file(self, tmp_path):
        """빈 파일 (헤더만)"""
        csv_content = "Member Code,Name"
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content, encoding='utf-8')

        result = read_csv(str(csv_file))

        assert result == []

    def test_handles_korean_content(self, tmp_path):
        """한글 내용 처리"""
        csv_content = "Member Code,Name\nM001,홍길동\nM002,김철수"
        csv_file = tmp_path / "test.csv"
        csv_file.write_bytes(b'\xef\xbb\xbf' + csv_content.encode('utf-8'))

        result = read_csv(str(csv_file))

        assert result[0]['Name'] == '홍길동'
        assert result[1]['Name'] == '김철수'


class TestFindCsv:
    """find_csv 함수 테스트"""

    def test_returns_latest_file(self, tmp_path, mocker):
        """가장 최근 파일 반환"""
        # 여러 파일 생성
        (tmp_path / "20240101_members.csv").touch()
        (tmp_path / "20240115_members.csv").touch()
        (tmp_path / "20240110_members.csv").touch()

        # config.DOWNLOAD_DIR를 tmp_path로 mock
        mocker.patch('src.airtable.csv_reader.config.DOWNLOAD_DIR', tmp_path)

        result = find_csv("*_members.csv")

        # 정렬 후 마지막 파일 (20240115)
        assert "20240115_members.csv" in result

    def test_raises_when_no_files(self, tmp_path, mocker):
        """파일 없을 때 FileNotFoundError"""
        mocker.patch('src.airtable.csv_reader.config.DOWNLOAD_DIR', tmp_path)

        with pytest.raises(FileNotFoundError) as exc_info:
            find_csv("*_members.csv")

        assert "패턴에 맞는 파일 없음" in str(exc_info.value)

    def test_matches_pattern(self, tmp_path, mocker):
        """패턴 매칭"""
        (tmp_path / "members.csv").touch()
        (tmp_path / "orders.csv").touch()

        mocker.patch('src.airtable.csv_reader.config.DOWNLOAD_DIR', tmp_path)

        result = find_csv("orders.csv")

        assert "orders.csv" in result
        assert "members.csv" not in result
