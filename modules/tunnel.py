import os, sys
from threading import Thread
from subprocess import Popen, DEVNULL

def prepare(id):
    print('Installing simple-http-tunnel...')
    os.system('npm i -g simple-http-tunnel > /dev/null')

    data = os.getenv('TUNNEL_DATA')
    assert data, 'no TUNNEL_DATA env'
    url, login, password = data.split('=')

    url = url.replace('%id%', id)
    os.system(f'simple-http-tunnel config server {url}')
    os.system(f'simple-http-tunnel auth {login} {password}')

    return url


def run(port):
    o = sys.stdout if os.getenv('DEBUG_TUNNEL', 0) else DEVNULL
    process = Popen(f'simple-http-tunnel start {port}', stdout=o, shell=True)
    process.wait()


def get(id, port=7860):
    url = prepare(id)
    Thread(target=run, args=(port,)).start()
    print(f'Tunnel is ready: {url}')
    return url
