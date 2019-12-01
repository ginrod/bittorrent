import unittest
from network import Peer
from protocol import Node
from multiprocessing import Process
import client
import utils
import network
import threading
import time


def make_kbucket(ids):
    r = []
    for i in ids:
        r.append((i, 'localhost', 8000 + i))
    return r


def node(ID):
    return (ID, 'localhost', 8000 + ID)


class TestCheckDatabase(unittest.TestCase):

    def test_publisherFall_closerArrives_furthestDropData(self):

        peers = {}

        def start_peers(peersID):
            for ID in peersID:
                peer = Peer(Node(*node(ID), alpha=2, k=3, B=4))
                peers[ID] = peer
                threading._start_new_thread(network.start, (peer,))

        # Starting 8 peers
        start_peers([ID for ID in range(8)])

        # Doing pings to populate de routing tables
        utils.build_PINGS_input(0, 7)
        client.start('files/PINGS From 0 until 7.txt')

        # Checking k-closest
        k_closest = [(0 ^ 8, (0, 'localhost', 8000)),
                     (1 ^ 8, (1, 'localhost', 8001)), (2 ^ 8, (2, 'localhost', 8002))]

        self.assertEqual(k_closest, peers[0].lookup_node(8))
        publisher, key, value = (0, 'localhost', 8000), 8, 'test publication'
        utils.build_PUBLISH_input(publisher, key, value)
        client.start(f'files/PUBLISH ({key}, {value}) from {publisher}.txt')

        # Checking that value stores un kclosest
        self.assertIn('8', utils.load_json('storage0.json'))
        self.assertIn('8', utils.load_json('storage1.json'))
        self.assertIn('8', utils.load_json('storage2.json'))

        # Killing node 0
        peers[0].socket.close()
        start_peer(8)
        start_peer(9)

        # Doing PINGS
        utils.build_PINGS_input(1, 9)
        client.start('files/PINGS From 1 until 9.txt')

        time.sleep(2)  # sleep 2 seconds to give time to republishing

        # Checking k-closest (now 8 and 9 are closer to 8 than 2)
        k_closest = [(8 ^ 8, (8, '127.0.0.1', 8008)),
                     (9 ^ 8, (9, '127.0.0.1', 8009)), (1 ^ 8, (1, '127.0.0.1', 8001))]

        self.assertEqual(k_closest, peers[1].lookup_node(8))
        self.assertNotIn('8', utils.load_json('storage2.json'))

        self.assertIn('8', utils.load_json('storage8.json'))
        self.assertIn('8', utils.load_json('storage9.json'))
        self.assertIn('8', utils.load_json('storage1.json'))

        time.sleep(25)  # Waiting till time for the original publisher is over
        self.assertNotIn('8', utils.load_json('storage8.json'))
        self.assertNotIn('8', utils.load_json('storage9.json'))
        self.assertNotIn('8', utils.load_json('storage9.json'))


class TestFIND_NODE(unittest.TestCase):

    def test_ExactlyKinKbucket(self):
        node = Node(0, 'localhost', 8000, k=2, B=3)
        node.route_table[2] = [(4, 'localhost', 8004), (6, 'localhost', 8006)]
        self.assertEqual([n for _, n in node.FIND_NODE(
            5)], [(4, 'localhost', 8004), (6, 'localhost', 8006)])

    def test_LessThanKinKbucket(self):
        node = Node(0, 'localhost', 8000, k=5, B=4)
        node.route_table = [
            [(1, 'localhost', 8001)],
            [(2, 'localhost', 8002), (3, 'localhost', 8003)],
            [(4, 'localhost', 8004), (6, 'localhost', 8006), (8, 'localhost', 8008)],
            [(11, 'localhost', 8011), (14, 'localhost', 8014), (13, 'localhost', 8013)]
        ]
        r = [n for _, n in node.FIND_NODE(5)]
        l = make_kbucket([2, 3, 4, 6, 8])
        for elem in r:
            self.assertIn(elem, l)

    def test_lessThanKinRoutingTable(self):
        node = Node(0, 'localhost', 8000, k=5, B=4)
        node.route_table = [
            [(1, 'localhost', 8001)],
            [(2, 'localhost', 8002), (3, 'localhost', 8003)],
            [(4, 'localhost', 8004)],
            [(11, 'localhost', 8011)]
        ]
        r = [n for _, n in node.FIND_NODE(5)]
        l = make_kbucket([1, 2, 3, 4, 11])
        for elem in r:
            self.assertIn(elem, l)


class TestLookup(unittest.TestCase):

    def test_static(self):
        peers = []
        processes = []
        for i in range(8):
            peers.append(Peer(Node(i, 'localhost', 8000+i, alpha=2, k=3, B=2)))
        for p in peers:
            processes.append(Process())


if __name__ == "__main__":
    unittest.main()


TestCheckDatabase().test_publisherFall_closerArrives_furthestDropData()
