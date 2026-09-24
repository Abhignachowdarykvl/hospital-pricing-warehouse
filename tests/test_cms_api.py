"""Unit tests for the ingestion module. No network calls: we mock the HTTP layer."""

from unittest.mock import MagicMock

from src.ingest import cms_api


def test_fetch_page_handles_list_payload():
    session = MagicMock()
    session.get.return_value.json.return_value = [{"a": 1}, {"a": 2}]
    rows = cms_api.fetch_page(session, "https://example.com", offset=0, size=2)
    assert rows == [{"a": 1}, {"a": 2}]


def test_fetch_page_handles_results_wrapper():
    session = MagicMock()
    session.get.return_value.json.return_value = {"results": [{"a": 1}]}
    rows = cms_api.fetch_page(session, "https://example.com", offset=0, size=2)
    assert rows == [{"a": 1}]


def test_build_session_sets_user_agent():
    session = cms_api.build_session()
    assert "hospital-pricing-warehouse" in session.headers["User-Agent"]
