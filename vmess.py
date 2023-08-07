import copy
import json
from protocol import Protocol


class Vmess(Protocol):
    template = {
        "protocol": "vmess",
        "settings": {
            "vnext": [
            ]
        },
        "streamsettings": {
            "transport": "tcp"
        },
        "mux": {
            "enabled": True
        }
    }

    snext = {
        "address": "",
        "port": 0,
        "users": [
            {
                "id": "",
                "alterId": 0
            }
        ]
    }

    def __init__(self, tmp: dict | str) -> None:
        if isinstance(tmp, str):
            tmp = json.loads(tmp)
        port = int(tmp['port'])
        address = tmp['add']
        super(). __init__(address, port)
        self.id = tmp['id']
        self.alterId = int(tmp['aid'])
        
    # get single server
    def outbound(self):
        server = copy.deepcopy(Vmess.snext)
        server['address'] = self.address
        server['port'] = self.port
        user = server['users'][0]
        user['id'] = self.id
        user['alterId'] = self.alterId
        return server
    
    @staticmethod
    def gen_outbound(items):
        cfg = copy.deepcopy(Vmess.template)
        for item in items:
            if item.ping():
                server = item.outbound()
                cfg['settings']['vnext'].append(server)
        return cfg
