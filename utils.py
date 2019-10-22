import uuid

def build_PING_msg():
    msg = { 'method': 'PING' }
    return msg

def build_FIND_NODE_msg(ID):
    msg = { 'method': 'FIND_NODE', 'id' : ID }
    return msg

def build_FIND_VALUE_msg(ID):
    msg = { 'method': 'FIND_VALUE', 'id' : ID }
    return msg

def build_STORE_msg(key, value):
    msg = { 'method': 'STORE', 'storeKey' : key, 'storeValue' : value }
    return msg

def generate_random_id():
    return uuid.uuid4().hex

class TimeOutException(Exception):
    pass
