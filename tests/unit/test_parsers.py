import pytest
from bs4 import BeautifulSoup
import json
import csv
import io

from taxos.infrastructure.scrapers.parsers import ParserFactory, JSONParser, CSVParser, HTMLParser, PDFParser


def test_parser_factory():
    assert isinstance(ParserFactory.get_parser("json"), JSONParser)
    assert isinstance(ParserFactory.get_parser("csv"), CSVParser)
    assert isinstance(ParserFactory.get_parser("html"), HTMLParser)
    assert isinstance(ParserFactory.get_parser("pdf"), PDFParser)
    
    with pytest.raises(ValueError):
        ParserFactory.get_parser("unknown")


def test_json_parser():
    parser = ParserFactory.get_parser("json")
    data = {"key": "value"}
    result = parser.parse(json.dumps(data).encode("utf-8"))
    assert result == data


def test_csv_parser():
    parser = ParserFactory.get_parser("csv")
    csv_data = "col1,col2\nval1,val2\nval3,val4"
    result = parser.parse(csv_data.encode("utf-8"))
    assert len(result) == 2
    assert result[0]["col1"] == "val1"
    assert result[1]["col2"] == "val4"


def test_html_parser():
    parser = ParserFactory.get_parser("html")
    html_data = "<html><body><h1>Test</h1></body></html>"
    result = parser.parse(html_data.encode("utf-8"))
    assert isinstance(result, BeautifulSoup)
    assert result.find("h1").text == "Test"


# PDF testing requires a mock PDF file byte stream, skipping full test for brevity
# but verifying the factory returns the correct type.
