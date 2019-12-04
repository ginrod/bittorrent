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

import threading

PIECE_LENGTH = 1024


TRACKER_IP = "localhost"
TRACKER_PORT = "5000"
TRACKER_URL = f"{TRACKER_IP}:{TRACKER_PORT}"

def get_infohash(metainfo):
    return hashlib.sha1(torrent_parser.encode(metainfo["info"])).hexdigest()

class Client:

    # NUMWANT = 50
    # NO_PEER_ID = 0
    # COMPACT = 0

    '''
    FINDING TRACKER VIA BROADCAST
    '''
    def get_connection(self):
        while not self.contact:
            try : 
                self.find_contact()
            except: 
                pass
            time.sleep(0.5)
    
    def find_contact(self, localhost_only=False):
        broadcast_msg = { 'operation': 'DISCOVER', 'join': False, 'ip': self.ip, 'port': self.port, 
                          'sender': [-1, self.ip, self.port]  }
        broadcast_msg = json.dumps(broadcast_msg).encode()
        
        def do_broadcast():
            udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            if localhost_only:
                for p in range(8000, 8081):
                # for p in range(8002, 8003):
                    udp_sock.sendto(broadcast_msg, ('127.0.0.1', p))
            else:
                udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                udp_sock.sendto(broadcast_msg, ('255.255.255.255', 6666))

        # threading._start_new_thread(do_broadcast, )
        do_broadcast()

        # Set socket as server
        server = socket.socket()
        server.settimeout(0.5)
        # try:    
        server.bind(('', self.port))
        # except Exception as ex:
        #     pass

        server.listen(1)
        dht_peer, _ = server.accept()
        # self.contact = tuple(json.loads(self._recvall(dht_peer)))        
        self.contact = tuple(json.loads(dht_peer.recv(1024)))        
        
        # Set socket as client
        # self.close_connection()
        server.close()

    def check_tracker(self):
        import socket
        sock = socket.socket()
        try:
            sock.connect((self.contact))
        except:
            self.get_connection()
            TRACKER_IP, TRACKER_PORT = self.contact
            TRACKER_URL = f"{TRACKER_IP}:{TRACKER_PORT}"

    def get_tracker_url(self):
        self.check_tracker()
        return f"{self.contact[0]}:{self.contact[1]}"

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
            "name": metainfo["info"]["short_name"],
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

    def request_metainfo(self, connection, name):
        url = urllib.parse.urlencode({"name": name})
        connection.request("GET", f"/search?{url}")
        response = json.loads(connection.getresponse().read())
        response = response[0] if response != "NO" else response 

        if response == "NO":
            raise Exception("There is not .torrent for that name")

        infohash = get_infohash(response)
        # return [(key, response[key]["metainfo"]) for key in response]
        return infohash, response

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

        # _ = self.get_tracker_url()
        # TRACKER_IP, TRACKER_PORT = self.contact
        connection = http.client.HTTPConnection(TRACKER_IP, TRACKER_PORT)
        print("Connected to TRACKER")
        
        try:
            infohash, _metainfo = self.request_metainfo(connection, name)
        except Exception:
            print(f"The tracker doesn't know about any torrent of name: {name}")
            return

        complete = False

        while not complete:
            TRACKER_URL = self.get_tracker_url()
            request = self.create_announce_request(_metainfo, TRACKER_URL, uploaded, downloaded, "started")
            response = self.make_announce_request(connection, request)
            bitfield = self.peer.download(response['peers'], _metainfo)
            complete = all(bitfield)

        connection.request("PUT", urllib.parse.quote(f"/have/{self.id}/{self.ip}/{self.port}/complete/{_metainfo['info']['short_name']}/{infohash}"))
        self._print(f"downloaded successfully: {_metainfo['info']['short_name']}{_metainfo['info']['extension']}")
        connection.close()

    def share(self, path, mode="single-file", root_name=""):
        #create the .torrent
        TRACKER_URL = self.get_tracker_url()
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

    import argparse, socket
    parser = argparse.ArgumentParser()
    parser.add_argument('-port', '--port', type=int, default=7008)
    parser.add_argument('-ip', '--ip', type=str, default='192.168.1.100')

    args = parser.parse_args()

    ip = args.ip
    port = int(args.port)

    if not ip:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)

    paths = ["/home/tony/Desktop/Orientación del proyecto/COOL Language Reference Manual.pdf",
            "/media/tony/01D54288CC477C00/Escuela/Música Estudiar, Música Relajante para Reducir Estres, Música para Trabajar, Estudiar, ☯3043.mp4",
            "/media/tony/01D54288CC477C00/Escuela/4to/Sistemas distribuidos/Distributed_Systems_3-190909.pdf",
            "/media/tony/01D54288CC477C00/Music/23. Justin Timberlake - Cant Stop The Feeling.mp3",
            "/home/tony/Desktop/23. Justin Timberlake - Cant Stop The Feeling.mp3",
            "/home/tony/Desktop/Distributed_Systems_3-190909.pdf",
	        "/media/tony/Tony1/Peliculas/The Lion King/The Lion King [El Rey Leon] [2019] [1080p] [Dual Audio].mkv",
            "/media/tony/Tony1/Peliculas/Drama/El Club de Los Incomprendidos [2014] [1,29 Gb]/El Club de Los Incomprendidos [2014].avi"]

    names = [
            "COOL Language Reference Manual",
            "Música Estudiar, Música Relajante para Reducir Estres, Música para Trabajar, Estudiar, ☯3043",
            "Distributed_Systems_3-190909",
            "23. Justin Timberlake - Cant Stop The Feeling",
            "23. Justin Timberlake - Cant Stop The Feeling",
            "Distributed_Systems_3-190909",
	        "The Lion King [El Rey Leon] [2019] [1080p] [Dual Audio]", "El Club de Los Incomprendidos [2014]"
            ]

    # ip = "localhost"
    # port = int(input("port:"))
    c = Client(ip, port)

    while True:
        op, param = input('>>>').split('|')
        if op == 'share':
            c.share(param)
        elif op == 'get':
            c.download(param)
        elif op == 'exit':
            break

        # command = input(">>>").split()
        # if not command:
        #     continue
        # elif command[0] == "share":
        #     if len(command == 2):
        #         c.share(int(command[1]))
        #     else:
        #         c.share([int(p) for p in command[2:]], root_name=command[1])
        # elif command[0] == "get":
        #     c.download(names[int(command[1])])
        # elif command[0] == "exit":
        #     break
        # else:
        #     continue
