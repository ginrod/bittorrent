def generate(address_space):
    nodes = []
    c = 2 ** address_space
    for i in range(c):
        n = Node(i, '127.0.0.1', 8080)
        n.route_table = [[] for j in range(address_space)]
        nodes.append(n)


    for current_node in nodes:
        for target_node in nodes:

            distance = current_node.ID ^ target_node.ID
            # print('current node: ',current_node)
            # print('target_node:   ', target_node)
            # print('distance: ', distance)


            if distance:
                rt_pos = int(math.log2(distance))
                # print('rt_pos: ', rt_pos)
                current_node.route_table[rt_pos].append(target_node)

            print('\n')

    return nodes


def xor_table(address_space):
    t = []
    for i in range(address_space):
        t.append([])
        for j in range(address_space):
            t[i].append(i ^ j)

    for r in t:
        print(r)