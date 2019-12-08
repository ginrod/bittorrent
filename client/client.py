import os
import hashlib
import time
import http.client
import torrent_parser
from peer_wire_protocol import Peer
import metainfo
import json
import sys
import urllib

import threading, utils_client

PIECE_LENGTH = 1024

#develop
TRACKER_IP = "localhost"
TRACKER_PORT = 5000

TRACKER_URL = f"{TRACKER_IP}:{TRACKER_PORT}"

def get_infohash(metainfo):
    return hashlib.sha1(torrent_parser.encode(metainfo["info"])).hexdigest()

class Client:

    # NUMWANT = 50
    # NO_PEER_ID = 0
    # COMPACT = 0

    '''
    GET TRACKER
    '''
    def get_connection(self):
        while not self.contact:
            try :
                self.contact = utils_client.find_contact(self.ip)
            except:
                pass
            # time.sleep(0.5)

    def check_tracker(self):
        import socket
        sock = socket.socket()
        try:
            sock.connect((self.contact))
        except Exception as ex:
            self.contact = None
            self.get_connection()

        return self.contact

    def get_tracker_url(self):
        return f'{self.contact[0]}:{self.contact[1]}'

    def __init__(self, ip, port, contact=None):
        self.ip = ip
        self.port = port
        self.id = hashlib.sha1((str(os.getpid()) + str(time.time())).encode()).hexdigest()
        self.tracker_id = None
        self.peer = Peer(self.ip, self.port, self.port + 1)
        self.contact = contact

        threading._start_new_thread(self.peer.accept_connections,())

    def _print(self, text, flag='a'):
        with open('history', flag) as h:
            h.write(f"({self.ip}, {self.port}): {text}\n")

    def create_announce_request(self, metainfo, tracker_url: str, uploaded, downloaded, event, numwant=None, no_peer_id=None):

        params = {
            "name": metainfo["info"]["name"],
            "infohash": get_infohash(metainfo),

            "peer_id": self.id,
            "ip": self.ip,
            "port": self.port,

            "uploaded": uploaded,
            "downloaded": downloaded,
            "left": metainfo["info"]["length"] - downloaded,

            "event": event,

            # "compact": self.COMPACT,
            # "no_peer_id": self.NO_PEER_ID,
            # "numwant": self.NUMWANT,
            # "tracker_id": self.tracker_id
        }

        url = "/announce?" + urllib.parse.urlencode(params)

        return url

    def request_metainfo(self, name):
        TRACKER_IP, TRACKER_PORT = self.check_tracker()
        connection = http.client.HTTPConnection(TRACKER_IP, TRACKER_PORT)
        url = urllib.parse.urlencode({"name": name})
        connection.request("GET", f"/search?{url}")
        response = json.loads(connection.getresponse().read())
        return response

    def make_announce_request(self, connection, url):
        connection.request("GET", url)
        response = connection.getresponse()
        r = response.read()
        data = json.loads(r)
        return data

    def download(self, _metainfo):
        print(f"Downloading {_metainfo['info']['name']}...")
        downloaded = 0
        uploaded = 0

        # TRACKER_IP, TRACKER_PORT = self.check_tracker()
        # connection = http.client.HTTPConnection(TRACKER_IP, TRACKER_PORT)
        print("Connected to TRACKER")

        infohash = utils_client.get_infohash(_metainfo)

        self.peer.files_shared_lock.acquire()
        self.peer.files[infohash] = {}
        file_info = self.peer.files[infohash]
        file_info["bitfield"] = [False for _ in range(_metainfo["info"]["no_pieces"])]
        file_info["piece_length"] = _metainfo["info"]["piece_length"]
        file_info["path"] = f"downloaded/{_metainfo['info']['name']}"
        file_info["length"] = _metainfo["info"]["length"]
        with open(f"files_shared.json", "w") as json_file:
            json.dump(self.peer.files, json_file)
        self.peer.files_shared_lock.release()

        complete = False
        start = 0

        while not complete:
            #real app
            TRACKER_IP, TRACKER_PORT = self.check_tracker()
            connection = http.client.HTTPConnection(TRACKER_IP, TRACKER_PORT)
            TRACKER_URL = self.get_tracker_url()
            request = self.create_announce_request(_metainfo, TRACKER_URL, uploaded, downloaded, "started")
            response = self.make_announce_request(connection, request)
            start = self.peer.download(response['peers'], _metainfo, start)
            # complete = (start == _metainfo['info']['no_pieces'])
            complete = all(file_info["bitfield"])

        try: connection.close()
        except: pass
        print(f"{_metainfo['info']['name']} downloaded successfully!!")

    def perform_download(self, _metainfo):
        threading._start_new_thread(self.download, (_metainfo,))

    def perform_share(self, path):
        threading._start_new_thread(self.share, (path,))

    def share(self, path):
        #create the .torrent

        print(f"sharing {path}")

        #real app
        self.check_tracker()
        TRACKER_URL = self.get_tracker_url()

        _metainfo = metainfo.create_metainfo(path, TRACKER_URL)
        _metainfo_encoded = torrent_parser.encode(_metainfo)

        infohash = hashlib.sha1(torrent_parser.encode(_metainfo["info"])).hexdigest()

        #update the files_shared.json
        self.peer.files_shared_lock.acquire()
        self.peer.files[infohash] = {"bitfield": [True for _ in range(_metainfo["info"]["length"]//_metainfo["info"]["piece_length"] + 1)],
                                     "piece_length": _metainfo["info"]["piece_length"],
                                     "path": path
                                    }

        with open(f"files_shared.json", 'w') as f:
            json.dump(self.peer.files, f)

        self.peer.files_shared_lock.release()

        #connect to the tracker
        #real app
        TRACKER_IP, TRACKER_PORT = self.check_tracker()
        connection = http.client.HTTPConnection(TRACKER_IP, TRACKER_PORT)

        #upload the .torrent
        headers = {"Content-type": "text/plain"}
        connection.request("POST", f"/metainfo/{self.id}/{self.ip}/{self.port}", _metainfo_encoded, headers)
        connection.getresponse()

        connection.request("PUT", urllib.parse.quote(f"/have/{self.id}/{self.ip}/{self.port}/complete/{_metainfo['info']['name']}/{infohash}"))

        print(f"shared: {_metainfo['info']['name']}")

        return _metainfo["info"]["name"], _metainfo["info"]["length"]


def concat(command):
    path = ""
    for s in command[2:]:
        path += s
    return path

if __name__ == "__main__":

    import argparse, socket
    parser = argparse.ArgumentParser()
    parser.add_argument('-port', '--port', type=int, default=7008)
    parser.add_argument('-ip', '--ip', type=str, default=None)

    args = parser.parse_args()

    ip = args.ip
    port = int(args.port)

    if not ip:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)

    c = Client(ip, port)

    while True:
        try:
            op, param = input('>>>').split('|')
            if op == 'share':
                c.perform_share(param)
            elif op == 'get':
                _metainfos = c.request_metainfo(param.lower().strip())
                if _metainfos == []:
                    print("There isn't a torrent for that name on the network")
                    continue
                for i, m in enumerate(_metainfos):
                    print(f"{i}. {m['info']['name']}")
                idx = int(input("Select file to download:"))
                c.perform_download(_metainfos[idx])
            elif op == 'exit':
                break
            else:
                continue
        except Exception as e:
            print(e)
            continue