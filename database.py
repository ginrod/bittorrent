import socket, json, threading, time, utils

class Database:

    def find_contact(self, localhost_only=False):
        broadcast_msg = { 'operation': 'DISCOVER', 'join': False, 'ip': self.ip, 'port': self.port, 
                          'sender': [-1, self.ip, self.port]  }
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
                udp_sock.sendto(broadcast_msg, ('255.255.255.255', 8080))

        # threading._start_new_thread(do_broadcast, )
        do_broadcast()

        # Set socket as server
        server = socket.socket()
        # server.settimeout()
        # try:    
        server.bind(('', self.port))
        # except Exception as ex:
        #     pass

        server.listen(1)
        dht_peer, _ = server.accept()
        self.contact = tuple(json.loads(self._recvall(dht_peer)))        
        
        # Set socket as client
        # self.close_connection()
        server.close()

    def get_connection(self):
        while not self.contact:
            try : 
                self.find_contact()
            except Exception as ex: 
                pass
            time.sleep(1)

    def _recvall(self, sock):
        data = b''
        while True: 
            chunk = sock.recv(1024)
            if not chunk: 
                break
            if chunk.endswith(b'\r\n\r\n'):
                data += chunk[0:-4]
                break
            data += chunk

        return data

    def __init__(self, ip='127.0.0.1', port=5000, contact=None):
        self.ip, self.port = ip, port
        self.contact = contact
        # self.contact = ('192.168.1.100', 9000)

    def __getitem__(self, ID):
   
        def get(sock):
            msg = utils.build_LOOKUP_msg(ID)
            sock.sendall(json.dumps(msg).encode() + b'\r\n\r\n')
            value = self._recvall(sock)
            founded = True
            try: founded, value = json.loads(value)
            except: pass

            if not founded: value = None
            # if not founded: raise Exception('El valor no está en la base de datos')

            return value

        sock = socket.socket() 
        try:
            sock.connect((self.contact))
            value = get(sock)
            utils.close_connection(sock)
            return value
        except:
            self.get_connection()
            sock.connect((self.contact))
        
        value = get(sock)
        utils.close_connection(sock)
        return value

    def _send_bytes(self, bytes_array):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.contact[0], 9090))
        sock.sendall(bytes_array)
        sock.close()

    def _setnames(self, name, ID):
        strings = utils.get_substrings(name)
        for s in strings:
            self._setname(s, ID)

    def _setname(self, name, ID):
        sock = socket.socket()
        
        def post():
            msg = utils.build_PUBLISH_msg(utils.INDEX_KEY, (name, ID), to_update=True)
            sock.sendall(json.dumps(msg).encode())
            
        try:
            sock.connect((self.contact))
            post()            
        except Exception as ex:
            self.get_connection()
            sock.connect((self.contact))
            post()
        
        utils.close_connection(sock)


    def __setitem__(self, ID, assign):

        value, name, to_update = assign
        if not isinstance(name, list): name = [name]
        sock = socket.socket()
        
        def post():
            msg, is_json_serializable = None, True
            is_file = False
            try:
                msg = utils.build_PUBLISH_msg(ID, value, to_update)
                msg = json.dumps(msg).encode()
            except TypeError:
                is_json_serializable = False
                path = f'files/storage/files/{name[0]}'
                msg = utils.build_PUBLISH_msg(ID, path, 'file')
                msg = json.dumps(msg).encode()
                is_file = True
                
            sock.sendall(msg + b'\r\n\r\n')
            if not is_json_serializable:
                self._send_bytes(value)
            
            if is_file:
                patterns = utils.get_substrings(name[0]) + name[1:]
                msg = utils.build_PUBLISH_msg(utils.INDEX_KEY, (patterns, key), to_update=True)
            
        try:
            sock.connect((self.contact))
            post()            
        except Exception as ex:
            self.get_connection()
            sock.connect((self.contact))
            post()
        
        utils.close_connection(sock)

    def find_keys_by_name(self, name):
        def get(sock):
            msg = utils.build_LOOKUP_msg(utils.INDEX_KEY)
            sock.sendall(json.dumps(msg).encode() + b'\r\n\r\n')
            value = self._recvall(sock)
            founded = True
            try: founded, value = json.loads(value)
            except: pass

            if not founded: value = None

            return value[name]

        sock = socket.socket() 
        try:
            sock.connect((self.contact))
            value = get(sock)
            utils.close_connection(sock)
            return value[name]
        except:
            self.get_connection()
            sock.connect((self.contact))
        
        value = get(sock)
        utils.close_connection(sock)
        return value[name]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=str, default='127.0.0.1')
    parser.add_argument('-p', '--port', type=int, default=5000)

    args = parser.parse_args()

    # start(args.input)
    database = Database('127.0.0.1', args.port)
    # database[1] = 'Hello'
    print(database[1])