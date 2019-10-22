import socket
import uuid
import datetime
import json
import utils
import heapq
import math
from protocol import Node

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

                if result is not None:
                    answer = {'operation': 'RESPONSE', 'result': result,
                             'key': data['key'], 'sender': [self.node.ID, self.node.ip, self.node.port] }
                    answer = json.dumps(answer).encode()
                    self.socket.sendto(answer, addr)
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

    def update(self, senderNode):
        print("Updating" + str(self.node) + "...")

        senderNode = tuple(senderNode)
        senderID = senderNode[0]

        #Find the appropiate k-bucket for the sender id
        kBucket = self.node.find_kBucket(senderID)

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
                    self.socket.recvfrom(1024)
                    kBucket.append(kBucket[0])
                    kBucket.remove(kBucket[0])
                # otherwise it's evicted from the k-bucket and the new node inserted at the tail
                except socket.timeout:
                    kBucket.remove(kBucket[0])
                    kBucket.append(senderNode)
        self.node.print_routing_table()

    def lookup(self, ID):
        #Insert all nodes of the k-bucket list of start on a list
        nodes = self.node.get_all_nodes(ID)

        #Select the alpha closest nodes to ID
        to_query = heapq.nsmallest(self.node.alpha, nodes)

        pending = []
        heapq.heapify(pending)

        enquired = []

        closest_node = heapq.nsmallest(1, to_query)

        while True:

            for n in to_query:

                # k_closest = n[1].FIND_NODE(ID, self.node.k)
                k_closest = None
                msg = utils.build_FIND_NODE_msg(ID, self.node)
                try:
                    k_closest = self.RPC(msg, (n[1][0], n[1][2]))
                except:
                    # What to do if the RPC doesn't work
                    pass

                enquired.append(n)


                for t in k_closest:
                    if not t in enquired and not t in to_query:
                        pending.append(t)

            to_query.clear()

            if pending == []:
                break


            c = heapq.nsmallest(1, pending)
            if c[0] <= closest_node[0]:
                closest_node = c
                for _ in range(self.node.alpha):
                    try:
                        to_query.append(heapq.heappop(pending))
                    except:
                        break
            else:
                for _ in range(self.node.k):
                    try:
                        to_query.append(heapq.heappop(pending))
                    except:
                        break

        return heapq.nsmallest(self.node.k, enquired)




if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=8000)
    parser.add_argument('-i', '--id', type=int, default=1)

    args = parser.parse_args()

    ID = args.id
    node = Node(ID, '127.0.0.1', args.port, B=3, k=2)
    peer = Peer(node)
    peer.serve()
