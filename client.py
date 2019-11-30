import socket
import json
import utils
from database import Database

def start(Input):
    s = socket.socket()
    s.bind(('localhost', 5000))

    s.connect(('127.0.0.1', 8006))

    msg = utils.build_PUBLISH_msg(8, 'foo')


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=str, default='127.0.0.1')
    parser.add_argument('-p', '--port', type=int, default=5000)

    args = parser.parse_args()

    # start(args.input)
    hostname = socket.gethostname()    
    IP = socket.gethostbyname(hostname)
    IP = '192.168.43.144'
    import time
    s = time.time()
    # print(s)
    database = Database(IP, args.port)
    # database[2] = utils.assign('AL FIN PINCHA')
    # print(database[2])
    # database[4] = utils.assign('Dato 4')
    # database[3] = utils.assign('Dato 3')
    # database[6] = utils.assign(('Dato 6', True, 'soy una tupla :-)'))
    # database[5] = utils.assign('Dato 5')
    # print(f'5:{database[5]}')
    # print(f'6:{database[6]}')
    # print(f'3:{database[3]}')
    # print(f'4:{database[4]}')
    data = []
    with open('files/torrents/real.torrent', 'rb') as f:
        data = f.read()

    database[7] = utils.assign(data, name='real.torrent')
    # loaded = database[7]
    # equals = data == loaded

    # print(equals)
    # import threading

    # threading.Thread()

    print('Resultado(s) obtenido en', time.time() - s, ' segundos')