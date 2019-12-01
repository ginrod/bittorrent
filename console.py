import client
import peer_wire_protocol


if __name__ == "__main__":

    clients = {}
    trackers = []

    while True:
        command = input(prompt=">>>").split()

        if command[0] == "client":
            id = command[1]
            ip = command[2]
            port = int(command[3])
            clients[id] = client.Client(ip, port)

        if command[0] == "share":
            c = clients[command[1]]
            path = 