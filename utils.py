import uuid
import socket
import time
import json
import datetime
import os
import threading

# Kademlia ID used to do a name index in database
INDEX_KEY = 10

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

# 8000 EXECUTE 8000 PUBLISH store_key: 7 store_value: Mi_primera_publicacion publisher: 0
def build_PINGS_input(begin, end):
    with open(f'files/PINGS From {begin} until {end}.txt', 'w') as file:
        for i in range(begin, end + 1):
            for j in range(i + 1, end + 1):
                file.write(f'{8000 + i} RPC {8000 + j} PING\n')
            file.write('\n')


def parse_to_json(obj):
    if isinstance(obj, datetime.datetime):
        return [obj.year, obj.month, obj.day,
                obj.hour, obj.minute, obj.second, obj.microsecond]


def parse_from_json(database):
    # print(database)
    for k in database:
        database[k]['timeo'] = datetime.datetime(*(database[k]['timeo']))
        database[k]['timer'] = datetime.datetime(*(database[k]['timer']))

    return database


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

def dumps_json(data):
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

def build_STORE_msg(key, value, publisher, sender, value_type='json'):
    return {'operation': 'EXECUTE',
            'method': 'STORE', 'store_key': key, 'store_value': value,
            'sender': list(sender), 'publisher': list(publisher),
            'key': generate_random_id(),
            'value_type': value_type }

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

def generate_random_id():
    return uuid.uuid4().hex

def build_xor_table(address_space):
    xor_table = [[i ^ j for i in range(address_space)]
                 for j in range(address_space)]
    return xor_table

def save_file(path, file_bytes):
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
    except OSError: pass

def assign(data, name='', to_update=False):
    return (data, name, to_update) 