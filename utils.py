import uuid
import socket
import time
import json, datetime

import torrent_parser
import hashlib

def parse_to_json(obj):
    if isinstance(obj, datetime.datetime):
        return [obj.year, obj.month, obj.day,
                obj.hour, obj.minute, obj.second, obj.microsecond]

def parse_from_json(database):
    for k in database:
        database[k]['timeo'] = datetime.datetime(*(database[k]['timeo']))
        database[k]['timer'] = datetime.datetime(*(database[k]['timer']))

    return database


def get_infohash(metainfo):
    return hashlib.sha1(torrent_parser.encode(metainfo["info"])).hexdigest()


def load_json(path):
    data = {}
    try:
        with open(path) as json_file:
            data = parse_from_json(json.load(json_file))
    except:
        with open(path, 'w') as json_file:
            json.dump(data, json_file, default=parse_to_json)

    return data

def dump_json(data, path):
    with open(path, 'w') as json_file:
        json.dump(data, json_file, default=parse_to_json)



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


def load(name):
    f = None
    try:
        f = open(name, "r+b")
    except:
        f = open(name, "wb")
    return f


# def sendall_to(msg, addr, socket, time_out=5):
#     sent = 0
#     start = time.time()
#     while sent < len(msg) and time.time() - start < time_out:
#         sent += socket.sendto(msg, addr)
#     if sent != len(msg):
#         raise socket.timeout

def get_answer(expected_key, s:socket.socket, attempts=3):

    for _ in range(attempts):
        data = json.loads(s.recvfrom(1024)[0])

        if data['key'] == expected_key:
            return data

    raise socket.timeout

def build_xor_table(address_space):
    xor_table = [[i ^ j for i in range(address_space)] for j in range(address_space)]
    return xor_table
