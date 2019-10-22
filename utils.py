import uuid

def build_PING_msg(senderID):
    return { 'operation': 'EXECUTE',
             'method': 'PING',
             'sender_id': senderID,
             'key': generate_random_id() }

def build_FIND_NODE_msg(ID, senderID):
    return { 'operation': 'EXECUTE',
            'method': 'FIND_NODE', 'id' : ID,
            'sender_id': senderID,
            'key': generate_random_id() }

def build_FIND_VALUE_msg(ID, senderID):
    return { 'operation': 'EXECUTE',
             'method': 'FIND_VALUE', 'id' : ID,
             'sender_id' : senderID,
             'key': generate_random_id() }

def build_STORE_msg(key, value, senderID):
    return { 'operation': 'EXECUTE',
             'method': 'STORE', 'store_key' : key, 'store_value' : value,
             'sender_id': senderID,
             'key': generate_random_id() }

def generate_random_id():
    return uuid.uuid4().hex

class TimeOutException(Exception):
    pass
