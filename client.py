import os
import hashlib
import time
import http.client
import torrent_parser
from peer_wire_protocol import Peer
import metainfo
import json
import sys
import utils
import urllib

import threading

PIECE_LENGTH = 1024


TRACKER_IP = "localhost"
TRACKER_PORT = "5000"
TRACKER_URL = f"{TRACKER_IP}:{TRACKER_PORT}"

class Client:

    # NUMWANT = 50
    # NO_PEER_ID = 0
    # COMPACT = 0

    def __init__(self, ip, port):

        self.ip = ip
        self.port = port
        self.id = hashlib.sha1((str(os.getpid()) + str(time.time())).encode()).hexdigest()
        self.tracker_id = None
        self.peer = Peer(self.ip, self.port, self.port + 1)

        threading._start_new_thread(self.peer.accept_connections,())

    def _print(self, text, flag='a'):
        with open('history', flag) as h:
            h.write(f"({self.ip}, {self.port}): {text}\n")

    def create_announce_request(self, metainfo, tracker_url: str, uploaded, downloaded, event, numwant=None, no_peer_id=None):

        params = {
            "name": metainfo["info"]["short_name"],
            "infohash": utils.get_infohash(metainfo),

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

    def request_metainfo(self, connection, name):
        url = urllib.parse.urlencode({"name": name})
        connection.request("GET", f"/search?{url}")
        print("Response:")
        response = json.loads(connection.getresponse().read())
        return [(key, response[key]["metainfo"]) for key in response]

    def make_announce_request(self, connection, url):
        connection.request("GET", url)
        response = connection.getresponse()
        r = response.read()
        data = json.loads(r)
        return data

    def download(self, name):
        print(f"Downloading {name}...")
        downloaded = 0
        uploaded = 0

        connection = http.client.HTTPConnection(TRACKER_IP, TRACKER_PORT)
        print("Connected to TRACKER")

        #For the moment assume that the client wants the first element of the list
        infohash, _metainfo = self.request_metainfo(connection, name)[0]
        print("AA")
        complete = False
        msg_sent = False
        while not complete:
            request = self.create_announce_request(_metainfo, TRACKER_URL, uploaded, downloaded, "started")
            response = self.make_announce_request(connection, request)
            bitfield = self.peer.download(response['peers'], _metainfo)
            complete = all(bitfield)
            if any(bitfield) and not complete and not msg_sent:
                connection.request("PUT", urllib.parse.quote(f"/have/{self.id}/{self.ip}/{self.port}/incomplete/{_metainfo['info']['short_name']}/{infohash}"))
                msg_sent = True
        connection.request("PUT", urllib.parse.quote(f"/have/{self.id}/{self.ip}/{self.port}/complete/{_metainfo['info']['short_name']}/{infohash}"))
        self._print(f"downloaded successfully: {_metainfo['info']['short_name']}{_metainfo['info']['extension']}")
        connection.close()

    def share(self, path):
        #create the .torrent
        _metainfo = metainfo.create_metainfo([path], TRACKER_URL)
        _metainfo_encoded = torrent_parser.encode(_metainfo)

        infohash = hashlib.sha1(torrent_parser.encode(_metainfo["info"])).hexdigest()

        #update the files_shared.json
        self.peer.files[infohash] = {"bitfield": [True for _ in range(_metainfo["info"]["length"]//_metainfo["info"]["piece_length"] + 1)],
                                     "piece_length": _metainfo["info"]["piece_length"],
                                    }
        with open(f"files_shared{self.port}.json", 'w') as f:
            json.dump(self.peer.files, f)

        #connect to the tracker
        connection = http.client.HTTPConnection(TRACKER_IP, TRACKER_PORT)

        #upload the .torrent
        headers = {"Content-type": "text/plain"}
        connection.request("POST", f"/metainfo/{self.id}/{self.ip}/{self.port}", _metainfo_encoded, headers)
        connection.getresponse()
        self._print(f"shared {_metainfo['info']['short_name']}{_metainfo['info']['extension']}")


def concat(command):
    path = ""
    for s in command[2:]:
        path += s
    return path

if __name__ == "__main__":

    #truncate the history
    # with open("history", "w") as h:
    #     pass

    paths = ["/home/tony/Desktop/Orientación del proyecto/COOL Language Reference Manual.pdf",
            "/media/tony/01D54288CC477C00/Escuela/Música Estudiar, Música Relajante para Reducir Estres, Música para Trabajar, Estudiar, ☯3043.mp4",
            "/media/tony/01D54288CC477C00/Escuela/4to/Sistemas distribuidos/Distributed_Systems_3-190909.pdf",
            "/media/tony/01D54288CC477C00/Music/23. Justin Timberlake - Cant Stop The Feeling.mp3",
            "/home/tony/Desktop/23. Justin Timberlake - Cant Stop The Feeling.mp3",
            "/home/tony/Desktop/Distributed_Systems_3-190909.pdf"]

    names = [
            "COOL Language Reference Manual",
            "Música Estudiar, Música Relajante para Reducir Estres, Música para Trabajar, Estudiar, ☯3043",
            "Distributed_Systems_3-190909",
            "23. Justin Timberlake - Cant Stop The Feeling",
            "23. Justin Timberlake - Cant Stop The Feeling",
            "Distributed_Systems_3-190909"
            ]

    ip = "localhost"
    port = int(input("port:"))
    c = Client(ip, port)

    while True:
        command = input(">>>").split()
        if not command:
            continue
        elif command[0] == "share":
            c.share(paths[int(command[1])])
        elif command[0] == "get":
            c.download(names[int(command[1])])
        elif command[0] == "exit":
            break
        else:
            continue