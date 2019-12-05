import flask
from flask import jsonify
# import client
# from client.client import Client
import torrent_parser
import json
import tracker
from tracker.tracker import Database
import sys

def get_open_port():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("",0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port

INDEX_KEY = 661843241451724053717825306583068845753374048118

DB_IP = None

CONTACT = None

app = flask.Flask(__name__)

CLIENT = None

@app.route('/search/<name>')
def search(name):
    db = Database(DB_IP, get_open_port())
    CONTACT = db.contact
    _dict = db[INDEX_KEY]
    try:
        torrent_keys = _dict[name]
    except:
        return flask.jsonify([])

    metainfos = []

    for tk in torrent_keys:
        value = _dict[tk]
        if not value:
            continue
        metainfos.append(torrent_parser.decode(value))

    return flask.jsonify(metainfos)

@app.route('/shared')
def shared():
    shared_files = json.load("client/files_shared.json")
    answer = []
    for infohash in shared_files:
        answer.append({"path": shared_files[infohash]["path"], "size": shared_files[infohash]["length"]})
    return flask.jsonify(answer)

@app.route('/share/<path>')
def share(path):
    name, size = CLIENT.share(path)
    return jsonify(name=name, size=size)


if __name__ == "__main__":
    import argparse, socket
    parser = argparse.ArgumentParser()

    parser.add_argument('-ip', '--ip', type=str, default=None)
    args = parser.parse_args()

    IP = args.ip
    # CLIENT = Client(IP, get_open_port())


    if not ip:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
    app.run("0.0.0.0", 5001)
