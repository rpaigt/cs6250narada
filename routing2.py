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

g = nx.Graph()

routes = {}
ip_address_dict = { 'B' : '192.168.1.119' }
neighbour_list = ['B']
#latencies = {}
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

	client = socket.socket()
	client.settimeout(1)
	tries = 0
	delay = 0
	max_tries = 2

	while tries < max_tries:
		try:
			client.connect((ip_address, port))

			start = datetime.datetime.now()
			client.send('ECHO\n')
			client.recv(1024)
			end = datetime.datetime.now()
			delay = (((end - start) / 2).microseconds) / 1000.0

		except:
			tries += 1
			if tries == max_tries:
				delay = 9999

	if update:
		g.add_node(node)
		g.add_edge(this_node, node, weight = delay)

	# if update:
	# 	if not latencies.has_keys(this_node):
	# 		latencies[this_node] = {}

	# 	latencies[this_node][node] = delay


	return delay


## update_data = [neighbour, neighbourip, (node, nodeip, delay), ... ]
def handle_update(update_data):

	update_data = json.loads(update_data)

	lock.acquire()

	if len(update_data) >= 2:
		incoming_node = update_data[0]
		incoming_node_ip = update_data[1]

		if not incoming_node in ip_address_dict.keys():
			ip_address_dict[incoming_node] = incoming_node_ip

		if not incoming_node in neighbour_list:
			neighbour_list.append(incoming_node)

		#if not incoming_node in latencies.keys():
		#	ping_node(incoming_node)

		if not g[this_node].has_key(incoming_node):
			ping_node(incoming_node)


		if len(update_data) > 2:
			for route_vector in update_data[2:]:
				handle_route_vector(incoming_node, route_vector)

	lock.release()

def handle_route_vector(incoming_node, route_vector):
	#cost = latencies[this_node].get(incoming_node, 9999)
	#cost = g[this_node][incoming_node]['weight']
	
	previous_node = incoming_node

	for (node, ip_address, delay) in route_vector:
		if not node in ip_address_dict.keys():
			ip_address_dict[node] = ip_address

		#cost += delay
		#if cost < latencies.get(node, 9999):
		#	latencies[node] = cost

		g.add_node(node)
		g.add_edge(previous_node, node, weight = delay)

		previous_node = node


def handle_connection(socket, address):

	data = socket.recv(1024)
	data = data.split('\n')

	if data[0] == 'ECHO':
		socket.send(data[0])
		socket.close()

	elif data[0] == 'UPDATE':
		handle_update(data[1:])

	elif data[0] == 'DATA':
		print data[1:]

	else:
		pass

def populate_latencies():
	workers = []
	for node in neighbour_list:
		workers.append(gevent.spawn(ping_node, node))
	gevent.joinall(workers)

def build_initial_graph():
	g.add_node(this_node)
	for neighbour in neighbour_list:
		g.add_node(neighbour)

	for node, latency in latencies.items():
		g.add_edge(this_node, node, weight = latencies[this_node][node])


def update_graph():
	pass

populate_latencies()
build_initial_graph()


server = StreamServer(('0.0.0.0', port), handle_connection)
print 'Starting server on port: ' + str(port)
server.serve_forever()