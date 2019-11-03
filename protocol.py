import heapq
import math
import json
import utils

class Node:

    def __init__(self, ID, ip, port, alpha=3, k=20, B=160):
        self.ID = ID
        self.ip = ip
        self.port = port

        self.alpha = alpha
        self.k = k
        self.B = B

        self.storage = f'storage{ID}.json'


        self.route_table = [[] for _ in range(B)]


    def __repr__(self):
        return f'({self.ID}, {self.ip}, {self.port})'
        # return str((self.ID, self.ip, self.port))

    def __iter__(self):
        return iter([self.ID, self.ip, self.port])

    def print_routing_table(self):
        def format(kBucket):
            elements = []
            for n in kBucket:
                elements.append(n[0])
            return elements

        r = ''
        for i in range(len(self.route_table)):
            r += '[' + str(2**i) + ',' + str(2**(i + 1)) + '): ' + str(format(self.route_table[i])) + '\n'
        print(r)

    def get_all_nodes(self, ID):
        nodes = []
        for k_bucket in self.route_table:
            for n in k_bucket:
                nodes.append((n.ID ^ ID, n))
        return nodes

    def find_kBucket(self, senderID):

        d = self.distance_to((senderID, ))

        i = int(math.log2(d)) if d != 0 else 0

        return (self.route_table[i], i)

    def distance_to(self, other):
        return self.ID ^ other[0]

    def FIND_VALUE(self, ID):
        
        data = utils.load_json(self.storage)
        if str(ID) in data:
            return (True, data[str(ID)])
        return (False, self.FIND_NODE(ID))

    def STORE(self, key, value):
        print(f'*******Value: {value}')
        key = str(key)
        data = utils.load_json(self.storage)
        data[key] = value
        print(f'data to store: {data}')
        utils.dump_json(data, self.storage)


    def PING(self):
        return True

    def FIND_NODE(self, ID):
        return self.get_n_closest(ID, self.k)


    def get_n_closest(self, ID, n):
        k_bucket, i = self.find_kBucket(ID)
        heap = []
        n_closest = [ (ID ^ n[0], n) for n in heapq.nsmallest(n, k_bucket)]
        inf, sup = i-1,i+1
        while len(n_closest) < n and (inf >=0 or sup < self.B):
            if inf >= 0:
                heap += [(ID ^ n[0], n) for n in self.route_table[inf]]
                inf -= 1
            if sup < self.B:
                heap += [(ID ^ n[0], n) for n in self.route_table[sup]]
                sup += 1

            if len(n_closest) + len(heap) >= n:
                for _ in range(n - len(n_closest)):
                    n_closest.append(heapq.heappop(heap))

        return n_closest