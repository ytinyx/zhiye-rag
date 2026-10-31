"""Optional Docling smoke test; never writes extracted documents into the repo."""
import os
from pathlib import Path

import pytest


@pytest.mark.pdf_model
def test_pdf_parse():
    configured_path = os.getenv("TEST_PDF_PATH")
    if not configured_path:
        pytest.skip("Set TEST_PDF_PATH to a PDF you are allowed to use")
    path = Path(configured_path)
    if not path.is_file():
        pytest.fail("TEST_PDF_PATH does not point to a file")
    from src.parsers.pdf_parse import PDFParser

    result = PDFParser().parse(str(path))
    assert result.filename == path.name
    assert result.total_pages > 0
    assert result.raw_text.strip()
    assert result.total_chunks == len(result.chunks) > 0
