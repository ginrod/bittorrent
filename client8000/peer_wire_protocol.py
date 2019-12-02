import json
from peer_wire_messages import handshake, data, send_msg, bitfield_answer, bitfield_request, piece
import threading
import socket
import hashlib
import os
import time
import utils

import http.client
import urllib

TRACKER_IP = "localhost"
TRACKER_PORT = 5000

class Peer:
    """ Represents a network node that participates in a file exchange """
    def __init__(self, ip, client_port, server_port):
        #Generate an id related to the local machine
        self.id = hashlib.sha1((str(os.getpid()) + str(time.time())).encode()).hexdigest()

        #Initialize ip and ports
        self.ip = ip
        self.client_port = client_port
        self.server_port = server_port

        #initialize sockets
        self.tcp_client = socket.socket()

        self.tcp_server = socket.socket()
        self.tcp_server.bind((self.ip, self.server_port))
        self.tcp_server.listen(256)

        self.files = utils.load_json(f"files_shared{self.client_port}.json")


    def download(self, peers, metainfo):
        """ Makes all the actions needed to download a file
                peers: List of peers wich contains totally o partially the file
                infohash: 20-byte SHA1 hash of the info dictionary on the metainfo file
        """

        infohash = utils.get_infohash(metainfo)

        active_peers = [] #Peers of the peers list that are connected

        #handshake round
        print("Performing the handshake round...")
        for p in peers:
            rp = f"({p['ip']}, {p['port'] + 1})"
            print(f"Connecting to {rp}")
            self.tcp_client = socket.socket()
            self.tcp_client.connect((p["ip"], p["port"] + 1))
            print(f"Sending handshake msg to {rp}")
            handshake(self.tcp_client, infohash, self.id)
            handshake_answer = self.tcp_client.recv(1024)
            print(f"Handshake answer from {rp} received")
            if not handshake_answer:
                print(f"The handshake msg from {rp} is empty")
                self.tcp_client.close()
                continue
            handshake_answer = json.loads(handshake_answer)
            # if handshake_answer["peer_id"] != p["id"]:
            #     print("There are different ids")
            #     self.tcp_client.close()
            #     continue
            active_peers.append(p)
            print(f"{rp} added to the list of active peers")


        print("Handshake round finished")
        print(f"Active peers: {active_peers}")

        #bitfield round
        print("\n\nPerforming bitfield round")
        peers_bitfields = []
        for i, p in enumerate(active_peers.copy()):
            try:
                addr = (p['ip'], p['port'] + 1)
                #connect to remote peer
                print(f"Connecting to {addr}")
                self.tcp_client = socket.socket()
                self.tcp_client.connect(addr)

                #get remote peer's bitfield
                print(f"Requesting {addr} bitfield")
                bitfield_request(self.tcp_client, infohash)
                bitfield_answer = self.recv_all(self.tcp_client)
                print(f"Bifield from {addr} received")

                #If no answer from remote_peer, close the connection
                if not bitfield_answer:
                    print("Closing the connection")
                    self.tcp_client.close()
                    active_peers.pop(i)
                    continue

                bitfield_answer = json.loads(bitfield_answer)
                peers_bitfields.append(bitfield_answer["bitfield"])
            except (ConnectionResetError, ConnectionRefusedError, socket.timeout):
                active_peers.pop(i)
                continue

        print("Bitfield round finished\n\n\n")

        print(f"Ready to download file with infohash: {infohash}")

        self.files[infohash] = {}
        file_info = self.files[infohash]
        file_info["bitfield"] = [False for _ in range(metainfo["info"]["no_pieces"])]
        file_info["piece_length"] = metainfo["info"]["piece_length"]

        connection = http.client.HTTPConnection(TRACKER_IP, TRACKER_PORT)
        msg_sent = False

        for j, b in enumerate(peers_bitfields):
            for i in range(len(b)):
                if b[i] and not file_info["bitfield"][i]:
                    try:
                        #connect to the peer
                        self.tcp_client = socket.socket()
                        addr = (active_peers[j]['ip'], active_peers[j]['port'] + 1)
                        self.tcp_client.connect(addr)

                        #request the piece
                        print(f"Requesting piece {i}")
                        piece(self.tcp_client, i, metainfo["info"]["name"], metainfo["info"]["piece_length"])

                        #download the piece
                        print(f"Copying piece {i}")
                        # data = self.tcp_client.recv(metainfo["info"]["piece_length"] * 2)
                        data = self.recv_all(self.tcp_client)
                        if not data:
                            continue
                        print(f"Piece {i} copied successfully")

                        #write the whole piece in the partial file of the download
                        print(f"Copying piece {i}")
                        try:
                            with open(f"downloaded/{metainfo['info']['short_name']}{metainfo['info']['extension']}", "r+b") as f:
                                piece_length = metainfo["info"]["piece_length"]
                                #set the offset of the file in the correct place of the piece
                                f.seek(piece_length * i, 0)
                                #write the piece
                                f.write(data)
                        except:
                            with open(f"downloaded/{metainfo['info']['short_name']}{metainfo['info']['extension']}", "wb") as f:
                                piece_length = metainfo["info"]["piece_length"]
                                f.seek(piece_length * i, 0)
                                f.write(data)

                        print(f"Piece {i} downloaded successfully")

                        if not msg_sent:
                            connection.request("PUT", urllib.parse.quote(f"/have/{self.id}/{self.ip}/{self.client_port}/incomplete/{metainfo['info']['short_name']}/{infohash}"))
                            msg_sent = True

                        #mark the piece in the bitfield
                        self.files[infohash]["bitfield"][i] = True

                        #update the 'files_shared' file
                        with open(f"files_shared{self.client_port}.json", "w") as json_file:
                            json.dump(self.files, json_file)

                        #close the connection with tracker
                        connection.close()

                    except (ConnectionResetError, ConnectionRefusedError, socket.timeout):
                        pass

        return self.files[infohash]["bitfield"]

    def accept_connections(self):

        while True:
            connection, addr = self.tcp_server.accept()
            threading._start_new_thread(self.serve, (connection, addr))

    def serve(self, connection: socket.socket, addr):


        print("Serving on port: " + str(self.server_port))
        #Peers may close a connection if they receive no messages for a certain period of time.
        #Two minutes is the default value for timeout
        connection.settimeout(120)

        infohash = ""

        msg = connection.recv(1024)
        if not msg:
            return

        msg = json.loads(msg)

        if msg["message"] == "handshake":
            print(msg)
            print(f"Handshake from {addr}")
            #If the client doesn't contain the file, then it closes the connection with the remote peer
            print(f"Files: {self.files}")
            if msg["infohash"] not in self.files:

                print("Closing the conection...")
                connection.close()
                return

            print("correct infohash")
            #If the peer contains the file, then sends a handshake msg to the remote peer
            infohash = msg ["infohash"]
            handshake(connection, msg["infohash"], self.id)
            print(f"handshake answer sended to {addr}")

        elif msg["message"] == "keep-alive":
            return

        elif msg["message"] == "interested":
            peer_interested = True

        elif msg["message"] == "not interested":
            peer_interested = False

        elif msg["message"] == "have":
            return

        elif msg["message"] == "bitfield":
            print(f"Bitfield from {addr}")
            bitfield_answer(connection, self.files[msg['infohash']]["bitfield"])

        elif msg["message"] == "piece":
            with open(f"{msg['file_name']}", "rb") as f:
                f.seek(msg['index'] * msg['length'])
                chunk = f.read(msg['length'])
                data(connection, chunk)
        connection.close()


    def recv_all(self, connection: socket.socket):
        data = b""
        chunk = connection.recv(1024)
        while chunk:
            data += chunk
            chunk = connection.recv(1024 * 1024)
        return data

    def print(self, data):
        with open("peer_history", "a") as h:
            h.write(f"Peer({self.ip}, {self.client_port}, {self.server_port}): {data}\n")

if __name__ == "__main__":
    A = Peer("127.0.0.1", 8000, 8001)