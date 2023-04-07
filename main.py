import json
import yaml
import sys
from loguru import logger
from base64 import b64decode
from urllib.request import urlopen
from urllib.parse import urlsplit
from pathlib import Path
from shadowsocks import ShadowSocks
from vmess import Vmess


with open(Path(__file__).parent / 'settings.yaml') as f:
    custom_config = yaml.load(f, Loader=yaml.Loader)
    
logger.add(custom_config['log_path'], format="{time} - {level} - {message}")
subscribe_url = custom_config['subscription_url']
return_content = urlopen(subscribe_url).read()
share_links = b64decode(return_content).decode('utf-8').splitlines()
# print(share_links)

v2ray_config_path = custom_config['v2ray_config_path']
try:
    with open(v2ray_config_path) as f:
        v2ray_config = json.load(f)
except:
    print(f'The config.json for v2ray not found in {v2ray_config_path}.')
    sys.exit(1)
    
outbounds: list = v2ray_config['outbounds']
outbounds.clear()

ss_items: list[ShadowSocks] = []
vmess_items: list[Vmess] = []
        
for share_link in share_links:
    url = urlsplit(share_link)
    protocal = url.scheme
    tmp = b64decode(url.netloc + '===').decode('utf-8')
    if protocal == 'ss':
        ss_items.append(ShadowSocks(tmp))
    elif protocal == 'vmess':
        vmess_items.append(Vmess(json.loads(tmp)))
        
outbounds.append(ShadowSocks.gen_outbound(ss_items))
outbounds.append(Vmess.gen_outbound(vmess_items))
logger.info('Subscription update OK.')


with open(custom_config['v2ray_config_path'], 'w') as f:
    json.dump(v2ray_config, f)
    

if custom_config['docker']:
    import docker    
    client = docker.from_env()
    try:
        ct = client.containers.get(custom_config['docker_name'])
        ct.restart()
        logger.info('Container restart OK.')
    except:
        ports = {}
        for port in custom_config['ports']:
            ports[f'{port}/tcp'] = port
        ct = client.containers.run('v2fly/v2fly-core', command=f'run -c /etc/v2fly/config.json', volumes={v2ray_config_path: {'bind': '/etc/v2fly/config.json', 'mode': 'rw'}}, ports=ports, detach=True)
        logger.warning('No container found. Start a new one.')
