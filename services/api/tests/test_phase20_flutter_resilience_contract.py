from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_download_resume_validates_server_range_before_appending():
    source = _source("apps/mobile/lib/src/features/delivery/application/download_resource.dart")
    assert "download_content_range_mismatch" in source
    assert "Headers.contentRangeHeader" in source
    assert "start==offset" in source
    assert "length==total" in source


def test_transient_network_failure_does_not_consume_persistent_retry_budget_twice():
    source = _source("apps/mobile/lib/src/features/delivery/application/download_resource.dart")
    queue = _source("apps/mobile/lib/src/features/delivery/application/delivery_repository.dart")
    assert "incrementRetry:!transient" in source
    assert "e.message=='network_unavailable'" in queue
    assert "attempts:q.attempts" in queue


def test_download_integrity_remains_mandatory_before_finalize():
    source = _source("apps/mobile/lib/src/features/delivery/application/download_resource.dart")
    checksum = source.index("download_checksum_mismatch")
    finalize = source.index("store.finalize")
    ready = source.index("local.markReady")
    assert checksum < finalize < ready
