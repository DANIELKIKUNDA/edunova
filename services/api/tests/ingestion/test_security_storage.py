from __future__ import annotations

import pytest

from app.modules.ingestion.infrastructure.storage import LocalStagingStorage
from app.modules.ingestion.infrastructure.security import ClamAvTcpScanner


def test_local_staging_blocks_path_traversal(tmp_path):
    s=LocalStagingStorage(str(tmp_path))
    with pytest.raises(ValueError,match='invalid_storage_key'): s.put('../escape.bin',b'x',content_type='application/octet-stream')
    s.put('safe/a.bin',b'ok',content_type='application/octet-stream'); assert s.read('safe/a.bin')==b'ok'


class FakeSocket:
    def __init__(self,response:bytes): self.response=response; self.sent=bytearray(); self.done=False
    def __enter__(self): return self
    def __exit__(self,*_): return False
    def sendall(self,data): self.sent.extend(data)
    def recv(self,_):
        if self.done:return b''
        self.done=True; return self.response


def test_clamav_scanner_accepts_clean_and_rejects_malware(monkeypatch):
    monkeypatch.setattr('socket.create_connection',lambda *a,**k:FakeSocket(b'stream: OK\0'))
    ClamAvTcpScanner().scan(b'hello',filename='x.pdf')
    monkeypatch.setattr('socket.create_connection',lambda *a,**k:FakeSocket(b'stream: Eicar-Test-Signature FOUND\0'))
    with pytest.raises(ValueError,match='malware_detected'): ClamAvTcpScanner().scan(b'bad',filename='x.pdf')
