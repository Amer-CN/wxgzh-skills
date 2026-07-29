"""hotfix4: canonical structured claim numbers pass schema and chart parsing."""
from media_enrichment.chart_generator import extract_numbers_from_claim


def test_structured_number_object_is_preserved_and_parsed():
    claim = {"numbers": [{"value": 6, "unit": "GB"}]}
    assert extract_numbers_from_claim(claim) == [("6GB", 6.0, "GB")]


def test_mixed_string_and_structured_numbers_are_supported():
    claim = {"numbers": ["76.2%", {"value": 5, "unit": "min"}]}
    assert extract_numbers_from_claim(claim) == [
        ("76.2%", 76.2, "%"),
        ("5min", 5.0, "min"),
    ]
