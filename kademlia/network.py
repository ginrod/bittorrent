import socket
import uuid
import datetime, time
import json
import utils
import heapq
import math
from protocol import Node
import threading, random
# from database import Database

import sys

def exit_thread():
    threading.current_thread()._delete()



INDEX_KEY = 661843241451724053717825306583068845753374048118

class Peer:

    def __init__(self, node, tcp_server_port=9000):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind((node.ip, node.port))

        self.lock = threading.Lock()
        self.node = node
        self.reponses = {}
        self.tcp_server_port = tcp_server_port

        self.tcp_server = socket.socket()
        self.tcp_server.bind((node.ip, tcp_server_port))
        self.tcp_server.listen(256)

        now = datetime.datetime.now()
        self.kBucketRefreshTimes = [now] * len(node.route_table)
        self.received_msgs = set()

        # utils.create_dirs('files/storage/files')
        self.recvfile_lock = threading.Lock()
        self.kBucketRefreshTimes_lock = threading.Lock()
        self.reponses_lock = threading.Lock()

    def serve(self):
        print('Peer with ID ' + str(self.node.ID) + " serving at : " +  str(self.node.ip) + ":" + str(self.node.port))

        while True:
            try:
                msg, _ = self.udp_socket.recvfrom(1024)
            except Exception as ex:
                print('EXCEPCION EN serve')
                print(ex)
                continue

            print('RECVFROM IN serve')
            if msg is not None:
                data = json.loads(msg)

                if data['key'] in self.received_msgs:
                    continue
                else:
                    self.received_msgs.add(data['key'])

                addr = data['sender'][1], data['sender'][2]
                threading._start_new_thread(self.proccess_message, (data, addr, True))

            # self.node.print_routing_table()

    def proccess_message(self, data, addr, running_in_thread=False):
        # data = json.loads(msg)
        if data['operation'] != 'DISCOVER':
            print("Data received: " + str(data))

        if data['operation'] == 'DISCOVER':
            if data['join']:
                # addr = str(data['sender'][1]), int(data['sender'][2])
                if addr != (self.node.ip, self.node.port):
                    answer = { 'operation': 'CONTACT', 'sender': list(self.node),
                            'key': data['key'] }

                    self.send_udp_msg(json.dumps(answer).encode(), addr)
                    self.update(tuple(data['sender']))
                    print(f"{data['sender']} joined")

            else:
                if addr != (self.node.ip, self.node.port):
                    ip, port = str(data['ip']), int(data['port'])
                    server_addr = (self.node.ip, self.tcp_server_port)
                    try: self.sendall(server_addr, ip, port)
                    except: pass

        elif data['operation'] == 'CONTACT':
            contact = tuple(data['sender'])
            self.update(contact)
            self.lookup_node(self.node.ID)

        # A peer has to perform a method specified by other peer by RPC
        elif data['operation'] == 'EXECUTE':
            result = None
            if data['method'] == 'FIND_NODE':
                result =  self.node.FIND_NODE(data['id'])
            elif data['method'] == 'FIND_VALUE':
                result = self.node.FIND_VALUE(data['id'])
                answer = {'operation': 'RESPONSE', 'result': result,
                            'key': data['key'], 'sender': [self.node.ID, self.node.ip, self.node.port] }
                self.sendall(answer, addr[1])
                if 'sender' in data: self.update(tuple(data['sender']))
                return

            elif data['method'] == 'PING':
                result = self.node.PING()
            elif data['method'] == 'STORE':
                key, value = data['store_key'], data['store_value']
                publisher, sender = tuple(data['publisher']), tuple(data['sender'])
                result = self.node.STORE(key, value, publisher, sender, to_update=data['to_update'])
            elif data['method'] == 'LOOKUP':
                result = self.lookup_value(data["id"])
            elif data['method'] == 'PUBLISH':
                node = self.node.asTuple()
                self.publish(data, node, node)

            if result is not None:
                answer = {'operation': 'RESPONSE', 'result': result,
                            'key': data['key'], 'sender': [self.node.ID, self.node.ip, self.node.port] }
                answer = utils.dumps_json(answer).encode()
                self.send_udp_msg(answer, addr)


                if 'sender' in data:
                    self.update(tuple(data['sender']))

        # A peer is requested to perform a RPC to other peer
        elif data['operation'] == 'RPC':
            msg = None

            if data['method'] == 'FIND_NODE':
                msg =  utils.build_FIND_NODE_msg(data['id'], self.node)
            elif data['method'] == 'FIND_VALUE':
                msg =  utils.build_FIND_VALUE_msg(data['id'], self.node)
            elif data['method'] == 'PING':
                msg =  utils.build_PING_msg(self.node)
            elif data['method'] == 'STORE':
                msg = utils.build_STORE_msg(data['storeKey'], data['store_value'], self.node, self.node)

            if msg is not None:
                # The address of the remote peer wich it will be used as the target of the RPC
                addr = (data['ip'], data['port'])
                msg = utils.dumps_json(msg).encode()
                self.send_udp_msg(msg, addr)


        # The peer receives the answer of a RPC made before
        elif data['operation'] == 'RESPONSE':
            self.set_response(data['key'], data)
            if not Node.Equals(data['sender'], self.node):
                self.update(data['sender'])
        if running_in_thread:
            exit_thread()

    def publish(self, data, publisher, sender, file_bytes=None):
        if data['value_type'] == 'file' and not file_bytes:
            file_bytes = self.recv_file()

        k_closest = [n for _, n in self.lookup_node(data['store_key'])]
        for node in k_closest:
            if data['to_update']:
                msg = utils.build_UPDATE_msg(data['store_key'], data['store_value'], publisher, sender)
                # self._update(data['store_key'], data['store_value'], publisher, sender)
            else:
                msg = utils.build_STORE_msg(data['store_key'], data['store_value'], publisher, sender, data['value_type'])
            self.sendall(msg, node[1])


        return k_closest

    def _send_file(self, file_bytes, ip):
        try:
            sock = socket.socket()
            sock.connect((ip, 9090))
            sock.sendall(file_bytes)
            sock.close()
        except ConnectionRefusedError: pass

    def _close_socket(self, sock):
        try:
            sock.close()
            sock.shutdown(socket.SHUT_WR)
        except: pass

    def _lookup_and_update(self, ID, running_in_thread=False):
        k_closest = [n for _, n in self.lookup_node(ID)]
        for n in k_closest: self.update(n)
        if running_in_thread:
            exit_thread()

    def refresh_kbuckets(self):
        copyTimes = list(self.kBucketRefreshTimes)
        for i, kBucketRefreshTime in enumerate(copyTimes):
            if datetime.datetime.now() - kBucketRefreshTime >= datetime.timedelta(seconds=10):
            # if datetime.datetime.now() - kBucketRefreshTime >= datetime.timedelta(seconds=1):
            # if datetime.datetime.now() - kBucketRefreshTime >= datetime.timedelta(hours=1):
                routing_table = self.node.route_table
                kBucket = routing_table[i]

                if len(kBucket) == 0:
                    continue

                rand_idx = random.randrange(0, len(kBucket))
                rand_ID = kBucket[rand_idx][0]
                now = datetime.datetime.now()
                threading._start_new_thread(self._update_kbucket_time, (rand_idx, now, True))
                threading._start_new_thread(self._lookup_and_update, (rand_ID, True))

    def republish_data(self):
        # !EYE!
        # For manual testing lets consider 1 hour as 10 seconds,
        # the 24 hours are 240 seconds (4 minutes)
        # For unit testing consider 1 hour as 1 second

        # my_local_database = utils.load_json(self.node.storage)
        keys_to_drop = set()

        # database = Database(self.node.ip, 5050, contact=(self.node.ip, self.tcp_server_port))
        # database = Database(self.node.ip, 5050, contact=(self.node.ip, 9000))
        for key, data in self.node.database.items():
            original_republish = True if datetime.datetime.now() - data['timeo'] < datetime.timedelta(seconds=240) else False
            # original_republish = True if datetime.datetime.now() - data['timeo'] < datetime.timedelta(seconds=24) else False
            # original_republish = True if datetime.datetime.now() - data['timeo'] < datetime.timedelta(days=1) else False

            if not original_republish:
                # database.pop(key)
                # keys_to_drop.add(key)
                # continue
                pass

            if datetime.datetime.now() - data['timer'] >= datetime.timedelta(seconds=10):
            # if datetime.datetime.now() - data['timer'] >= datetime.timedelta(seconds=1):
            # if datetime.datetime.now() - data['timer'] >= datetime.timedelta(hours=1):

                # Republishing
                # self.publish(data, data['publisher'], self.node.asTuple())
                file_bytes = None
                if data['value_type'] == 'file':
                    file_bytes = utils.load_file(data['value'])

                msg = utils.build_PUBLISH_msg(key, data['value'], data['value_type'], data['to_update'])

                k_closest = self.publish(msg, data['publisher'], self.node.asTuple(), file_bytes)
                if self.node.asTuple() not in k_closest:
                    keys_to_drop.add(key)
                # if data['value_type']

        for key in keys_to_drop:
            self.node.store_lock.acquire()
            self.node.database.pop(key)
            try:
                self.node.store_lock.release()
            except: pass

    def check_network(self, time_unit=1):

        while True:
            try:
                self.refresh_kbuckets()
                self.republish_data()
            except Exception as e:
                print(f'EXCEPCION EN check_network')
                print(e)
                pass

            time.sleep(time_unit)

    def update(self, senderNode):
        senderNode = tuple(senderNode)
        senderID = senderNode[0]
        if senderID == self.node.ID: return

        #Find the appropiate k-bucket for the sender id
        kBucket, idx = self.node.find_kBucket(senderID)

        #If the sending node already exists in the k-bucket
        if senderNode in kBucket:
            #moves it to the tail of the list
            kBucket.remove(senderNode)
            kBucket.append(senderNode)

        else:
            #if the bucket has fewer than k entries, insert it at the tail
            if len(kBucket) < self.node.k:
                kBucket.append(senderNode)
            else:

                # PING the least_recently seen node
                _, leastNodeIp, leastNodePort = kBucket[0]
                msg = utils.build_PING_msg(self.node)

                # If exists it is moved to the tail of the list and the sender node is discarded
                try:
                    # print(kBucket[0])
                    # self.send_udp_msg(utils.dumps_json(msg).encode(), (leastNodeIp, leastNodePort))
                    # self.get_response(msg['key'])
                    sock = self.sendall(msg, leastNodeIp, close=False)
                    sock.settimeout(1)
                    ans = sock.recv(1024)
                    if ans.decode() != 'PING': raise socket.timeout()

                    kBucket.append(kBucket[0])
                    kBucket.remove(kBucket[0])
                # otherwise it's evicted from the k-bucket and the new node inserted at the tail
                except socket.timeout:
                    kBucket.remove(kBucket[0])
                    kBucket.append(senderNode)

        now = datetime.datetime.now()
        threading._start_new_thread(self._update_kbucket_time, (idx, now, True))
        # self.node.print_routing_table()

    def _update_kbucket_time(self, idx, t, running_in_thread=False):
        if self.kBucketRefreshTimes[idx] >= t: return
        self.kBucketRefreshTimes_lock.acquire()
        if self.kBucketRefreshTimes[idx] >= t: return
        self.kBucketRefreshTimes[idx] = t
        try:
            self.kBucketRefreshTimes_lock.release()
        except: pass
        if running_in_thread:
            exit_thread()

    def lookup_node(self, ID):
        ID = int(ID)
        to_query = self.node.get_n_closest(ID, self.node.alpha)

        pending = []
        heapq.heapify(pending)

        myinfo = (self.node.ID ^ ID, self.node.asTuple())
        enquired = [myinfo]
        alives = [myinfo]

        if len(to_query) == 0:
            return [(self.node.ID ^ ID, self.node.asTuple())]
            # return []

        closest_node = heapq.nsmallest(1, to_query)[0][0]

        round = 1
        while True:

            for d,n in to_query:
                k_closest, data = [], None
                if not Node.Equals(n, self.node):

                    # k_closest = n[1].FIND_NODE(ID, self.node.k)
                    msg = utils.build_FIND_NODE_msg(ID, self.node.asTuple())

                    ip, port = n[1], n[2]
                    # self.send_udp_msg(utils.dumps_json(msg).encode(), (ip, port))
                    # # data = self.get_answer(msg['key'])
                    # data = self.get_response(msg['key'])

                    sock = self.sendall(msg, n[1], close=False)
                    # data = self.get_response(msg['key'])
                    data = self.recvall(sock)
                    try:
                        data = json.loads(data)
                    except: data = None
                    utils.close_connection(sock)

                    if data:
                        k_closest = [(t[0], tuple(t[1])) for t in data['result']]
                        self.update(tuple(data['sender']))

                if (d,n) not in enquired:
                    enquired.append((d, n))

                if data != None and (d,n) not in alives:
                    alives.append((d, n))

                for t in k_closest:
                    if not t in enquired and not t in to_query and not t in pending:
                        pending.append(t)

            to_query.clear()

            if pending == []:
                break

            c = heapq.nsmallest(1, pending)[0][0]
           # print(c)
            #print(closest_node)
            top = self.node.alpha if c <= closest_node else self.node.k
            closest_node = min(closest_node, c)
            for _ in range(top):
                try:
                    to_query.append(heapq.heappop(pending))
                except:
                    break
            round += 1

        # return heapq.nsmallest(self.node.k, enquired)
        return heapq.nsmallest(self.node.k, alives)

    def lookup_value(self, ID):
        to_query = self.node.get_n_closest(ID, self.node.alpha)

        pending = []
        heapq.heapify(pending)

        myinfo = (self.node.ID ^ ID, self.node.asTuple())
        enquired = [myinfo]
        alives = [myinfo]

        if len(to_query) == 0:
            founded, data, file_bytes = self.node.FIND_VALUE(ID)
            if founded: return (True, data, file_bytes)
            else: return (False, myinfo, None)
        else:
            founded, data, file_bytes = self.node.FIND_VALUE(ID)
            if founded: return (True, data, file_bytes)

        closest_node = heapq.nsmallest(1, to_query)[0][0]

        round = 1
        while True:

            for d,n in to_query:
                k_closest, data = [], None
                if not Node.Equals(n, self.node):
                    msg = utils.build_FIND_VALUE_msg(ID, self.node.asTuple())

                    sock = self.sendall(msg, n[1], close=False)
                    # data = self.get_response(msg['key'])
                    data = self.recvall(sock)
                    utils.close_connection(sock)

                    if data != None:
                        data = json.loads(data)
                        if data['result'][0]: return data['result']
                        # if data['result'][0]: return data
                        k_closest = [(t[0], tuple(t[1])) for t in data['result'][1]]
                        self.update(tuple(data['sender']))

                if (d,n) not in enquired:
                    enquired.append((d, n))

                if data != None and (d,n) not in alives:
                    alives.append((d, n))

                for t in k_closest:
                    if not t in enquired and not t in to_query and not t in pending:
                        pending.append(t)

            to_query.clear()

            if pending == []:
                break

            c = heapq.nsmallest(1, pending)[0][0]
            top = self.node.alpha if c <= closest_node else self.node.k
            closest_node = min(closest_node, c)
            for _ in range(top):
                try:
                    to_query.append(heapq.heappop(pending))
                except:
                    break
            round += 1

        return (False, heapq.nsmallest(self.node.k, enquired), None)

    def get_response(self, expected_key, timeout=2.5):
        s = time.time()
        while expected_key not in self.reponses and time.time() - s < timeout: pass
        # if expected_key in self.reponses: return self.reponses.pop(expected_key)
        # return None
        # while expected_key not in self.reponses: pass
        if expected_key not in self.reponses: return None
        self.reponses_lock.acquire()
        ans = self.reponses.pop(expected_key)
        try:
            self.reponses_lock.release()
        except: pass
        return ans

    def receive_from(self, timeout=2.5):
        # self.udp_socket.settimeout(timeout)
        msg, addr = None, None
        try:
            msg, addr = self.udp_socket.recvfrom(1024)
        # except socket.timeout: pass
        except (socket.timeout, ConnectionResetError):
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.bind((self.node.ip, self.node.port))
            try: msg, addr = self.udp_socket.recvfrom(1024)
            except (socket.timeout, ConnectionResetError): pass

        return msg, addr

    def set_response(self, key, value, timeout=2.5):
        self.reponses_lock.acquire()
        self.reponses[key] = value
        try:
            self.reponses_lock.release()
        except: pass

    def delete_response(self, key, timeout=2.5):
        self.reponses_lock.acquire()
        self.reponses.pop(key)
        try:
            self.reponses_lock.release()
        except: pass

    def discover(self, localhost_only=False):
        broadcast_msg = { 'operation': 'DISCOVER', 'join': True, 'sender': list(self.node), 'key': utils.generate_random_id() }
        broadcast_msg = utils.dumps_json(broadcast_msg)
        broadcast_msg = broadcast_msg.encode()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        if localhost_only:
            for p in range(8000, 8011):
                if p != self.node.port:
                    sock.sendto(broadcast_msg, ('127.0.0.1', p))
        else:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(broadcast_msg, ('255.255.255.255', 8081))
            # sock.sendto(broadcast_msg, ('255.255.255.255', 8081))

    def join(self):
        def has_contact(p):
            for kBucket in p.node.route_table:
                if len(kBucket) > 0: return True
            return False

        # while not has_contact(self):
        while True:
            self.discover()
            time.sleep(1)

        # self.node.print_routing_table()

    def sendall(self, msg, ip, port=9000, close=True):
        try:
            sock = socket.socket()
            sock.connect((ip, port))
            sock.sendall(utils.dumps_json(msg).encode() + b'\r\n\r\n')
            if close: utils.close_connection(sock)
            return sock
        except (TimeoutError, OSError): pass

    def send_udp_msg(self, msg, addr):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(msg, addr)

    def recv_file(self):
        self.recvfile_lock.acquire(True)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.node.ip, 9090))
        sock.listen(1)
        sender, _ = sock.accept()

        data = b''
        while True:
            # chunk = sender.recv(1024)
            chunk = sender.recv(4096)
            if not chunk:
                break
            data += chunk

        sender.close()
        sock.close()
        
        try:
            self.recvfile_lock.release()
        except: pass
        return data

    def recvall(self, client):

        def recv():
            data = b''
            while True:
                chunk = client.recv(1024)
                if not chunk:
                    break

                if chunk.endswith(b'\r\n\r\n'):
                    data += chunk[0:-4]
                    # data = chunk.replace(b'\r\n\r\n', b'')
                    break

                data += chunk

            return data

        # lock_acquired = self.lock.acquire(True)
        # if lock_acquired:
        msg = None
        try:
            msg = recv()
        except: pass

        return msg

    def attend_clients(self):

        def attend(client):
            while True:
                msg = self.recvall(client)

                if not msg:
                    break

                # print(f'RECEIVED MSG {msg}')
                data = {'method': None}
                try:
                    data = json.loads(msg)
                except:
                    pass

                if data['method'] == 'PUBLISH':
                    node = self.node.asTuple()
                    self.publish(data, node, node)
                elif data['method'] == 'LOOKUP':
                    answer = self.lookup_value(data['id'])

                    founded, result, file_bytes = answer[0], answer[1], answer[2]
                    if founded and result['value_type'] == 'file':

                        if not file_bytes: file_bytes = self.recv_file()
                        # try: client.sendall(file_bytes)
                        # except: pass
                        client.sendall(file_bytes)
                    else:
                        if not founded: result = None
                        client.sendall(utils.dumps_json(result).encode() + b'\r\n\r\n')
                    client.close()

                elif data['method'] == 'PING':
                    client.send(b'PING')
                elif data['method'] == 'STORE':
                    key, value = data['store_key'], data['store_value']
                    publisher, sender = tuple(data['publisher']), tuple(data['sender'])

                    real_value = None
                    if data['value_type'] == 'file':
                        real_value = self.recv_file()

                    self.node.STORE(key, value, publisher, sender, data['value_type'], real_value, data['to_update'])

                elif data['method'] == 'FIND_VALUE':
                    founded, result, file_bytes = self.node.FIND_VALUE(data['id'])
                    answer = {'operation': 'RESPONSE', 'result': (founded, result, file_bytes),
                                'key': data['key'], 'sender': [self.node.ID, self.node.ip, self.node.port] }

                    # client.sendall(utils.dumps_json(answer).encode() + b'\r\n\r\n')
                    answer = utils.dumps_json(answer)
                    client.sendall(answer.encode() + b'\r\n\r\n')
                    if founded and result['value_type'] == 'file':
                        # files_bytes = utils.load_file(result['value'])
                        self._send_file(file_bytes, data['sender'][1])

                    if not Node.Equals(data['sender'], self.node):
                        self.update(data['sender'])

                elif data['method'] == 'UPDATE':
                    self._update(data['store_key'], data['store_value'], data['publisher'], data['sender'])

                elif data['method'] == 'FIND_NODE':
                    result = self.node.FIND_NODE(data['id'])
                    answer = {'operation': 'RESPONSE', 'result': result,
                                'key': data['key'], 'sender': [self.node.ID, self.node.ip, self.node.port] }

                    # client.sendall(utils.dumps_json(answer).encode() + b'\r\n\r\n')
                    answer = utils.dumps_json(answer)
                    client.sendall(answer.encode() + b'\r\n\r\n')

                    if not Node.Equals(data['sender'], self.node):
                        self.update(data['sender'])
            exit_thread()

        def attend_saved(sock):
            try:
                attend(sock)
            except Exception as ex:
                print('EXCEPCION EN attend_clients')
                print(ex)
            exit_thread()

        while True:
            c, _ = self.tcp_server.accept()
            threading._start_new_thread(attend_saved, (c,))

    def attend_new_nodes(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.node.ip, 8081))
        while True:
            msg = None
            try:
                msg, _ = sock.recvfrom(1024)
            except Exception as ex:
                print('EXCEPCION EN attend_new_nodes')
                print(ex)
                continue

            if msg is not None:
                data = json.loads(msg)
                addr = data['sender'][1], data['sender'][2]
                threading._start_new_thread(self.proccess_message, (data, addr, True))

    def __del__(self):
        # open('files/destructor called', 'w')
        self._close_socket(self.udp_socket)
        self._close_socket(self.tcp_server)

    def _update_peers_list(self, key, value, publisher, sender):
        key = str(key)

        # database = utils.load_json(self.node.storage)
        # print(f'UPDATING {key}:{value}')
        if key in self.node.database:
            if not isinstance(value, list): value = [value]
            # peers_to_check = database[key]['value'] + value
            # # peers_to_check = [tuple(v) for v in peers_to_check]
            # peers_to_check = list(set(peers_to_check))
            # to_drop = set()
            # for el
            ids = set([dic['id'] for dic in self.node.database[key]['value']])
            for dic in value:
                if dic['id'] not in ids:
                    self.node.store_lock.acquire()
                    self.node.database[key]['value'].append(dic)
                    try:
                        self.node.store_lock.release()
                    except: pass
        else:
            if not isinstance(value, list): value = [value]
            self.node.STORE(key, value, publisher, sender, to_update=True)

    def _update_names_dic(self, key, value, publisher, sender):
        key = str(key)

        # database = utils.load_json(self.node.storage)

        if key not in self.node.database:
            self.node.store_lock.acquire()
            self.node.database[key] = {}
            self.node.database[key]['value'] = value
            self.node.database[key]['timeo'] = self.node.database[key]['timer'] = datetime.datetime.now()
            self.node.database[key]['value_type'] = 'json'
            self.node.database[key]['to_update'] = True
            self.node.database[key]['publisher'] = publisher
            try:
                self.node.store_lock.release()
            except: pass
        else:
            for p in value:
                if p not in self.node.database[key]['value']:
                    self.node.store_lock.acquire()
                    self.node.database[key]['value'][p] = value[p]
                    try:
                        self.node.store_lock.release()
                    except: pass
                else:
                    new_keys = self.node.database[key]['value'][p] + value[p]
                    new_keys = list(set(new_keys))
                    self.node.store_lock.acquire()
                    self.node.database[key]['value'][p] = new_keys
                    try:
                        self.node.store_lock.release()
                    except: pass

            now = datetime.datetime.now()
            if sender == publisher:
                self.node.store_lock.acquire()
                self.node.database[key]['timeo'] = now
                try:
                    self.node.store_lock.release()
                except: pass

            self.node.store_lock.acquire()
            self.node.database[key]['timer'] = now
            try:
                self.node.store_lock.release()
            except: pass

        # utils.dump_json(database, self.node.storage)

    def _update(self, key, value, publisher, sender):
        # Updating names

        if int(key) == utils.INDEX_KEY:
            self._update_names_dic(key, value, publisher, sender)
        else:
            # Updating peers list
            self._update_peers_list(key, value, publisher, sender)

# if __name__ == '__main__':
#     import argparse
#     parser = argparse.ArgumentParser()
#     parser.add_argument('-id', '--id', type=int, default=0)
#     parser.add_argument('-port', '--port', type=int, default=9000)
#     parser.add_argument('-ip', '--ip', type=str, default=None)

#     args = parser.parse_args()

#     ID = args.id
#     IP = args.ip

#     if not IP:
#         hostname = socket.gethostname()
#         IP = socket.gethostbyname(hostname)

#     node = Node(ID, IP, int(args.port), B=4, k=2, alpha=2)
#     peer = Peer(node, int(args.port))

#     while True:
#         try:
#             threading._start_new_thread(peer.join, ())
#             threading._start_new_thread(peer.check_network, ())
#             threading._start_new_thread(peer.attend_new_nodes, ())

#             peer.attend_clients
#         except Exception as ex:
#             print('UN ERROR PROVOCÓ EL REINICO DEL NODO')
#             print(ex)
#             if isinstance(ex, KeyboardInterrupt):
#                 break

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-uport', '--udp_port', type=int, default=8000)
    parser.add_argument('-id', '--id', type=int, default=-1)
    parser.add_argument('-tport', '--tcp_server_port', type=int, default=9000)
    parser.add_argument('-ip', '--ip', type=str, default=None)

    args = parser.parse_args()

    IP = args.ip
    if not IP:
        hostname = socket.gethostname()
        IP = socket.gethostbyname(hostname)

    import uuid
    ID = int(args.id)
    if ID == -1:
        ID = utils.get_key(uuid.uuid4().hex)

    node = Node(ID, IP, int(args.udp_port), B=160, k=20, alpha=3)

    peer = Peer(node, int(args.tcp_server_port))
    threading._start_new_thread(peer.join, ())
    threading._start_new_thread(peer.check_network, ())
    threading._start_new_thread(peer.attend_clients, ())
    threading._start_new_thread(peer.attend_new_nodes, ())
    peer.serve()
