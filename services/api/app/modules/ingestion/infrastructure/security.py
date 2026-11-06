from __future__ import annotations

import socket
import struct


class DisabledMalwareScanner:
    """Development/test adapter. Production must use ClamAV and fail closed."""
    def scan(self, payload: bytes, *, filename: str) -> None:
        return None


class ClamAvTcpScanner:
    def __init__(self, host: str = "clamav", port: int = 3310, timeout_seconds: float = 30.0) -> None:
        self.host = host
        self.port = port
        self.timeout_seconds = timeout_seconds

    def scan(self, payload: bytes, *, filename: str) -> None:
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout_seconds) as sock:
                sock.sendall(b"zINSTREAM\0")
                view = memoryview(payload)
                offset = 0
                chunk_size = 1024 * 1024
                while offset < len(view):
                    chunk = view[offset: offset + chunk_size]
                    sock.sendall(struct.pack("!I", len(chunk)))
                    sock.sendall(chunk)
                    offset += len(chunk)
                sock.sendall(struct.pack("!I", 0))
                response = bytearray()
                while True:
                    part = sock.recv(4096)
                    if not part:
                        break
                    response.extend(part)
                    if b"\0" in part:
                        break
        except OSError as exc:
            raise RuntimeError("malware_scanner_unavailable") from exc
        text = response.replace(b"\0", b"").decode("utf-8", errors="replace").strip()
        if "FOUND" in text:
            raise ValueError("malware_detected")
        if not text.endswith("OK"):
            raise RuntimeError("malware_scan_failed")
