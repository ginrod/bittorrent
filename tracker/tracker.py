import torrent_parser
import hashlib, os, time


import flask

import sys

from database import Database

import json, utils_tracker, socket, threading

def _print(text, flag='a'):
    with open("tracker_trace", flag) as f:
        f.write(f"{text}\n")

def get_infohash(metainfo):
    return hashlib.sha1(torrent_parser.encode(metainfo["info"])).hexdigest()

class Tracker:
    # 6666
    def attend_clients(self):
        sock = socket.socket()
        sock.bind(('', 6660))
        sock.listen(256)

        def attend(client):
            while True:
                try:
                    msg = client.recv(1024)
                except: continue
                if not msg:
                    break
                # threading._start_new_thread(self.proccess_message, ())

        while True:
            c, _ = sock.accept()
            threading._start_new_thread(attend, (c,))

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

    def attend_new_nodes(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', 6666))
        while True:
            msg, _ = sock.recvfrom(1024)

            if msg is not None:
                data = json.loads(msg)
                addr = data['sender'][1], data['sender'][2]
                threading._start_new_thread(self.proccess_message, (data, addr))

    def __init__(self, ip, port=5050, request_interval=5, min_interval=5):
        self.database = Database(ip, port)
        # self._request_interval = request_interval
        # self._min_interval = min_interval
        # self._tracker_id = hashlib.sha1((str(os.getpid()) + str(time.time())).encode()).hexdigest()
        threading._start_new_thread(self.attend_clients, ())
        threading._start_new_thread(self.attend_new_nodes, ())

    def build_response(self, request):

        answer = {}

        # name + infohash + "peers_complete"
        ID = request['name'] + request['infohash'] + 'peers'
        hashed = utils_tracker.get_key(ID)
        answer["peers"] = self.database[request['name'] + request['infohash'] + 'peers']

        # answer["complete"] = stats["complete"]
        # answer["incomplete"] = stats["incomplete"]

        # answer["interval"] = self._request_interval
        # answer["min_interval"] = self._min_interval

        # if request.tracker_id:
        #     answer["tracker_id"] = request.tracker_id
        # else:
        #     answer["tracker_id"] = self._tracker_id

        # elif request.type == "Scrape":
        #     files = {}

        #     collection = []
        #     if request.infohashes:
        #         collection = request.infohashes
        #     else:
        #         collection = self.database

        #     for key in collection:
        #             files[key] = {
        #                 "complete": self.database[key]["complete"],
        #                 "incomplete": self.database[key]["incomplete"],
        #                 "downloaded": self.database[key]["downloaded"],
        #                 "name": self.database[key]["name"]
        #                 }

        #     answer["files"] = files
        # else:
        #     raise Exception("Invalid type of request")

        return answer


app = flask.Flask(__name__)

# DATABASE = {}

# TRACKER = Tracker("0.0.0.0", 8000)
TRACKER = None

@app.route('/announce')
def announce():
    response = TRACKER.build_response(flask.request.args)
    return json.dumps(response)

@app.route('/have/<client_id>/<ip>/<port>/<portion>/<name>/<infohash>', methods=["PUT"])
def have(client_id, ip, port, portion, name, infohash):
    # if portion == "complete":
        # TRACKER.database[name][infohash]["peers_complete"].append({"ip": ip, "port": int(port), "id": client_id})
    TRACKER.database[name + infohash + "peers"] = utils_tracker.assign(data={"ip": ip, "port": int(port), "id": client_id}, to_update=True)
    # else:
    #     # TRACKER.database[name][infohash]["peers_incomplete"].append({"ip": ip, "port": int(port), "id": client_id})
    #     TRACKER.database[name + infohash + "peers"] = utils_tracker.assign(data={"ip": ip, "port": int(port), "id": client_id}, to_update=True)
    return ""

@app.route('/search')
def search():
    # metainfos = TRACKER.database[flask.request.args["name"]]
    pattern_torrents_keys_dic = TRACKER.database[utils_tracker.INDEX_KEY]
    name = flask.request.args["name"]
    torrent_keys = pattern_torrents_keys_dic[name]
    # torrents_keys [flask.request.args['name']]
    # {'Maluma': [12831271, 32082198372]
    # metainfo = TRACKER.Databse[32082198372]
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
        name = metainfo_decoded["info"]["short_name"]
        infohash = get_infohash(metainfo_decoded)

        print(f'NAME: {name}')
        ID = name + infohash + "peers"
        hashed = utils_tracker.get_key(ID)
        # print('SETTING metainfo')
        TRACKER.database[name + infohash + "metainfo"] = utils_tracker.assign(metainfo_decoded, name)
        

        # print('SETTING peers list')
        TRACKER.database[name + infohash + "peers"] = utils_tracker.assign({"ip": ip, "port": int(port), "id": client_id}, to_update=True)
        # TRACKER.database[name + infohash + "peers_incomplete"] = []

        # print_database()
        return ""

# def print_database():
#     print(".torrents:")

#     for name in TRACKER.database:
#         for infohash in TRACKER.database[name]:
#             _metainfo = TRACKER.database[name][infohash]["metainfo"]
#             print(f"name: {_metainfo['info']['short_name']}\textension: {_metainfo['info']['extension']}\tsize: {_metainfo['info']['length']}\tpiece length: {_metainfo['info']['piece_length']}\tpieces: {_metainfo['info']['no_pieces']}")
#     print("---" * 40 + "\n")

# @app.route('/scrape')
# def scrape():
#     request = ScrapeRequest(flask.request)
#     response = TRACKER.build_response(request)
#     return flask.Response(response)

if __name__ == "__main__":
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

    app.run(host="0.0.0.0", port=5000)