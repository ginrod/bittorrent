import heapq
import math
import json
import utils
import datetime
import threading

class Node:

    def __init__(self, ID, ip, port, alpha=3, k=20, B=160):
        self.ID = ID
        self.ip = ip
        self.port = port

        self.alpha = alpha
        self.k = k
        self.B = B

        # utils.create_dirs('files/storage')
        self.storage = 'files/storage/storage.json'

        self.route_table = [[] for _ in range(B)]
        self.store_lock = threading.Lock()
        self.database = utils.load_json(self.storage)
        threading._start_new_thread(self.persist_database, ())

    def persist_database(self, time_unit=5):
        import time
        while True:
            self.store_lock.acquire()
            utils.dump_json(self.database, self.storage)
            try: self.store_lock.release()
            except: pass
            time.sleep(time_unit)

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
            r += '[' + str(2**i) + ',' + str(2**(i + 1)) + \
                '): ' + str(format(self.route_table[i])) + '\n'
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
        # return self.ID ^ other[0]
        return self.ID ^ int(other[0])

    def FIND_VALUE(self, ID):
        # self.store_lock.acquire()
        if str(ID) in self.database:
            try:
                self.store_lock.release()
            except: pass
            return (True, self.database[str(ID)], None)
        # self.store_lock.release()
        return (False, self.FIND_NODE(ID), None)

    def STORE(self, key, value, publisher, sender, value_type='json', real_value=None, to_update=False):
        # print(f'STORING key:{key}, value:{value}')
        key = str(key)

        # database = utils.load_json(self.storage)
        data = {'value': value }

        self.store_lock.acquire()
        if key in self.database:
            data = self.database[key]
            # If the value to save is a file parm value is the path and real_value the file bytes array
            # if real_value: utils.save_file(value, real_value)

            data['value'] = value
            now = datetime.datetime.now()
            if sender == publisher:
                data['timeo'] = now

            data['timer'] = now
        else:
            # If the value to save is a file parm value is the path and real_value the file bytes array
            if real_value: utils.save_file(value, real_value)
            data['publisher'] = publisher
            data['timeo'] = data['timer'] = datetime.datetime.now()
            data['value_type'] = value_type
            data['to_update'] = to_update

        self.database[key] = data
        try:
            self.store_lock.release()
        except: pass

    def PING(self):
        return True

    def FIND_NODE(self, ID):
        return self.get_n_closest(ID, self.k)

    def get_n_closest(self, ID, n):
        k_bucket, i = self.find_kBucket(ID)
        heap = []
        n_closest = [(ID ^ n[0], n) for n in heapq.nsmallest(n, k_bucket)]
        inf, sup = i-1, i+1
        while len(n_closest) < n and (inf >= 0 or sup < self.B):
            if inf >= 0:
                heap += [(ID ^ n[0], n) for n in self.route_table[inf]]
                inf -= 1
            if sup < self.B:
                heap += [(ID ^ n[0], n) for n in self.route_table[sup]]
                sup += 1

            if len(n_closest) + len(heap) >= n:
                for _ in range(n - len(n_closest)):
                    n_closest.append(heapq.heappop(heap))

        if len(n_closest) < n:
            top = min(n - len(n_closest), len(heap))
            for _ in range(top):
                n_closest.append(heapq.heappop(heap))

        return n_closest

    def asTuple(self):
        return tuple(iter(self))

    def asList(self):
        return list(iter(self))

    @staticmethod
    def Equals(n1, n2):
        n1, n2 = list(iter(n1)), list(iter(n2))
        return n1[0] == n2[0] and n1[1] == n2[1] and n1[2] == n2[2]