import json
import sys
from settings import Settings
from loguru import logger
from base64 import b64decode
from urllib.request import urlopen
from urllib.parse import urlsplit
from pathlib import Path
from shadowsocks import ShadowSocks
from vmess import Vmess


logger.add(Settings.log_path)


def main():
    return_content = urlopen(Settings.subscription_url).read()
    share_links = b64decode(return_content).decode('utf-8').splitlines()

    try:
        with open(Settings.v2ray_config_path) as f:
            v2ray_config: dict = json.load(f)
    except:
        print(
            f'The config.json for v2ray not found in {Settings.v2ray_config_path}.')
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

    with open(Settings.v2ray_config_path, 'w') as f:
        json.dump(v2ray_config, f, indent=4)

    if Settings.docker:
        import docker
        client = docker.from_env()
        try:
            ct = client.containers.get(Settings.container_name)
            ct.restart()
            logger.info('Container restart OK.')
        except:
            ports = {}
            for port in Settings.ports:
                ports[f'{port}/tcp'] = port
            ct = client.containers.run(
                image='v2fly/v2fly-core',
                command=f'run -c /etc/v2fly/config.json',
                volumes={Settings.v2ray_config_path: {
                    'bind': '/etc/v2fly/config.json', 'mode': 'rw'}},
                ports=ports,
                detach=True,
                name=Settings.container_name
            )
            logger.warning('No container found. Start a new one.')


main()
