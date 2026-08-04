"""Document parsers for extracting tax data from various sources."""

import csv
import io
import json
from abc import ABC, abstractmethod
from typing import Any, ClassVar, cast

import pdfplumber
from bs4 import BeautifulSoup
import openpyxl
from lxml import etree


class AbstractParser(ABC):
    """Base interface for all document parsers."""

    @abstractmethod
    def parse(self, content: bytes) -> Any:
        """Parse raw byte content into a structured format."""


class JSONParser(AbstractParser):
    """Parses JSON responses."""

    def parse(self, content: bytes) -> dict[str, Any] | list[Any]:
        return cast("dict[str, Any] | list[Any]", json.loads(content.decode("utf-8")))


class CSVParser(AbstractParser):
    """Parses CSV content into a list of dictionaries."""

    def parse(self, content: bytes) -> list[dict[str, str]]:
        text_content = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text_content))
        return list(reader)


class HTMLParser(AbstractParser):
    """Parses HTML content using BeautifulSoup."""

    def parse(self, content: bytes) -> BeautifulSoup:
        return BeautifulSoup(content, "lxml")


class PDFParser(AbstractParser):
    """Parses PDF text content using pdfplumber."""

    def parse(self, content: bytes) -> str:
        text_blocks = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_blocks.append(text)
        return "\n".join(text_blocks)


class ExcelParser(AbstractParser):
    """Parses Excel content into list of lists."""

    def parse(self, content: bytes) -> list[list[Any]]:
        wb = openpyxl.load_workbook(filename=io.BytesIO(content), data_only=True)
        ws = wb.active
        if not ws:
            return []
        
        data = []
        for row in ws.iter_rows(values_only=True):
            data.append(list(row))
        return data


class XMLParser(AbstractParser):
    """Parses XML and RSS feeds."""

    def parse(self, content: bytes) -> etree._Element:
        return etree.fromstring(content)


class ParserFactory:
    """Factory to get the right parser based on content format."""

    _parsers: ClassVar[dict[str, AbstractParser]] = {
        "json": JSONParser(),
        "csv": CSVParser(),
        "html": HTMLParser(),
        "pdf": PDFParser(),
        "excel": ExcelParser(),
        "xlsx": ExcelParser(),
        "xml": XMLParser(),
        "rss": XMLParser(),
    }

    @classmethod
    def get_parser(cls, format_type: str) -> AbstractParser:
        parser = cls._parsers.get(format_type.lower())
        if not parser:
            raise ValueError(f"No parser found for format: {format_type}")
        return parser
