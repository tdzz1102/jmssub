import json
import sys
from requests import Session
from loguru import logger
from base64 import b64decode
from urllib.parse import urlsplit
from time import sleep
from shadowsocks import ShadowSocks
from vmess import Vmess
from settings import Settings


logger.add(Settings.log_path)
sub_content = ''
# count = 0


def update_sub():
    global sub_content
    share_links = b64decode(sub_content).decode('utf-8').splitlines()

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
            ct = client.containers.run(
                image='v2fly/v2fly-core',
                command=f'run -c /etc/v2fly/config.json',
                volumes={Settings.v2ray_config_path: {
                    'bind': '/etc/v2fly/config.json', 'mode': 'rw'}},
                network_mode='host',
                detach=True,
                name=Settings.container_name
            )
            logger.warning('No container found. Start a new one.')


def main():
    se = Session()
    se.trust_env = False
    while True:
        logger.info('Working...')
        global sub_content
        try:
            new_sub_content = se.get(Settings.subscription_url).text
            if new_sub_content != sub_content:
                logger.warning('Detected subscription change.')
                sub_content = new_sub_content
                update_sub()
        except Exception as e:
            logger.error(str(e))
        sleep(60)
    
    
if __name__ == '__main__':
    main()