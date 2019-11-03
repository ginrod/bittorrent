import unittest
from network import Peer
from protocol import Node
from multiprocessing import Process

def make_kbucket(ids):
    r = []
    for i in ids:
        r.append((i, 'localhost', 8000 + i))
    return r
def node(ID):
    return (ID, 'localhost', 8000 + ID)


class TestFIND_NODE(unittest.TestCase):

    def test_ExactlyKinKbucket(self):
        node = Node(0,'localhost', 8000, k=2, B=3)
        node.route_table[2] = [(4, 'localhost', 8004), (6, 'localhost', 8006)]
        self.assertEqual(node.FIND_NODE(5), [(4, 'localhost', 8004), (6, 'localhost', 8006)])

    def test_LessThanKinKbucket(self):
        node = Node(0,'localhost', 8000, k=5, B=4)
        node.route_table = [
            [(1, 'localhost', 8001)],
            [(2, 'localhost', 8002), (3, 'localhost', 8003)],
            [(4, 'localhost', 8004), (6, 'localhost', 8006), (8, 'localhost', 8008)],
            [(11, 'localhost', 8011), (14, 'localhost', 8014), (13, 'localhost', 8013)]
        ]
        r = node.FIND_NODE(5)
        l = make_kbucket([2,3,4,6,8])
        for elem in r:
            self.assertIn(elem, l)

    def test_lessThanKinRoutingTable(self):
        node = Node(0,'localhost', 8000, k=5, B=4)
        node.route_table = [
            [(1, 'localhost', 8001)],
            [(2, 'localhost', 8002), (3, 'localhost', 8003)],
            [(4, 'localhost', 8004)],
            [(11, 'localhost', 8011)]
        ]
        r = node.FIND_NODE(5)
        l = make_kbucket([1,2,3,4,11])
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