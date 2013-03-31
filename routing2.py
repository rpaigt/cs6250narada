import gevent
import networkx as nx
import datetime
import signal
import json
from gevent import socket
from gevent.server import StreamServer
from gevent.coros import BoundedSemaphore

port = 30000
this_node = 'A'
this_ip = '192.168.1.51'

g = nx.Graph()

routes = {}
ip_address_dict = { 'B' : '192.168.1.59' }
neighbour_list = ['B']
best_routes = {}

lock = BoundedSemaphore(1)

def send_data(node, data):
	ip_address = ip_address_dict[node]
	client = socket.socket()
	client.connect((ip_address, port))
	client.send(data)
	gevent.sleep(0)
	client.close()

def send_to_neighbours(data):
	for node in neighbour_list:
		gevent.spawn(send_data, node, data)
		gevent.sleep(0)
		

def ping_node(node, update=True):
	ip_address = ip_address_dict[node]
	
	tries = 0
	delay = 0
	max_tries = 2

	while tries < max_tries:
		try:
			print 'Pinging: ', ip_address, port, tries

			client = socket.socket()
			client.settimeout(5)
			client.connect((ip_address, port))

			start = datetime.datetime.now()
			client.send('ECHO\n')
			client.recv(1024)
			end = datetime.datetime.now()

			delay = (((end - start) / 2).microseconds) / 1000.0
			break
			
		except:
			tries += 1
			if tries == max_tries:
				delay = 9999

	if update:
		g.add_node(node)
		g.add_edge(this_node, node, weight = delay)

	return delay


## update_data = [neighbour, neighbourip, [node, nodeip, delay], ... ]
def handle_update(update_data):
	lock.acquire()

	if len(update_data) >= 2:
		incoming_node = update_data[0]
		incoming_node_ip = update_data[1]

		if not incoming_node in ip_address_dict.keys():
			ip_address_dict[incoming_node] = incoming_node_ip

		if not incoming_node in neighbour_list:
			neighbour_list.append(incoming_node)

		if not g[this_node].has_key(incoming_node):
			ping_node(incoming_node)


		if len(update_data) > 2:
			for route_vector in update_data[2:]:
				handle_route_vector(incoming_node, route_vector)

	lock.release()

def handle_route_vector(incoming_node, route_vector):
	previous_node = incoming_node

	for (node, ip_address, delay) in route_vector:
		if not node in ip_address_dict.keys():
			ip_address_dict[node] = ip_address

		g.add_node(node)
		g.add_edge(previous_node, node, weight = delay)

		previous_node = node

def propagate_update(update_data):
	if len(update_data) >= 2:
		incoming_node = update_data[0]
		incoming_node_ip = update_data[1]

	data = [this_node, this_ip, [incoming_node, incoming_node_ip, g[this_node][incoming_node]['weight']]]
	
	for vector in update_data[2:]:
		data.append(vector)
	data = json.dumps(data)
	data = 'UPDATE\n' + data

	send_to_neighbours(data)

def handle_connection(socket, address):

	data = socket.recv(1024)
	data = data.split('\n')

	if data[0] == 'ECHO':
		socket.send(data[0])
		socket.close()

	elif data[0] == 'UPDATE':
		data = json.loads(data[1:])

		handle_update(data)
		propagate_update(data)

	elif data[0] == 'DATA':
		print data[1:]

	else:
		pass

def populate_latencies():
	workers = []
	for node in neighbour_list:
		print 'node: ' + node
		workers.append(gevent.spawn(ping_node, node))
	gevent.joinall(workers)

def update_graph():
	pass

populate_latencies()
print g.nodes()
for (a,b) in g.edges():
	print a,b, g[a][b]['weight']


server = StreamServer(('0.0.0.0', port), handle_connection)
print 'Starting server on port: ' + str(port)
server.serve_forever()
