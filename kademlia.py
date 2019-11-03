import heapq
import math
import socket
import json
import uuid
import datetime



class Node:

    def __init__(self, ID, ip, port, alpha=3, k=20, B=160):
        self.ID = ID
        self.ip = ip
        self.port = port

        self.alpha = alpha
        self.k = k

        self.route_table = [[] for _ in range(B)]

    def __repr__(self):
        return str(self.ID)


    def get_all_nodes(self, ID):
        nodes = []
        for k_bucket in self.route_table:
            for n in k_bucket:
                nodes.append((n.ID ^ ID, n))
        return nodes


    def FIND_NODE(self, ID):
        nodes = self.get_all_nodes(ID)
        k_closest = heapq.nsmallest(self.k, nodes)
        return k_closest


    def lookup(self, ID):
        #Insert all nodes of the k-bucket list of start on a list
        nodes = self.get_all_nodes(ID)

        #Select the alpha closest nodes to ID
        to_query = heapq.nsmallest(self.alpha, nodes)

        pending = []
        heapq.heapify(pending)

        enquired = []

        closest_node = heapq.nsmallest(1, to_query)

        while True:

            for n in to_query:

                k_closest = n[1].FIND_NODE(ID, self.k)

                enquired.append(n)


                for t in k_closest:
                    if not t in enquired and not t in to_query:
                        pending.append(t)

            to_query.clear()

            if pending == []:
                break

            c = heapq.nsmallest(1, pending)
            if c[0] <= closest_node[0]:
                for _ in range(self.alpha):
                    try:
                        to_query.append(heapq.heappop(pending))
                    except:
                        break
            else:
                for _ in range(self.k):
                    try:
                        to_query.append(heapq.heappop(pending))
                    except:
                        break

        return heapq.nsmallest(self.k, enquired)
