import copy


class ShadowSocks:
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
        self.method, self.port = kakera[0], int(kakera[2])
        self.password, self.address = kakera[1].split('@')

    # def outbound(self):
    #     cfg = copy.deepcopy(ShadowSocks.template)
    #     server = copy.copy(ShadowSocks.snext)
    #     server['address'] = self.address
    #     server['method'] = self.method
    #     server['port'] = self.port
    #     server['password'] = self.password
    #     cfg['settings']['servers'].append(server)
    #     return cfg

    @staticmethod
    def gen_outbound(items):
        cfg = copy.deepcopy(ShadowSocks.template)
        for item in items:
            server = copy.copy(ShadowSocks.snext)
            server['address'] = item.address
            server['method'] = item.method
            server['port'] = item.port
            server['password'] = item.password
            cfg['settings']['servers'].append(server)
        return cfg