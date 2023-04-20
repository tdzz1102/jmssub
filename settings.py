class Settings:
    sub_url = 'https://jmssub.net/members/getsub.php?service=719998&id=988bd515-6f99-409c-8ef6-a64fdf0f5e95'
    v2ray_config_path = '/root/jmssub-dev/config.json'
    log_path = '/root/jmssub-dev/log.log'

    redis_port = 6379
    redis_db = 9

    docker = True
    container_name = 'v2ray-dev'
    ports = [34567, 45678]

