import os
import subprocess
from threading import Thread

def prepare(prefix):
    print('Installing lite-http-tunnel...')
    os.system('npm i -g lite-http-tunnel > /dev/null')

    data = os.getenv('TUNNEL_DATA')
    assert(data, 'no TUNNEL_DATA env')
    url, login, password = data.split(':')

    os.system(f'lite-http-tunnel config server {url}')
    os.system(f'lite-http-tunnel config path /{prefix}')
    os.system(f'lite-http-tunnel auth {login} {password}')

    return f'{url}/{prefix}'


def run(port):
    process = subprocess.Popen(f'lite-http-tunnel start {port}', shell=True)
    process.wait()


def get(prefix, port=7860):
    url = prepare(prefix)
    Thread(target=run, args=(port,)).start()
    return url
