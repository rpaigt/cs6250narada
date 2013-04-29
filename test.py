import socket
import json

port = 30000

ip_file = 'ipaddresses.txt'
neighbour_file = 'neighbours.txt'

with open(ip_file) as f:
    temp_ip_node_mapping = f.readlines()
            
with open(neighbour_file) as f:
    temp_neighbours = f.readlines()

ip_node_mapping = [ip_node.strip().split(',') for ip_node in temp_ip_node_mapping]

ip_address_dict = {}
for node, ip in ip_node_mapping:
    ip_address_dict[node] = ip


neighbour_list = [n.strip() for n in temp_neighbours]


def send(node, data):
    s = socket.socket()
    s.connect((ip_address_dict[node], port))
    s.sendall(data)
    print("Sent data to node {} at {}".format(node, (ip_address_dict[node],port)))
    s.close()

def status(node):
    data = 'STATUS\n'
    send(node, data)

def sendfile(sender, receiver, filename):
    print "Setting the sender's name to: {}".format(sender)
    f = open(filename, 'r')
    content = f.read()
    f.close()
    data = 'DATA\n' + json.dumps([sender, ip_address_dict[sender], filename, content])
    send(receiver, data)

    
