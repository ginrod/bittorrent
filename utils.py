import uuid
import socket
import time
import json, datetime, os

import torrent_parser
import hashlib, sys

# Kademlia ID used to do a name index in database
INDEX_KEY = 10

def get_key(s: str):
    h = hashlib.sha1(s.encode())
    return int.from_bytes(h.digest(), byteorder=sys.byteorder)

def get_prefixes(name):
    prefixes = set()
    for i in range(len(name) + 1):
        pref = name[0:i]
        prefixes.add(pref)
    
    return prefixes

def get_suffixes(name):
    suffixes = set(['', name])
    for i in range(len(name) + 1):
        suff = name[i:len(name)]
        suffixes.add(suff)
    
    return suffixes

def get_prefixes_and_suffixes(name):
    substrings = set(['', name])
    for i in range(len(name) + 1):
        pref = name[0:i]
        suff = name[i:len(name)]
        substrings.add(pref)
        substrings.add(suff)

    return substrings

def get_substrings(name):
    substrings = set(['', name])
    for i in range(len(name)):
        for j in range(i + 1, len(name) + 1):
            substrings.add(name[i:j])
    
    return substrings

def parse_to_json(obj):
    if isinstance(obj, datetime.datetime):
        return [obj.year, obj.month, obj.day,
                obj.hour, obj.minute, obj.second, obj.microsecond]

def parse_from_json(database):
    for k in database:
        try:
            database[k]['timeo'] = datetime.datetime(*(database[k]['timeo']))
            database[k]['timer'] = datetime.datetime(*(database[k]['timer']))
        except :
            database[k][1]['timeo'] = datetime.datetime(*(database[k][1]['timeo']))
            database[k][1]['timer'] = datetime.datetime(*(database[k][1]['timer']))

    return database


def get_infohash(metainfo):
    return hashlib.sha1(torrent_parser.encode(metainfo["info"])).hexdigest()


def load_json(path):
    data = {}
    try:
        with open(path) as json_file:
            data = parse_from_json(json.load(json_file))
    except:
        # dump_json(data, path)
        pass

    return data

def dump_json(data, path):
    idx = path.rindex('/')
    dirs = path[:idx]
    create_dirs(dirs)
    # if not data:
    #     x = 6

    with open(path, 'w') as json_file:
        json.dump(data, json_file, default=parse_to_json)

def dumps_json(data) -> str:
    return json.dumps(data, default=parse_to_json)



def build_PING_msg(sender):
    return {'operation': 'EXECUTE',
            'method': 'PING',
            'sender': list(sender),
            'key': generate_random_id()}


def build_FIND_NODE_msg(ID, sender):
    return {'operation': 'EXECUTE',
            'method': 'FIND_NODE', 'id': ID,
            'sender': list(sender),
            'key': generate_random_id()}


def build_FIND_VALUE_msg(ID, sender):
    return {'operation': 'EXECUTE',
            'method': 'FIND_VALUE', 'id': ID,
            'sender': list(sender),
            'key': generate_random_id()}

def build_STORE_msg(key, value, publisher, sender, value_type='json', to_update=False):
    return {'operation': 'EXECUTE',
            'method': 'STORE', 'store_key': key, 'store_value': value,
            'sender': list(sender), 'publisher': list(publisher),
            'key': generate_random_id(),
            'value_type': value_type,
            'to_update': to_update }

def build_PUBLISH_msg(key, value, value_type='json', to_update=False):
    return {'method': 'PUBLISH',
            'store_key': key, 'store_value': value,
            'key': generate_random_id(),
            'value_type': value_type,
            'to_update': to_update }

def build_LOOKUP_msg(ID):
    return {'operation': 'EXECUTE',
            'method': 'LOOKUP', 'id': ID,
            'key': generate_random_id() }

def build_UPDATE_msg(key, value, publisher, sender):
    return {'operation': 'EXECUTE',
            'method': 'UPDATE', 'store_key': key, 'store_value': value,
            'sender': list(sender), 'publisher': list(publisher),
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


def save_file(path, file_bytes):
    idx = path.rindex('/')
    dirs = path[:idx]
    create_dirs(dirs)
    with open(path, 'wb') as f:
        f.write(file_bytes)

def load_file(path):
    with open(path, 'rb') as f:
        data = f.read()
    
    return data

def close_connection(sock):
    try: sock.shutdown(socket.SHUT_WR)
    except: pass
    try: sock.close()
    except: pass

def create_dirs(path):
    try: os.makedirs(path)
    except OSError: 
        pass

def assign(data, name='', to_update=False):
    return (data, name, to_update) 

def build_xor_table(address_space):
    xor_table = [[i ^ j for i in range(address_space)] for j in range(address_space)]
    return xor_table