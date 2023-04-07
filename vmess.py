import copy

class Vmess:
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

    def __init__(self, tmp: dict) -> None:
        self.port = int(tmp['port'])
        self.id = tmp['id']
        self.alterId = int(tmp['aid'])
        self.address = tmp['add']
        # self.transport = tmp['net']
        # self.security = tmp['type']

    # def outbound(self):
    #     cfg = deepcopy(Vmess.template)
    #     server = cfg['settings']['vnext'][0]
    #     server['address'] = self.address
    #     server['port'] = self.port
    #     user = server['users'][0]
    #     user['id'] = self.id
    #     user['alterId'] = self.alterId
    #     return cfg
    
    @staticmethod
    def gen_outbound(items):
        cfg = copy.deepcopy(Vmess.template)
        for item in items:
            server = copy.deepcopy(Vmess.snext)
            server['address'] = item.address
            server['port'] = item.port
            user = server['users'][0]
            user['id'] = item.id
            user['alterId'] = item.alterId
            cfg['settings']['vnext'].append(server)
        return cfg
