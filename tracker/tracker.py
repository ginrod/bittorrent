import torrent_parser
import hashlib, os, time


import flask

import sys

from database import Database

import json

def _print(text, flag='a'):
    with open("tracker_trace", flag) as f:
        f.write(f"{text}\n")

def get_infohash(metainfo):
    return hashlib.sha1(torrent_parser.encode(metainfo["info"])).hexdigest()

class Tracker:

    def __init__(self, ip, port=5050, request_interval=5, min_interval=5):
        self.database = Database(ip, port)
        # self._request_interval = request_interval
        # self._min_interval = min_interval
        # self._tracker_id = hashlib.sha1((str(os.getpid()) + str(time.time())).encode()).hexdigest()

    def build_response(self, request):

        answer = {}

        stats = self.database[request['name']][request['infohash']]

        answer["peers"] = stats["peers_complete"] + stats["peers_incomplete"]

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
    if portion == "complete":
        TRACKER.database[name][infohash]["peers_complete"].append({"ip": ip, "port": int(port), "id": client_id})
    else:
        TRACKER.database[name][infohash]["peers_incomplete"].append({"ip": ip, "port": int(port), "id": client_id})
    return ""

@app.route('/search')
def search():
    metainfos = TRACKER.database[flask.request.args["name"]]
    
    return json.dumps(metainfos)

@app.route('/metainfo/<client_id>/<ip>/<port>', methods=["POST"])
def metainfo(client_id, ip, port):
    if flask.request.method == "POST":
        metainfo_encoded = flask.request.data
        metainfo_decoded = torrent_parser.decode(metainfo_encoded)
        name = metainfo_decoded["info"]["short_name"]
        infohash = get_infohash(metainfo_decoded)

        try:
            TRACKER.database[name][infohash] = {"metainfo": metainfo_decoded}
        except:
            TRACKER.database[name] = {infohash: {"metainfo": metainfo_decoded}}

        TRACKER.database[name][infohash]["peers_complete"] = [{"ip": ip, "port": int(port), "id": client_id}]
        TRACKER.database[name][infohash]["peers_incomplete"] = []

        print_database()
        return ""

def print_database():
    print(".torrents:")

    for name in TRACKER.database:
        for infohash in TRACKER.database[name]:
            _metainfo = TRACKER.database[name][infohash]["metainfo"]
            print(f"name: {_metainfo['info']['short_name']}\textension: {_metainfo['info']['extension']}\tsize: {_metainfo['info']['length']}\tpiece length: {_metainfo['info']['piece_length']}\tpieces: {_metainfo['info']['no_pieces']}")
    print("---" * 40 + "\n")

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