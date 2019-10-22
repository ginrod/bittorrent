import heapq
import math

class Node:

    def __init__(self, ID, ip, port, alpha=3, k=20, B=160):
        self.ID = ID
        self.ip = ip
        self.port = port

        self.alpha = alpha
        self.k = k

        self.route_table = [[] for _ in range(B)]

    def __repr__(self):
        # return f'({self.ID}, {self.ip}, {self.port})'
        return str((self.ID, self.ip, self.port))

    def get_all_nodes(self, ID):
        nodes = []
        for k_bucket in self.route_table:
            for n in k_bucket:
                nodes.append((n.ID ^ ID, n))
        return nodes

    def find_kBucket(self, senderID):
        d = self.distance_to((senderID, ))
        i = int(math.log2(d))

        return self.route_table[i]

    def distance_to(self, other):
        return self.ID ^ other[0]

    def FIND_VALUE(self, ID):
        pass

    def STORE(self, key, value):
        pass

    def PING(self):
        return True

    def FIND_NODE(self, ID):
        nodes = self.get_all_nodes(ID)
        k_closest = heapq.nsmallest(self.k, nodes)
        return k_closest