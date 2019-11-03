import socket
import uuid
import datetime
import json
import utils
import heapq
import math
from protocol import Node

import sys

class Peer:

    def __init__(self, node):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((node.ip, node.port))
        self.node = node

    def serve(self):
        print('Peer with ID ' + str(self.node.ID) + " serving on port: " + str(self.node.port))

        #If the peer doesn't receive a response after five seconds to it's request it desists of waiting for it
        self.socket.settimeout(5)

        #A list of requests the peer has sent but doesn't have received a response yet.
        #Every element has the structure key, address()
        pending_answers = []

        while True:
            # msg, addr = self.socket.recvfrom(1024)
            try:
                msg, addr = self.socket.recvfrom(1024)
            except socket.timeout:
                #If a TimeOut Error ocurs, the result of all pending requests is None
                for pa in pending_answers:
                    key, addr = pa
                    answer = {'operation': 'RESPONSE', 'result': None, 'key': key}
                    self.socket.sendto(json.dumps(answer).encode(), addr)
                pending_answers.clear()

                continue


            data = json.loads(msg)
            print("Data received: " + str(data))

            # A peer has to perform a method specified by other peer by RPC
            if data['operation'] == 'EXECUTE':
                result = None
                if data['method'] == 'FIND_NODE':
                    result =  self.node.FIND_NODE(data['id'])
                elif data['method'] == 'FIND_VALUE':
                    result = self.node.FIND_VALUE(data['id'])
                elif data['method'] == 'PING':
                    result = self.node.PING()
                elif data['method'] == 'STORE':
                    result = self.node.STORE(data['store_key'], data['storeValue'])
                elif data['method'] == 'LOOKUP':
                    print('\n\nID TYPE\n\n')

                    result = self.lookup(data["id"])
                if result is not None:
                    answer = {'operation': 'RESPONSE', 'result': result,
                             'key': data['key'], 'sender': [self.node.ID, self.node.ip, self.node.port] }
                    answer = json.dumps(answer).encode()
                    self.socket.sendto(answer, addr)
                    if 'sender' in data:
                        self.update(tuple(data['sender']))

            # A peer is requested to perform a RPC to other peer
            if data['operation'] == 'RPC':
                msg = None

                if data['method'] == 'FIND_NODE':
                    msg =  utils.build_FIND_NODE_msg(data['id'], self.node)
                elif data['method'] == 'FIND_VALUE':
                    msg =  utils.build_FIND_VALUE_msg(data['id'], self.node)
                elif data['method'] == 'PING':
                    msg =  utils.build_PING_msg(self.node)
                elif data['method'] == 'STORE':
                    msg = utils.build_STORE_msg(data['storeKey'], data['store_value'], self.node)

                # Add the answer of the request to the list of pending answers
                pending_answers.append((msg['key'], addr))

                if msg is not None:
                    # The address of the remote peer wich it will be used as the target of the RPC
                    addr = (data['ip'], data['port'])

                    msg = json.dumps(msg).encode()
                    print("Attempting to send data to: " + str(addr))
                    print("Data to send: " + str(msg))

                    self.socket.sendto(msg, addr)
                    print("RPC done to: " + str(addr))

            # The peer receives the answer of a RPC made before
            if data['operation'] == 'RESPONSE':
                #Look for the key of the request in the pending answers
                for pa in pending_answers:
                    if pa[0] == data['key']:
                        #remove it
                        pending_answers.remove(pa)
                        #send the answer to the client
                        self.socket.sendto(json.dumps(data).encode(), pa[1])
                self.update(data['sender'])

        self.node.print_routing_table()

    def update(self, senderNode):
        print("Updating" + str(self.node) + "...")

        senderNode = tuple(senderNode)
        senderID = senderNode[0]

        #Find the appropiate k-bucket for the sender id
        kBucket,_ = self.node.find_kBucket(senderID)

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
                    print(kBucket[0])
                    self.socket.sendto(json.dumps(msg).encode(), (leastNodeIp, leastNodePort))
                    utils.get_answer(msg['key'], self.socket)
                    kBucket.append(kBucket[0])
                    kBucket.remove(kBucket[0])
                # otherwise it's evicted from the k-bucket and the new node inserted at the tail
                except socket.timeout:
                    kBucket.remove(kBucket[0])
                    kBucket.append(senderNode)
        self.node.print_routing_table()

    def lookup(self, ID):
        f = open('lookup_debug', 'w')
        f.write(f'Performing lookup for {ID}\n')
        f.write(f'First step: getting alpha={self.node.alpha} closest nodes to {ID}\n')
        to_query = self.node.get_n_closest(ID, self.node.alpha)
        f.write(f'Result: {to_query}\n')

        pending = []
        heapq.heapify(pending)

        enquired = []

        closest_node = heapq.nsmallest(1, to_query)[0][0]

        round = 1
        while True:
            f.write(f'Round {round} of lookup({self.node}, 7)\n')
            f.write(f'Nodes to query: {to_query}\n')

            for d,n in to_query:

                # k_closest = n[1].FIND_NODE(ID, self.node.k)
                f.write(f'Performing FIND_NODE({self.node}, {n})\n')
                msg = utils.build_FIND_NODE_msg(ID, tuple(iter(self.node)))

                ip, port = n[1], n[2]
                self.socket.sendto(json.dumps(msg).encode(), (ip, port))
                k_closest = []
                try:
                    data = utils.get_answer(msg['key'], self.socket)

                    k_closest = [(t[0], tuple(t[1])) for t in data['result']]
                    print(f'AAAAAA: {k_closest}')
                    f.write(f'Result of FIND_NODE({self.node}, {n}): {k_closest}\n')
                    self.update(tuple(data['sender']))
                except socket.timeout:
                    f.write(f'Timeout during FIND_NODE({self.node}, {n})\n')
                    pass

                if (d,n) not in enquired:
                    enquired.append((d, n))

                for t in k_closest:
                    if not t in enquired and not t in to_query and not t in pending:
                        pending.append(t)

            to_query.clear()

            if pending == []:
                break

            c = heapq.nsmallest(1, pending)[0][0]
            print(c)
            print(closest_node)
            top = self.node.alpha if c <= closest_node else self.node.k
            closest_node = min(closest_node, c)
            for _ in range(top):
                try:
                    to_query.append(heapq.heappop(pending))
                except:
                    break
            f.write(f'Results after round #{round}: {enquired}\n')
            round += 1

        print(f'enquired: {enquired}')
        return heapq.nsmallest(self.node.k, enquired)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=8000)
    parser.add_argument('-i', '--id', type=int, default=1)

    args = parser.parse_args()

    ID = args.id
    node = Node(ID, '127.0.0.1', args.port, B=3, k=3, alpha=2)
    peer = Peer(node)
    peer.serve()
