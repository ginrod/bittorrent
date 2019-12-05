import json, hashlib, torrent_parser, socket

def find_contact(ip, port=37000, localhost_only=False):
    broadcast_msg = { 'operation': 'DISCOVER', 'join': False, 'ip': ip, 'port': port, 
                        'sender': [-1, ip, port]  }
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
    server.bind(('', port))
    # except Exception as ex:
    #     pass

    server.listen(1)
    dht_peer, _ = server.accept()
    # self.contact = tuple(json.loads(self._recvall(dht_peer)))        
    contact = tuple(json.loads(dht_peer.recv(1024)))        
    
    # Set socket as client
    # self.close_connection()
    server.close()
    return contact

def load_json(path):
    data = {}
    try:
        with open(path) as json_file:
            data = parse_from_json(json.load(json_file))
    except:
        # dump_json(data, path)
        pass

    return data

def get_infohash(metainfo):
    return hashlib.sha1(torrent_parser.encode(metainfo["info"])).hexdigest()