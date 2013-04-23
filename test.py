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
	print("Attempted to send data to node {} at {}:{}".format(node, ip_address_dict[node],port))                                                               
	s.sendall(data)
	s.close()

def status(node):
	data = 'STATUS\n'
	send(node, data)

def data(node):
	data = 'DATA\n' + json.dumps([node, ip_address_dict[node], 'Hello World!!'])
	send(node, data)

	
