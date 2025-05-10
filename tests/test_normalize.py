import pytest
from service.app.normalize import (
    parse_price,
    parse_floor,
    parse_living_space,
    map_category,
    clean_text,
)


@pytest.mark.parametrize("raw,expected", [
    ("CHF 1.200.000,00", 1200000),
    (250000, 250000),
    ("€3,500.50", 3500),
    ("invalid", 0),
])
def test_parse_price(raw, expected):
    assert parse_price(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    (None, 0),
    ("ground floor", 0),
    ("G", 0),
    ("5", 5),
    ("level 3", 3),
    (2, 2),
])
def test_parse_floor(raw, expected):
    assert parse_floor(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    (None, 0.0),
    (50, 50.0),
    ("100.5", 100.5),
    ("75 m²", 75.0),
    ("invalid", 0.0),
])
def test_parse_living_space(raw, expected):
    assert parse_living_space(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("Apartment", "apartment"),
    ("Single-family house", "house"),
    ("Commercial unit", "commercial"),
    ("Ground level", "ground"),
    ("Something else", "other"),
    (None, "other"),
])
def test_map_category(raw, expected):
    assert map_category(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("Hello, World!", "hello world"),
    ("Éléphant Café", "elephant cafe"),
    ("   Multiple   spaces\t\n", "multiple spaces"),
    (None, ""),
    ("", ""),
])
def test_clean_text(raw, expected):
    assert clean_text(raw) == expected
