import json
import socket

def send_msg(_dict, s: socket.socket):
    s.sendall(json.dumps(_dict).encode())

def handshake(s: socket.socket, infohash, peer_id, request=True):
    msg_type = "request" if request else "response"
    send_msg({"message": "handshake", "infohash": infohash, "peer_id": peer_id, "type": msg_type}, s)

def keep_alive(s):
    send_msg({"message": "keep-alive"}, s)

def intersted(s):
    send_msg({"message": "interested"}, s)

def not_interested(s):
    send_msg({"message": "not interested"}, s)

def choke(s):
    send_msg({"message": "choke"}, s)

def unchoke(s):
    send_msg({"message": "unchoke"}, s)

def have(s, piece_index):
    send_msg({"message": "have", "piece index": piece_index}, s)

def bitfield_answer(s, _bitfield):
    send_msg({"message": "bitfield", "bitfield": _bitfield}, s)

def bitfield_request(s, infohash):
    send_msg({"message": "bitfield", "infohash": infohash}, s)

def request(s, index):
    send_msg({"message": "request", "index": index}, s)

def piece(s, index, file_name, length):
    send_msg({"message": "piece", "index": index, "file_name": file_name, "length": length}, s)

def cancel(s, index, begin, length):
    send_msg({"message": "cancel", "begin": begin, "index": index, "length": length}, s)

def data(s, piece):
    s.sendall(piece)