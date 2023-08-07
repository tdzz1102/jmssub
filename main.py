import json
import threading
import requests
import subprocess
import uvicorn
from exporter import app as exporter_app
from loguru import logger
from base64 import b64decode
from urllib.parse import urlsplit
from time import sleep
from shadowsocks import ShadowSocks
from vmess import Vmess
from settings import Settings


logger.add(Settings.jmssub_log_path)
server: subprocess.Popen | None = None


def update_sub() -> dict:
    with requests.Session() as se:
        se.trust_env = False
        subscription_content = se.get(Settings.subscription_url).text
    share_links = b64decode(subscription_content).decode('utf-8').splitlines()
    
    try:
        with open(Settings.v2ray_config_path) as f:
            v2ray_config: dict = json.load(f)
    except Exception as e:
        # print(
        #     f'The config.json for v2ray not found in "{Settings.v2ray_config_path}".')
        # sys.exit(1)
        raise e

    outbounds: list = v2ray_config['outbounds']
    outbounds.clear()

    ss_items: list[ShadowSocks] = []
    vmess_items: list[Vmess] = []

    for share_link in share_links:
        url = urlsplit(share_link)
        protocal = url.scheme
        tmp = b64decode(url.netloc + '===').decode('utf-8')
        if protocal == 'ss':
            ss = ShadowSocks(tmp)
            ss_items.append(ss)
        elif protocal == 'vmess':
            vm = Vmess(tmp)
            vmess_items.append(vm)

    if vmess_items and vmess_items[1].ping():
        outbounds.append(Vmess.gen_outbound(vmess_items[1:2]))  # japan only
        logger.info('Japan server is avaliable. Use it!')
    else:
        if not Settings.vmess_only and ss_items:
            outbounds.append(ShadowSocks.gen_outbound(ss_items))
        if vmess_items:
            outbounds.append(Vmess.gen_outbound(vmess_items))
        print(outbounds)
        logger.info('Japan server is unavaliable. Use others...')
    if not outbounds:
        logger.error('No avaliable server now.')
    logger.info('Subscription update OK.')

    if len(ss_items) + len(vmess_items) == 0:
        logger.error('No avalible server.')

    with open(Settings.v2ray_config_path, 'w') as f:
        json.dump(v2ray_config, f, indent=4)
    
    return v2ray_config


def restart_server():
    global server
    if server:
        server.terminate()
        server.wait()
    with open(Settings.v2ray_log_path, 'a') as f:
        server = subprocess.Popen([Settings.bin_path, 'run', '-c', Settings.v2ray_config_path], stdout=f)


def start_exporter():
    uvicorn.run(exporter_app, host='0.0.0.0', port=Settings.exporter_port, ssl_keyfile=Settings.key_path, ssl_certfile=Settings.cert_path)


def main():
    exporter_thread = threading.Thread(target=start_exporter, daemon=True)
    exporter_thread.start()
    v2ray_config = {}
    while True:
        try:
            new_v2ray_config = update_sub()
            if new_v2ray_config != v2ray_config:
                # config changed. restart server!
                v2ray_config = new_v2ray_config
                restart_server()
        except Exception as e:
            logger.error(str(e))
            raise e
        sleep(60)


if __name__ == '__main__':
    main()
