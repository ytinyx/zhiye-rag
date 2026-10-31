"""HTML parser tests with a small, original fixture."""
from src.parsers.html_parser import HTMLParser
from src.parsers.chunker import ChunkStrategy, TextChunker


def test_parse_file(fixture_dir):
    result = HTMLParser().parse(str(fixture_dir / "sample.html"))
    assert result.filename == "sample.html"
    assert result.total_pages == 1
    assert result.total_chunks == len(result.chunks) > 0
    assert "RAG sample notes" in result.raw_text
    assert "<h1>" not in result.raw_text


def test_parse_from_bytes_matches_file(fixture_dir):
    path = fixture_dir / "sample.html"
    parser = HTMLParser()
    result = parser.parse_from_bytes(path.read_bytes(), path.name)
    assert result.raw_text == parser.parse(str(path)).raw_text
    assert "* Read the document" in result.raw_text or "- Read the document" in result.raw_text
    assert result.chunks


def test_supported_extensions():
    assert {".html", ".htm"} <= set(HTMLParser().supported_extensions())


def test_custom_chunker(fixture_dir):
    chunker = TextChunker(strategy=ChunkStrategy.CHARACTER, max_chunk_size=150,
                          min_chunk_size=20, chunk_overlap=20)
    result = HTMLParser(chunker=chunker).parse(str(fixture_dir / "sample.html"))
    assert len(result.chunks) > 1
    assert all(0 < chunk["length"] <= 150 for chunk in result.chunks)


def test_empty_html():
    result = HTMLParser().parse_from_bytes(b"<html><body></body></html>", "empty.html")
    assert result.raw_text.strip() == ""
    assert result.chunks == []
