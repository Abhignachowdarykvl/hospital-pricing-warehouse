from unittest.mock import MagicMock

from src.ingest import s3_upload


def test_s3_key_layout():
    assert s3_upload.s3_key("inpatient", "2026-09-24", "page_0000.json") == (
        "raw/inpatient/2026-09-24/page_0000.json"
    )


def test_upload_run_uploads_every_json(tmp_path, monkeypatch):
    run_dir = tmp_path / "2026-09-24"
    run_dir.mkdir()
    (run_dir / "page_0000.json").write_text("[]")
    (run_dir / "_manifest.json").write_text("{}")
    monkeypatch.setattr(s3_upload.settings, "s3_bucket", "test-bucket")

    client = MagicMock()
    n = s3_upload.upload_run("inpatient", run_dir, client=client)

    assert n == 2
    assert client.upload_file.call_count == 2
