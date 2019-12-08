import json
from peer_wire_messages import handshake, data, send_msg, bitfield_answer, bitfield_request, piece
import threading
import socket
import hashlib
import os
import time
import utils_client

import http.client
import urllib

# TRACKER_IP = None
# TRACKER_PORT = None

class Peer:

    '''
    GET TRACKER
    '''
    def get_connection(self):
        while not self.contact:
            try :
                self.contact = utils_client.find_contact(self.ip)
            except:
                pass
            time.sleep(0.5)

    def check_tracker(self):
        import socket
        sock = socket.socket()
        try:
            sock.connect((self.contact))
        except:
            self.contact = None
            self.get_connection()

        return self.contact

    """ Represents a network node that participates in a file exchange """
    def __init__(self, ip, client_port, server_port):
        #Generate an id related to the local machine
        self.id = hashlib.sha1((str(os.getpid()) + str(time.time())).encode()).hexdigest()

        #Initialize ip and ports
        self.ip = ip
        self.client_port = client_port
        self.server_port = server_port

        #initialize sockets
        # self.tcp_client = socket.socket()

        self.tcp_server = socket.socket()
        self.tcp_server.bind((self.ip, self.server_port))
        self.tcp_server.listen(256)

        self.files = utils_client.load_json(f"files_shared.json")
        self.files_shared_lock = threading.Lock()
        self.contact = None


    def download(self, peers, metainfo, start):

        infohash = utils_client.get_infohash(metainfo)

        active_peers = [] #Peers of the peers list that are connected

        #handshake round
        
        for p in peers:
            if p['ip'] == self.ip and p['port'] == self.client_port:
                continue

            rp = f"({p['ip']}, {p['port'] + 1})"
            # print(f"Connecting to {rp}")
            tcp_client = socket.socket()
            tcp_client.settimeout(1)
            try:
                tcp_client.connect((p["ip"], p["port"] + 1))
            except Exception as e:
                print(e)
                continue

            # print(f"Sending handshake msg to {rp}")
            handshake(tcp_client, infohash, self.id)
            try:
                handshake_answer = tcp_client.recv(1024)
            except:
                continue
            if not handshake_answer:
                tcp_client.close()
                continue
            handshake_answer = json.loads(handshake_answer)
            active_peers.append(p)

        #bitfield round
        peers_bitfields = []
        for i, p in enumerate(active_peers.copy()):
            try:
                addr = (p['ip'], p['port'] + 1)
                #connect to remote peer
                # print(f"Connecting to {addr}")
                tcp_client = socket.socket()
                tcp_client.settimeout(1)
                tcp_client.connect(addr)

                #get remote peer's bitfield
                # print(f"Requesting {addr} bitfield")
                bitfield_request(tcp_client, infohash)
                bitfield_answer = self.recv_all(tcp_client)
                # print(f"Bifield from {addr} received")

                #If no answer from remote_peer, close the connection
                if not bitfield_answer:
                    # print("Closing the connection")
                    tcp_client.close()
                    active_peers.pop(i)
                    continue

                bitfield_answer = json.loads(bitfield_answer)
                peers_bitfields.append(bitfield_answer["bitfield"])
            except (ConnectionResetError, ConnectionRefusedError, socket.timeout):
                active_peers.pop(i)
                continue

        # print("Bitfield round finished\n\n\n")

        # print(f"Ready to download file with infohash: {infohash}")



        
        msg_sent = False

        # for i in range(start, len(self.files[infohash]['bitfield'])):
        for i in range(0, len(self.files[infohash]['bitfield'])):
            for j, b in enumerate(peers_bitfields):
                try:

                    if b[i] and not self.files[infohash]["bitfield"][i]:
                        #connect to the peer
                        tcp_client = socket.socket()
                        
                        addr = (active_peers[j]['ip'], active_peers[j]['port'] + 1)
                        tcp_client.connect(addr)

                        #request the piece
                        # print(f"Requesting piece {i}")
                        piece(tcp_client, i, infohash, metainfo["info"]["piece_length"])

                        #download the piece
                        # print(f"Copying piece {i}")
                        # data = self.tcp_client.recv(metainfo["info"]["piece_length"] * 2)
                        data = self.recv_all(tcp_client)
                        if not data:
                            continue
                        # print(f"Piece {i} copied successfully")

                        #write the whole piece in the partial file of the download
                        # print(f"Copying piece {i}")
                        try:
                            try:
                                os.makedirs(f'downloaded')
                            except: pass
                            with open(f"downloaded/{metainfo['info']['name']}", "r+b") as f:
                                piece_length = metainfo["info"]["piece_length"]
                                #set the offset of the file in the correct place of the piece
                                f.seek(piece_length * i, 0)
                                #write the piece
                                f.write(data)
                        except:
                            try:
                                os.makedirs(f'downloaded')
                            except: pass
                            with open(f"downloaded/{metainfo['info']['name']}", "wb") as f:
                                piece_length = metainfo["info"]["piece_length"]
                                f.seek(piece_length * i, 0)
                                f.write(data)

                        # print(f"Piece {i} downloaded successfully")

                        if not msg_sent:
                            TRACKER_IP, TRACKER_PORT = self.check_tracker()
                            connection = http.client.HTTPConnection(TRACKER_IP, TRACKER_PORT)
                            connection.request("PUT", urllib.parse.quote(f"/have/{self.id}/{self.ip}/{self.client_port}/incomplete/{metainfo['info']['name']}/{infohash}"))
                            msg_sent = True

                        self.files_shared_lock.acquire()
                        #mark the piece in the bitfield
                        self.files[infohash]["bitfield"][i] = True

                        #update the 'files_shared' file
                        with open(f"files_shared.json", "w") as json_file:
                            json.dump(self.files, json_file)
                        self.files_shared_lock.release()

                        # start += 1

                        #close the connection with tracker
                        connection.close()

                except:
                    continue

        return start

    def accept_connections(self):
        
        def serve_saved(conn, ad):
            try:
                self.serve(conn, ad)
            except Exception as ex:
                print('EXCEPCION EN serve')
                print(ex)

        while True:
            connection, addr = self.tcp_server.accept()
            # threading._start_new_thread(self.serve, (connection, addr))
            threading._start_new_thread(serve_saved, (connection, addr))

    def serve(self, connection: socket.socket, addr):


        # print("Serving on port: " + str(self.server_port))
        #Peers may close a connection if they receive no messages for a certain period of time.
        #Two minutes is the default value for timeout
        connection.settimeout(120)

        infohash = ""

        try:
            msg = connection.recv(1024)
        except:
            return

        if not msg:
            return

        msg = json.loads(msg)

        if msg["message"] == "handshake":
            # print(msg)
            # print(f"Handshake from {addr}")
            #If the client doesn't contain the file, then it closes the connection with the remote peer
            # print(f"Files: {self.files}")
            if msg["infohash"] not in self.files:

                # print("Closing the conection...")
                connection.close()
                return

            # print("correct infohash")
            #If the peer contains the file, then sends a handshake msg to the remote peer
            infohash = msg ["infohash"]
            handshake(connection, msg["infohash"], self.id)
            # print(f"handshake answer sended to {addr}")

        elif msg["message"] == "keep-alive":
            return

        elif msg["message"] == "interested":
            peer_interested = True

        elif msg["message"] == "not interested":
            peer_interested = False

        elif msg["message"] == "have":
            return

        elif msg["message"] == "bitfield":
            # print(f"Bitfield from {addr}")
            bitfield_answer(connection, self.files[msg['infohash']]["bitfield"])

        elif msg["message"] == "piece":
            with open(self.files[msg["infohash"]]["path"], "rb") as f:
                f.seek(msg['index'] * msg['length'])
                chunk = f.read(msg['length'])
                data(connection, chunk)
        connection.close()
        threading.current_thread()._delete()


    def recv_all(self, connection: socket.socket):
        data = b""
        chunk = connection.recv(1024)
        while chunk:
            data += chunk
            chunk = connection.recv(1024 * 1024)
        return data


# if __name__ == "__main__":
    # A = Peer("127.0.0.1", 8000, 8001)