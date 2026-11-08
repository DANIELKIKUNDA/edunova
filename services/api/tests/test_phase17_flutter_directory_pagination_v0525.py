"""Static integration contracts for the admin Flutter directory (not Flutter runtime tests)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_flutter_directory_queries_are_uri_encoded_and_server_paginated():
    api = (ROOT / 'apps/admin/lib/src/features/editorial/editorial_api.dart').read_text()
    assert "queryParameters:params" in api
    assert "params['search']=search.trim()" in api
    assert "params['state']=state" in api
    assert "'offset':'$offset'" in api


def test_flutter_directory_has_bounded_navigation_and_search():
    shell = (ROOT / 'apps/admin/lib/src/features/platform/platform_shell.dart').read_text()
    assert 'directoryPageSize=25' in shell
    assert 'directoryOffset+institutionDirectory!.length>=directoryTotal' in shell
    assert 'directoryOffset==0' in shell
    assert 'directorySearchController.text' in shell
    assert 'directoryBusy' in shell
    assert 'directoryRequestId' in shell
