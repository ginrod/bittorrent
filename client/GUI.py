import flask
import client
import torrent_parser
import json
import sys
import utils_client
import threading

class AttributeDict(dict):

    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value

def get_open_port():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("",0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port



CONTACT = None

app = flask.Flask(__name__)

CLIENT = None

def json_load(json):
    json = json.loads(json) if isinstance(json, str) else json
    return AttributeDict(json)

@app.route('/share', methods=['POST'])
def share():
    data = flask.request.data
    _json = json.loads(data)
    path = flask.request.json["path"]
    CLIENT.share(path)

@app.route('/search/<name>')
def search(name):
    metainfos = CLIENT.search(name)
    response = [{"name": m["info"]["name"], "size": m["info"]["length"], "id": torrent_parser.encode(m)} for m in metainfos]
    return flask.jsonify(response)

@app.route('/download', methods=['POST'])
def download():
    to_download = []
    for m in to_download:
        m_decoded = torrent_parser.decode(m)
        threading._start_new_thread(CLIENT.download, (m_decoded,))



if __name__ == "__main__":
    import argparse, socket
    parser = argparse.ArgumentParser()

    parser.add_argument('-ip', '--ip', type=str, default="192.168.1.104")
    args = parser.parse_args()

    ip = args.ip
    if not ip:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)

    port = 5001
    while True:
        port = get_open_port()
        if port != 5001:
            break

    CLIENT = client.Client(ip, port)

    app.run("0.0.0.0", 5001)
