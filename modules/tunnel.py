import os
from threading import Thread
from subprocess import Popen, DEVNULL

def prepare(id):
    print('Installing lite-http-tunnel...')
    os.system('npm i -g lite-http-tunnel > /dev/null')

    data = os.getenv('TUNNEL_DATA')
    assert(data, 'no TUNNEL_DATA env')
    url, login, password = data.split('=')

    url = url.replace('%id%', id)
    os.system(f'lite-http-tunnel config server {url}')
    os.system(f'lite-http-tunnel auth {login} {password}')

    return url


def run(port):
    process = Popen(f'lite-http-tunnel start {port}', stdout=DEVNULL)
    process.wait()


def get(id, port=7860):
    url = prepare(id)
    Thread(target=run, args=(port,)).start()
    print(f'Tunnel is ready: {url}')
    return url
