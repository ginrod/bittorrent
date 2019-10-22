import socket
import uuid
import datetime
import json
import utils
from utils import TimeOutException
import heapq
import math
from protocol import Node

class Peer:

    def __init__(self, node):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((node.ip, node.port))
        self.node = node

    def RPC(self, msg, addr):
        key = utils.generate_random_id()
        msg['key'] = key
        msg['sender_id'] = self.node.ID
        self.socket.sendto(json.dumps(msg).encode(), addr)

        start = datetime.datetime.now()
        while (datetime.datetime.now() - start).seconds < 5:
            answer, _ = self.socket.recvfrom(1024)
            answer = json.loads(answer)

            if 'method' in answer:
                continue

            if answer['key'] == key:
                return answer['result']

        # raise Exception("The remote peer is not responding")

    def serve(self):
        while True:
            msg, addr = self.socket.recvfrom(1024)
            data = json.loads(msg)

            if 'result' in data:
                continue

            result = None

            print('ALERT')
            print(data)
            print('ALERT')

            if data['method'] == 'FIND_NODE':
                result =  self.node.FIND_NODE(data['id'])
            elif data['method'] == 'FIND_VALUE':
                result = self.node.FIND_VALUE(data['id'])
            elif data['method'] == 'PING':
                result = self.node.PING()
            elif data['method'] == 'STORE':
                result = self.node.STORE(data['storeKey'], data['storeValue'])

            if result is not None:
                answer = {'result': result, 'key': data['key']}
                self.socket.sendto(json.dumps(answer).encode(), addr)
                self.update(data['sender_id'])


    def update(self, senderID):
        # senderID, senderIp, senderPort = node
        kBucket = self.node.find_kBucket(senderID)

        if senderID in kBucket:
            kBucket.remove(senderID)
            kBucket.append(senderID)
        else:
            if len(kBucket) < self.node.k:
                kBucket.append(senderID)
            else:
                # last_recently_seen node
                _, lastNodeIp, lastNodePort = kBucket[0]
                msg = utils.build_PING_msg()

                try:
                    self.RPC(msg, (lastNodeIp, lastNodePort))
                    kBucket.append(kBucket[0])
                    kBucket.remove(kBucket[0])
                except:
                    kBucket.remove(kBucket[0])
                    kBucket.append(senderID)

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
                msg = utils.build_FIND_NODE_msg(ID)
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


def serve(peer):
    peer.serve()

def start():
    ID = 1
    node = Node(ID, '127.0.0.1', 8000, B=3)
    peer = Peer(node)

    import threading
    threading._start_new_thread(serve, (peer, ))

    while True:
        print('Peer raised at localhost:8000')
        x = input('Write input for testing\n').split(' ')

        if x[0] == 'PING':
            x[1] = int(x[1])
            ans = peer.RPC(utils.build_PING_msg(), ('localhost', x[1]))
            print(ans)

start()

# if __name__ == '__main__':
#     import argparse
#     parser = argparse.ArgumentParser()
#     parser.add_argument('-p', '--port', type=int, default=8000)
#     parser.add_argument('-i', '--id', type=int, default=1)

#     args = parser.parse_args()

#     ID = args.id
#     node = Node(ID, '127.0.0.1', args.port, B=3)
#     peer = Peer(node)

#     import threading

#     threading._start_new_thread(serve, (peer, ))

#     # while True:
#     actions = input('Write [RPC func] [args separated by spaces]\n').split(' ')

#     if actions[0] == 'PING':
#         port = int(actions[1])

#         msg = utils.build_PING_msg()
#         answer = peer.RPC(msg, ('localhost', port))
#         print('LLEGUE AKI')
#         print(answer)