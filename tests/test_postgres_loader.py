"""Tests for the pages -> DataFrame step. No database needed."""

import json

from src.load.postgres_loader import pages_to_frame


def test_pages_to_frame_combines_pages_and_adds_lineage(tmp_path):
    run_dir = tmp_path / "2026-01-01"
    run_dir.mkdir()
    (run_dir / "page_0000.json").write_text(json.dumps([{"DRG_Cd": "003", "Tot_Dschrgs": "11"}]))
    (run_dir / "page_0001.json").write_text(json.dumps([{"DRG_Cd": "004", "Tot_Dschrgs": "5"}]))

    df = pages_to_frame(run_dir)

    assert len(df) == 2
    assert list(df["drg_cd"]) == ["003", "004"]
    assert set(df["_source_file"]) == {"page_0000.json", "page_0001.json"}
    assert (df["_run_date"] == "2026-01-01").all()
    assert "_loaded_at" in df.columns


def test_pages_to_frame_keeps_values_as_strings(tmp_path):
    run_dir = tmp_path / "2026-01-01"
    run_dir.mkdir()
    (run_dir / "page_0000.json").write_text(json.dumps([{"Avg_Submtd_Cvrd_Chrg": "738478.63636"}]))

    df = pages_to_frame(run_dir)

    assert df["avg_submtd_cvrd_chrg"].iloc[0] == "738478.63636"
