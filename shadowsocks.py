import copy
from protocol import Protocol


class ShadowSocks(Protocol):
    template = {
        "protocol": "shadowsocks",
        "settings": {
            "servers": [
            ]
        }
    }

    snext = {
        "address": "",
        "method": "",
        "password": "",
        "port": 0
    }

    def __init__(self, tmp: str) -> None:
        # aes-256-gcm:pass@ip:port
        kakera = tmp.split(':')
        self.method, port = kakera[0], int(kakera[2])
        self.password, address = kakera[1].split('@')
        super().__init__(address, port)

    def outbound(self):
        server = copy.copy(ShadowSocks.snext)
        server['address'] = self.address
        server['method'] = self.method
        server['port'] = self.port
        server['password'] = self.password
        return server

    @staticmethod
    def gen_outbound(items):
        cfg = copy.deepcopy(ShadowSocks.template)
        for item in items:
            if item.ping():
                server = item.outbound()
                cfg['settings']['servers'].append(server)
        return cfg