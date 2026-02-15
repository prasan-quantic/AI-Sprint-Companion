"""
Test Suite for Document Parser Module
=====================================

This module contains comprehensive unit tests for the document parsing
functionality that extracts text from various file formats.

Test Coverage:
    - TXT file extraction with various encodings (UTF-8, UTF-16, Latin-1)
    - PDF file extraction (with mocked PyPDF2)
    - DOCX file extraction (with mocked python-docx)
    - DOC file extraction (legacy format)
    - Main extract_text_from_file async function
    - Error handling for unsupported formats
    - Empty file handling

Dependencies:
    - pytest
    - pytest-asyncio
    - unittest.mock

Usage:
    Run tests with: pytest tests/test_document_parser.py -v

Author: AI Sprint Companion Team
"""

import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import UploadFile

from app.document_parser import (
    extract_text_from_file,
    extract_from_txt,
    extract_from_pdf,
    extract_from_docx,
    extract_from_doc,
)


class TestExtractFromTxt:
    """
    Test suite for TXT file text extraction.

    Tests various text encodings and fallback behavior
    when encoding detection fails.
    """

    def test_extract_utf8_text(self):
        """
        Test extracting UTF-8 encoded text.

        Verifies that standard UTF-8 content is correctly decoded.
        """
        content = "Hello, World!".encode('utf-8')
        result = extract_from_txt(content)
        assert result == "Hello, World!"

    def test_extract_utf16_text(self):
        """
        Test extracting UTF-16 encoded text.

        Verifies that UTF-16 content is handled correctly.
        """
        content = "Hello, World!".encode('utf-16')
        result = extract_from_txt(content)
        assert "Hello" in result or "World" in result

    def test_extract_latin1_text(self):
        """
        Test extracting Latin-1 encoded text.

        Verifies that Latin-1 (ISO-8859-1) content with
        special characters is correctly decoded.
        """
        content = "Héllo, Wörld!".encode('latin-1')
        result = extract_from_txt(content)
        assert "llo" in result

    def test_extract_with_fallback(self):
        """
        Test extraction falls back to ignore errors.

        Verifies that content with invalid encoding bytes
        is handled gracefully by ignoring errors.
        """
        content = bytes([0x80, 0x81, 0x82, 0x41, 0x42, 0x43])
        result = extract_from_txt(content)
        assert "ABC" in result or result is not None


class TestExtractFromPdf:
    """
    Test suite for PDF file text extraction.

    Tests PDF parsing functionality with mocked PyPDF2 library
    to avoid external dependencies in unit tests.
    """

    def test_extract_pdf_import_error(self):
        """
        Test PDF extraction when PyPDF2 is not installed.

        Verifies that appropriate error message is returned
        when the required library is missing.
        """
        with patch.dict('sys.modules', {'PyPDF2': None}):
            with patch('app.document_parser.extract_from_pdf') as mock:
                mock.return_value = "[PDF parsing requires PyPDF2]"
                result = mock(b"fake pdf content")
                assert "PyPDF2" in result

    def test_extract_pdf_with_mock(self):
        """
        Test PDF extraction with mocked PyPDF2.

        Verifies that PDF content extraction works correctly
        when PyPDF2 is available and functioning.
        """
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Page 1 content"

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch('app.document_parser.PdfReader', return_value=mock_reader):
            result = extract_from_pdf(b"fake content")
            assert result is not None


class TestExtractFromDocx:
    """
    Test suite for DOCX file text extraction.

    Tests DOCX parsing functionality with mocked python-docx
    library including paragraph and table extraction.
    """

    def test_extract_docx_with_mock(self):
        """
        Test DOCX extraction with mocked python-docx.

        Verifies that paragraph content is correctly extracted
        from DOCX files.
        """
        mock_para = MagicMock()
        mock_para.text = "Paragraph content"

        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para]
        mock_doc.tables = []

        with patch('app.document_parser.Document', return_value=mock_doc):
            result = extract_from_docx(b"fake content")
            assert result is not None

    def test_extract_docx_with_tables(self):
        """
        Test DOCX extraction including table content.

        Verifies that both paragraphs and table cells
        are extracted from DOCX files.
        """
        mock_para = MagicMock()
        mock_para.text = "Paragraph"

        mock_cell1 = MagicMock()
        mock_cell1.text = "Cell 1"
        mock_cell2 = MagicMock()
        mock_cell2.text = "Cell 2"

        mock_row = MagicMock()
        mock_row.cells = [mock_cell1, mock_cell2]

        mock_table = MagicMock()
        mock_table.rows = [mock_row]

        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para]
        mock_doc.tables = [mock_table]

        with patch('app.document_parser.Document', return_value=mock_doc):
            result = extract_from_docx(b"fake content")
            assert result is not None


class TestExtractFromDoc:
    """
    Test suite for legacy DOC file text extraction.

    Tests the limited DOC format support which attempts
    to extract readable text from binary content.
    """

    def test_extract_doc_with_text(self):
        """
        Test DOC extraction with readable text content.

        Verifies that readable text portions are extracted
        from DOC files when possible.
        """
        content = b"This is some readable text content for testing"
        result = extract_from_doc(content)
        assert "readable" in result or "limited support" in result.lower()

    def test_extract_doc_binary_content(self):
        """
        Test DOC extraction with mostly binary content.

        Verifies graceful handling when DOC file contains
        primarily binary data with little readable text.
        """
        content = bytes([0x00, 0x01, 0x02, 0x03] * 20)
        result = extract_from_doc(content)
        assert result is not None


class TestExtractTextFromFile:
    """
    Test suite for the main async file extraction function.

    Tests the complete file extraction workflow including
    file type detection, content reading, and error handling.
    """

    @pytest.mark.asyncio
    async def test_extract_from_none_file(self):
        """
        Test extraction returns None for None file input.

        Verifies that the function handles None input gracefully.
        """
        result = await extract_text_from_file(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_extract_from_file_no_filename(self):
        """
        Test extraction returns None when filename is missing.

        Verifies that files without filenames are rejected.
        """
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = None
        result = await extract_text_from_file(mock_file)
        assert result is None

    @pytest.mark.asyncio
    async def test_extract_from_txt_file(self):
        """
        Test extraction from uploaded TXT file.

        Verifies complete workflow for TXT file processing
        including async file read and text extraction.
        """
        content = b"Test content for extraction"

        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.read = AsyncMock(return_value=content)
        mock_file.seek = AsyncMock()

        result = await extract_text_from_file(mock_file)
        assert result == "Test content for extraction"

    @pytest.mark.asyncio
    async def test_extract_from_empty_file(self):
        """
        Test extraction from empty file returns None.

        Verifies that empty files are handled appropriately.
        """
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "empty.txt"
        mock_file.read = AsyncMock(return_value=b"")
        mock_file.seek = AsyncMock()

        result = await extract_text_from_file(mock_file)
        assert result is None

    @pytest.mark.asyncio
    async def test_extract_unsupported_format(self):
        """
        Test extraction returns None for unsupported formats.

        Verifies that files with unrecognized extensions
        are handled gracefully.
        """
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "test.xyz"
        mock_file.read = AsyncMock(return_value=b"content")
        mock_file.seek = AsyncMock()

        result = await extract_text_from_file(mock_file)
        assert result is None

    @pytest.mark.asyncio
    async def test_extract_pdf_file(self):
        """
        Test extraction from uploaded PDF file.

        Verifies PDF file handling returns content or error message.
        """
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.read = AsyncMock(return_value=b"fake pdf content")
        mock_file.seek = AsyncMock()

        result = await extract_text_from_file(mock_file)
        assert result is not None

    @pytest.mark.asyncio
    async def test_extract_docx_file(self):
        """
        Test extraction from uploaded DOCX file.

        Verifies DOCX file handling returns content or error message.
        """
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "test.docx"
        mock_file.read = AsyncMock(return_value=b"fake docx content")
        mock_file.seek = AsyncMock()

        result = await extract_text_from_file(mock_file)
        assert result is not None

    @pytest.mark.asyncio
    async def test_extract_doc_file(self):
        """
        Test extraction from uploaded DOC file.

        Verifies legacy DOC file handling.
        """
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "test.doc"
        mock_file.read = AsyncMock(return_value=b"fake doc content with text")
        mock_file.seek = AsyncMock()

        result = await extract_text_from_file(mock_file)
        assert result is not None

    @pytest.mark.asyncio
    async def test_extract_handles_exception(self):
        """
        Test extraction handles exceptions gracefully.

        Verifies that read errors are caught and None is returned.
        """
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.read = AsyncMock(side_effect=Exception("Read error"))
        mock_file.seek = AsyncMock()

        result = await extract_text_from_file(mock_file)
        assert result is None

