import json
import sys
import redis
import requests
import configparser
from pathlib import Path
from loguru import logger
from base64 import b64decode
from urllib.parse import urlsplit
from time import sleep
from shadowsocks import ShadowSocks
from vmess import Vmess
from settings import Settings


config = configparser.ConfigParser()
config.read((Path(__file__).parent / 'config.ini').resolve())

# logger.add(Settings.log_path)
sub_content = ''


class RedisConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instanec._redis_client = redis.Redis(host='localhost', port=Settings.redis_port, db=Settings.redis_db, decode_responses=True)
        return cls._instance

    def get_redis_client(self) -> redis.client.Redis:
        return self._redis_client


rc = RedisConnection()


def init_db():
    r = rc.get_redis_client()
    r.set('settings:sub_url', Settings.sub_url)
    r.set('settings:v2ray_config_path', Settings.v2ray_config_path)
    r.set('settings:log_path', Settings.log_path)
    r.set('settings:docker', str(Settings.docker))
    r.set('settings:container_name', Settings.container_name)
    r.set('settings:ports', ','.join([str(x) for x in Settings.sub_url]))
    r.close()


def get_sub() -> bool:
    global sub_content
    se = requests.Session()
    se.trust_env = False
    r = rc.get_redis_client()
    sub_url = Settings.sub_url
    new_sub_content = se.get(sub_url).text
    if new_sub_content != sub_content:
        logger.warning('Sub update detacted')
        sub_content = new_sub_content
        share_links = b64decode(sub_content).decode('utf-8').splitlines()
        for i, share_link in enumerate(share_links):
            url = urlsplit(share_link)
            # ss or vmess
            protocal = url.scheme 
            # str or dict str
            desc = b64decode(url.netloc + '===')
            r.set(f'server:{i}:protocal', protocal)
            r.set(f'server:{i}:desc', desc)
            r.close()
        return True
    r.close()
    return False
    

def update_config():
    r = rc.get_redis_client()
    n = len(r.keys('server:*:protocal'))
    try:
        with open(Settings.v2ray_config_path) as f:
            v2ray_config: dict = json.load(f)
    except:
        logger.error(f'The config.json for v2ray not found in {Settings.v2ray_config_path}.')
        sys.exit(1)

    outbounds: list = v2ray_config['outbounds']
    outbounds.clear()
    ss_items, vmess_items = [], []
    for i in range(n):
        protocal = r.get(f'server:{i}:protocal')
        desc = r.get(f'server:{i}:desc')
        if protocal == 'ss':
            ss_items.append(ShadowSocks(desc))
        elif protocal == 'vmess':
            vmess_items.append(Vmess(json.loads(desc)))
            
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
    r.close()


def main():
    init_db()
    while True:
        logger.info('working...')
        if get_sub(): # 更新あり
            update_config()
        sleep(60)
    
    
if __name__ == '__main__':
    main()