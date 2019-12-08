import torrent_parser
import hashlib, os, time


import flask

import sys

from database import Database

import json, utils_tracker, socket, threading

from utils_tracker import get_key

def _print(text, flag='a'):
    with open("tracker_trace", flag) as f:
        f.write(f"{text}\n")

def get_infohash(metainfo):
    return hashlib.sha1(torrent_parser.encode(metainfo["info"])).hexdigest()

class Tracker:
    # 6666
    def attend_clients(self):
        sock = socket.socket()
        sock.bind((self.database.ip, 6660))
        sock.listen(256)

        def attend(client):
            while True:
                try:
                    msg = client.recv(1024)
                except: continue
                if not msg:
                    break
                # threading._start_new_thread(self.proccess_message, ())
            threading.current_thread()._delete()

        def attend_saved(sock):
            try:
                attend(c)
            except Exception as ex:
                print('EXCEPCION EN attend_clients')
                print(ex)
            threading.current_thread()._delete()

        while True:
            c, _ = sock.accept()
            threading._start_new_thread(attend_saved, (c,))

    def proccess_message(self, data, addr):
        if data['operation'] == 'DISCOVER':
            ip, port = str(data['ip']), int(data['port'])
            sock = socket.socket()
            try:
                sock.connect((ip, port))
                server_ip = self.database.ip
                my_addr = server_ip, 5000
                sock.send(json.dumps(my_addr).encode())
            except: pass
            sock.close()
        threading.current_thread()._delete()

    def attend_new_nodes(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.database.ip, 6666))
        while True:
            try:
                msg, _ = sock.recvfrom(1024)
            except Exception as e:
                print('EXCEPCION EN attend_new_nodes')
                print(e)
                continue

            if msg is not None:
                data = json.loads(msg)
                addr = data['sender'][1], data['sender'][2]
                threading._start_new_thread(self.proccess_message, (data, addr))

    def __init__(self, ip, port=5050, request_interval=5, min_interval=5):
        self.database = Database(ip, port)
        threading._start_new_thread(self.attend_clients, ())
        threading._start_new_thread(self.attend_new_nodes, ())

    def build_response(self, request):
        answer = {}
        answer["peers"] = self.database[get_key(request['name'] + request['infohash'] + 'peers')]
        answer["peers"] = answer["peers"] if answer["peers"] else []
        return answer


app = flask.Flask(__name__)

TRACKER = None

@app.route('/announce')
def announce():
    response = TRACKER.build_response(flask.request.args)
    return json.dumps(response)

@app.route('/have/<client_id>/<ip>/<port>/<portion>/<name>/<infohash>', methods=["PUT"])
def have(client_id, ip, port, portion, name, infohash):
    TRACKER.database[name + infohash + "peers"] = utils_tracker.assign(data={"ip": ip, "port": int(port), "id": client_id}, to_update=True)
    return ""

@app.route('/search')
def search():
    pattern_torrents_keys_dic = TRACKER.database[utils_tracker.INDEX_KEY]
    name = flask.request.args["name"]
    
    torrent_keys = []
    if name in pattern_torrents_keys_dic:
        torrent_keys = pattern_torrents_keys_dic[name]

    metainfos = []
    for key in torrent_keys:
        metainfo = TRACKER.database[key]
        metainfos.append(metainfo)
    return json.dumps(metainfos)

@app.route('/metainfo/<client_id>/<ip>/<port>', methods=["POST"])
def metainfo(client_id, ip, port):
    if flask.request.method == "POST":
        metainfo_encoded = flask.request.data
        metainfo_decoded = torrent_parser.decode(metainfo_encoded)
        name = metainfo_decoded["info"]["name"]
        infohash = get_infohash(metainfo_decoded)

        #Real app
        TRACKER.database[name + infohash + "metainfo"] = utils_tracker.assign(metainfo_decoded, name)
        TRACKER.database[name + infohash + "peers"] = utils_tracker.assign({"ip": ip, "port": int(port), "id": client_id}, to_update=True)

        return ""

if __name__ == "__main__":
    #real app
    import argparse, socket
    parser = argparse.ArgumentParser()
    parser.add_argument('-ip', '--ip', type=str, default=None)
    parser.add_argument('-port', '--port', type=int, default=5050)

    args = parser.parse_args()
    IP = args.ip
    port = int(args.port)

    if not IP:
        hostname = socket.gethostname()
        IP = socket.gethostbyname(hostname)

    TRACKER = Tracker(IP, port)

    # TRACKER = Tracker("localhost", 5000)

    app.run(host=IP, port=5000)