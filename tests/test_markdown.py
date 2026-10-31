"""Markdown parser tests using original, repository-owned fixtures."""
from src.parsers.markdown_parser import MarkdownParser
from src.parsers.chunker import ChunkStrategy, TextChunker


def test_parse_file(fixture_dir):
    path = fixture_dir / "sample.md"
    result = MarkdownParser().parse(str(path))
    assert result.filename == path.name
    assert result.raw_text == path.read_text(encoding="utf-8")
    assert result.total_pages == 1
    assert result.total_chunks == len(result.chunks) > 0
    assert result.metadata["parser"] == "markdown"


def test_parse_from_bytes_preserves_structure(fixture_dir):
    result = MarkdownParser().parse_from_bytes((fixture_dir / "sample.md").read_bytes(), "sample.md")
    assert result.filename == "sample.md"
    assert "# RAG sample notes" in result.raw_text
    assert "- Read the document" in result.raw_text
    assert "```python" in result.raw_text
    assert result.chunks


def test_supported_extensions():
    assert {".md", ".markdown"} <= set(MarkdownParser().supported_extensions())


def test_custom_chunker(fixture_dir):
    chunker = TextChunker(strategy=ChunkStrategy.CHARACTER, max_chunk_size=150,
                          min_chunk_size=20, chunk_overlap=20)
    result = MarkdownParser(chunker=chunker).parse(str(fixture_dir / "sample.md"))
    assert len(result.chunks) > 1
    assert all(0 < chunk["length"] <= 150 for chunk in result.chunks)


def test_empty_markdown():
    result = MarkdownParser().parse_from_bytes(b"", "empty.md")
    assert result.raw_text == ""
    assert result.chunks == []
    assert result.total_chunks == 0


def test_frontmatter_is_preserved():
    content = "---\ntitle: Sample notes\n---\n\n# Notes\n\nOriginal test content."
    result = MarkdownParser().parse_from_bytes(content.encode(), "frontmatter.md")
    assert result.raw_text == content
