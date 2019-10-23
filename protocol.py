import heapq
import math

class Node:

    def __init__(self, ID, ip, port, alpha=3, k=20, B=160):
        self.ID = ID
        self.ip = ip
        self.port = port

        self.alpha = alpha
        self.k = k
        self.B = B

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
        i = int(math.log2(d))

        return (self.route_table[i], i)

    def distance_to(self, other):
        return self.ID ^ other[0]

    def FIND_VALUE(self, ID):
        pass

    def STORE(self, key, value):
        pass

    def PING(self):
        return True

    def FIND_NODE(self, ID):
        k_bucket, i = self.find_kBucket(ID)
        heap = []
        k_closest = [ (ID ^ n[0], n) for n in k_bucket]
        inf, sup = i-1,i+1
        while len(k_closest) < self.k and (inf >=0 or sup < self.B):
            if inf >= 0:
                heap += [(ID ^ n[0], n) for n in self.route_table[inf]]
                inf -= 1
            if sup < self.B:
                heap += [(ID ^ n[0], n) for n in self.route_table[sup]]
                sup += 1

            if len(k_closest) + len(heap) >= self.k:
                for _ in range(self.k - len(k_closest)):
                    k_closest.append(heapq.heappop(heap))

        return [n for _, n in k_closest]








