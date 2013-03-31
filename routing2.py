import gevent
import networkx as nx
import datetime
import json
import signal
from gevent import socket
from gevent.server import StreamServer


port = 30000
g = nx.Graph()


with open('ipaddresses.txt') as f:
    ip_node_mapping = f.readlines()

with open('neighbours.txt') as f:
	neighbours = f.readlines()

ip_address_dict = {}
ip_node_mapping = [ip_node.strip().split(',') for ip_node in ip_node_mapping]

this_node = ip_node_mapping[0][0]	# First entry in the ipaddress file is the host node and ip pair
this_ip = ip_node_mapping[0][1]

g.add_node(this_node)

for node, ip in ip_node_mapping:
	ip_address_dict[node] = ip


neighbour_list = [n.strip() for n in neighbours]


def send_data(node, data):
	ip_address = ip_address_dict[node]
	client = socket.socket()
	client.connect((ip_address, port))

	client.send(data)
	gevent.sleep(0)
	client.close()

def send_to_neighbours(data, origin):
	for node in neighbour_list:
		if node == this_node or node == origin: continue
		gevent.spawn(send_data, node, data, update)
		gevent.sleep(0)
		

def ping_node(node, update=True):
	ip_address = ip_address_dict[node]
	
	tries = 0
	delay = 0
	max_tries = 2

	while tries < max_tries:
		try:
			client = socket.socket()
			client.settimeout(5)
			client.connect((ip_address, port))

			start = datetime.datetime.now()
			client.send('ECHO\n')
			client.recv(1024)
			end = datetime.datetime.now()
			
			client.close()

			delay = (((end - start) / 2).microseconds) / 1000.0
			break

		except:
			tries += 1
			if tries == max_tries:
				delay = 9999

	if update:
		g.add_node(node)
		g.add_edge(this_node, node, weight=delay)

	return delay


## update_data = [neighbour, neighbourip, [node, nodeip, delay], ... ]
def handle_update(update_data):
	if len(update_data) >= 2:
		incoming_node = update_data[0]
		incoming_node_ip = update_data[1]

		print 'Handling update data: '
		print incoming_node
		print incoming_node_ip

		if not incoming_node in ip_address_dict.keys():
			ip_address_dict[incoming_node] = incoming_node_ip

		if not incoming_node in neighbour_list:
			neighbour_list.append(incoming_node)

		if not g[this_node].has_key(incoming_node):
			ping_node(incoming_node)


		if len(update_data) > 2:
			for route_vector in update_data[2:]:
				handle_route_vector(incoming_node, route_vector)

def handle_route_vector(incoming_node, route_vector):
	previous_node = incoming_node

	print 'Route vector'
	print route_vector

	for (node, ip_address, delay) in route_vector:
		if not node in ip_address_dict.keys():
			ip_address_dict[node] = ip_address

		g.add_node(node)
		g.add_edge(previous_node, node, weight=delay)

		previous_node = node

def propagate_update(update_data):

	print 'Propagate update'
	if len(update_data) >= 2:
		incoming_node = update_data[0]
		incoming_node_ip = update_data[1]

	data = [this_node, this_ip, [incoming_node, incoming_node_ip, g[this_node][incoming_node]['weight']]]
	
	for vector in update_data[2:]:
		data.append(vector)
	data = json.dumps(data)
	data = "UPDATE\n" + data

	print 'Data to send for update'
	print data

	send_to_neighbours(data, origin=incoming_node)

def handle_connection(socket, address):

	data = socket.recv(1024)
	print data
	data = data.split('\n')

	if data[0] == 'ECHO':
		print 'ECHO Request: ',
		print address

		socket.send(data[0])
		socket.close()

	elif data[0] == 'UPDATE':
		print 'UPDATE Request: ',
		data = json.loads(data[1:])
		print data


		handle_update(data)
		propagate_update(data)

		socket.close()

	elif data[0] == 'DATA':
		print data[1:]

		socket.close();

	elif data[0] == 'STATUS':
		socket.send(str(g.nodes()))
		for a,b in g.edges():
			socket.send(str(a) + str(b) + str(g[a][b]['weight']))
		socket.close()

	else:
		print 'UNRECOG: '
		print data

def populate_neighbour_latencies():
	workers = []

	for node in neighbour_list:
		workers.append(gevent.spawn(ping_node, node))
	gevent.joinall(workers)

def update_graph():
	pass

def schedule(delay, func, *args, **kw_args):
    gevent.spawn_later(0, func, *args, **kw_args)
    gevent.spawn_later(delay, schedule, delay, func, *args, **kw_args)

def propagate_neighbour_latencies():
	neighbours = g[this_node]

	for nodeS in neighbours.keys():
		weightS = neighbours[nodeS]['weight']
		for nodeD in neighbours.keys():
			weightD = neighbours[nodeD]['weight']

			if nodeS == nodeD: continue

			data = [this_node, this_ip, [nodeD, ip_address_dict[nodeD], weightD]]

			gevent.spawn(send_data, nodeS, json.dumps(data))



server = StreamServer(('0.0.0.0', port), handle_connection)
print 'Starting server on port: ' + str(port)

gevent.signal(signal.SIGTERM, server.stop)
gevent.signal(signal.SIGQUIT, server.stop)
gevent.signal(signal.SIGINT, server.stop)

server.start()

populate_neighbour_latencies()
schedule(60, propagate_neighbour_latencies)
server.serve_forever()
