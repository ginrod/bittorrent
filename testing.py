import socket
import json



if __name__ == "__main__":

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('localhost', 5000))

    s.settimeout(6)

    import io

    reader = open('input', 'r')
    commands = reader.readlines()

    # while True:
    for command in commands:
        input_msg = command.split()
        # input_msg = input_msg[0:-1] if input_msg[-1] == '\n' else input_msg
        # input_msg = input("[PORT] [OPERATION] [OP_PORT] [METHOD] [ARGS...]\n").split()

        addr = 'localhost', int(input_msg[0])
        data = {'operation': input_msg[1], 'method': input_msg[3], 'ip': 'localhost', 'port': int(input_msg[2])}
        for arg in input_msg[4:]:
            arg_name, arg_value = tuple(arg.split(':'))

            if arg_name in ['port', 'ID']:
                data[arg_value] = int(arg_value)
            else: data[arg_name] = arg_value

        print("data to send to " + str(addr[0])+ ":" + str(addr[1]) + "\n" + str(data))
        s.sendto(json.dumps(data).encode(), addr)

        print("Waiting for an answer from " + str(addr))
        try:
            data, addr1 = s.recvfrom(1024)
            data = json.loads(data)
        except:
            print("Timeout error")
            continue


        print("Answer from RPC executded from address " + str(addr[0]) + ":" + str(addr[1]) + "is " + str(data['result']))
    
    reader.close()


