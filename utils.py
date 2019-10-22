import uuid
import socket
import time
import json

def build_PING_msg(sender):
    return { 'operation': 'EXECUTE',
             'method': 'PING',
             'sender': list(sender),
             'key': generate_random_id() }

def build_FIND_NODE_msg(ID, sender):
    return { 'operation': 'EXECUTE',
            'method': 'FIND_NODE', 'id' : ID,
            'sender': list(sender),
            'key': generate_random_id() }

def build_FIND_VALUE_msg(ID, sender):
    return { 'operation': 'EXECUTE',
             'method': 'FIND_VALUE', 'id' : ID,
             'sender' : list(sender),
             'key': generate_random_id() }

def build_STORE_msg(key, value, sender):
    return { 'operation': 'EXECUTE',
             'method': 'STORE', 'store_key' : key, 'store_value' : value,
             'sender': list(sender),
             'key': generate_random_id() }

def generate_random_id():
    return uuid.uuid4().hex



def sendall_to(msg, addr, socket, time_out=5):
    sent = 0
    start = time.time()
    while sent < len(msg) and time.time() - start < time_out:
        sent += socket.sendto(msg, addr)
    if sent != len(msg):
        raise socket.timeout

def get_answer(expected_key, s:socket.socket, attempts=3):

    for _ in range(attempts):
        data = json.loads(s.recvfrom(1024)[0])

        if data['key'] == expected_key:
            return data

    raise socket.timeout
