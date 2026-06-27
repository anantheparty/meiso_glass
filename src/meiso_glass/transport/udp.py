from __future__ import annotations

import socket
from dataclasses import dataclass

from meiso_glass.protocol import MeisoMessage


@dataclass
class UDPTransport:
    bind_host: str
    bind_port: int
    timeout_s: float = 0.2

    def __post_init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.bind_host, self.bind_port))
        self.sock.settimeout(self.timeout_s)

    def close(self) -> None:
        self.sock.close()

    def send(self, msg: MeisoMessage, host: str, port: int) -> None:
        self.sock.sendto(msg.to_bytes(), (host, port))

    def recv(self) -> tuple[MeisoMessage | None, tuple[str, int] | None]:
        try:
            data, addr = self.sock.recvfrom(65535)
            return MeisoMessage.from_bytes(data), addr
        except TimeoutError:
            return None, None
