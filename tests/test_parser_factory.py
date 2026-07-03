"""Factory behavior without initializing PDF or embedding models."""
import pytest

from src.parsers import ParserFactory, parse_file
from src.parsers.base import BaseParser


def test_supported_extensions():
    assert {".pdf", ".docx", ".md", ".html"} <= set(ParserFactory.supported_extensions())


@pytest.mark.parametrize("filename, expected", [
    ("sample.docx", "WordParser"), ("sample.DOCX", "WordParser"),
    ("sample.md", "MarkdownParser"), ("sample.Md", "MarkdownParser"),
    ("sample.html", "HTMLParser"),
])
def test_get_parser(filename, expected):
    assert type(ParserFactory.get_parser(filename)).__name__ == expected


def test_unsupported_file():
    with pytest.raises(ValueError, match="不支持的文件类型"):
        ParserFactory.get_parser("sample.xyz")


def test_register_parser(monkeypatch):
    class CustomParser(BaseParser):
        def supported_extensions(self):
            return [".custom"]

        def parse(self, file_path):
            raise NotImplementedError

        def parse_from_bytes(self, file_bytes, filename):
            raise NotImplementedError

    monkeypatch.setattr(ParserFactory, "_parsers", ParserFactory._parsers.copy())
    ParserFactory.register_parser(".CUSTOM", CustomParser)
    assert isinstance(ParserFactory.get_parser("sample.custom"), CustomParser)


@pytest.mark.parametrize("name", ["sample.md", "sample.html"])
def test_parse_text_fixture(fixture_dir, name):
    result = parse_file(str(fixture_dir / name))
    assert result.filename == name
    assert "RAG sample notes" in result.raw_text
    assert result.chunks


def test_parse_word(sample_docx):
    result = parse_file(str(sample_docx))
    assert result.filename == sample_docx.name
    assert result.table_count == 1
