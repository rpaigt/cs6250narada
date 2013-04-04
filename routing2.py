#!/usr/bin/python
import gevent
import networkx as nx
import datetime
import json
import signal
from gevent import socket
from gevent.server import StreamServer
import argparse


MAX_DELAY = 9999
port = 30000
g = nx.Graph()

#parse command line arguments
debug = False
#parse some command line arguments
parser = argparse.ArgumentParser(description='Start to listen and send refresh messsages')
parser.add_argument('-d', '--debug', action='store_true', help='enable debugging output')
args = parser.parse_args()
if args.debug: 
    debug = True
    print("Debugging output enabled.")




with open('ipaddresses.txt') as f:
    ip_node_mapping = f.readlines()
    
with open('neighbours.txt') as f:
	neighbours = f.readlines()
	

ip_address_dict = {}
ip_node_mapping = [ip_node.strip().split(',') for ip_node in ip_node_mapping]
if debug: print ("got ip_node_mapping as {}".format(ip_node_mapping))


this_node = ip_node_mapping[0][0]	# First entry in the ipaddress file is the host node and ip pair

this_ip = ip_node_mapping[0][1]
serverip = this_ip

g.add_node(this_node)



for node, ip in ip_node_mapping:
	ip_address_dict[node] = ip


neighbour_list = [n.strip() for n in neighbours]
if debug: print ("got neighbours as {}".format(neighbour_list))

disconnected_neighbours = {}

def send_data(node, data):#sends data to node
	ip_address = ip_address_dict[node]

	client = socket.socket()
	try:
		client.connect((ip_address, port))

		sent_bytes = client.send(data)
		gevent.sleep(0)
		client.close()
		return sent_bytes
	except:
		if debug: "sending data to {}, {} failed".format(node, data)
		return -1

def send_to_neighbours(data, origin):#propagates to all neighbours except origin
	for node in neighbour_list:
		if node == this_node or node == origin: continue
		gevent.spawn(send_data, node, data)
		gevent.sleep(0)
		

def ping_node(node, update=True):#returns delay from self to node@ip_address:port
	ip_address = ip_address_dict[node]

	tries = 0
	delay = 0
	MAX_TRIES = 2

	while tries < MAX_TRIES:
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
			if tries == MAX_TRIES:
				delay = MAX_DELAY

	if debug: 
		print("attempted to ping node {} at {}:{}".format(node, ip_address,port))
		print("pinged and measured a delay of {}".format(delay))

	if update: ## graph needs to be updated even if the ping time is MAX_DELAY since that indicates a connection being lost.		
		if delay != MAX_DELAY:
			if debug:
				print("adding edge {}--{}-->{} to graph".format(this_node, delay, node))
			g.add_node(node)
			g.add_edge(this_node, node, weight=delay)

			if node in disconnected_neighbours: disconnected_neighbours.pop(node, None)
		elif delay == MAX_DELAY:
			if node in g[this_node]:
				g.remove_edge(this_node, node)
			disconnected_neighbours[this_node] = 1

		

	return delay


## update_data = [neighbour, neighbourip, [node, nodeip, delay], ... ]
def handle_update(update_data):
	if debug: print("got update data of {}".format(update_data))
	if len(update_data) >= 2:
		incoming_node = update_data[0]
		incoming_node_ip = update_data[1]

		#if it's an entirely new node
		if not incoming_node in ip_address_dict.keys():
			ip_address_dict[incoming_node] = incoming_node_ip

		#if it's a known node that's requesting to be neighbour
		if not incoming_node in neighbour_list:
			neighbour_list.append(incoming_node)

		if not g[this_node].has_key(incoming_node):
			ping_node(incoming_node)

		if incoming_node in disconnected_neighbours:
			disconnected_neighbours.pop(incoming_node, None)


		if len(update_data) > 2:
			handle_route_vector(incoming_node, update_data[2:])

def handle_route_vector(incoming_node, route_vector):
	previous_node = incoming_node

	for (node, ip_address, delay) in route_vector:
		if not node in ip_address_dict.keys():
			ip_address_dict[node] = ip_address


		if delay != MAX_DELAY:
			g.add_node(node)
			g.add_edge(previous_node, node, weight=delay)
		else:
			if node in g[previous_node]:
				g.remove_edge(previous_node, node)

		previous_node = node

def propagate_update(update_data):

	if len(update_data) >= 2:
		incoming_node = update_data[0]
		incoming_node_ip = update_data[1]

	data = [this_node, this_ip, [incoming_node, incoming_node_ip, g[this_node][incoming_node]['weight']]]
	
	for vector in update_data[2:]:
		data.append(vector)
	data = json.dumps(data)
	data = "UPDATE\n" + data

	send_to_neighbours(data, origin=incoming_node)

def handle_connection(socket, address):

	data = socket.recv(1024)
	data = data.split('\n')

	print("new incoming {} connection from {}".format(data[0],address))
	if data[0] == 'ECHO':
		socket.send(data[0])
		socket.close()

	elif data[0] == 'UPDATE':
		data = json.loads(data[1])

		handle_update(data)
		propagate_update(data)

		socket.close()

	elif data[0] == 'DATA':
		print data[1:]
		socket.close();

	elif data[0] == 'STATUS':
		status += 'Node: ' + this_node + '\n'
		status += 'Connected nodes: ' + str(g.nodes()) + '\n'

		for a,b in g.edges():
			status += str(a) + ' ' + str(b) + ' ' + str(g[a][b]['weight']) + '\n'

		socket.send(status)
		socket.close()

	else:
		print 'UNRECOG: '
		print data


#this function pings each of its neighbours
def populate_neighbour_latencies():
	workers = []

	if debug: print "in schedule and neighbour_list is {}".format(neighbour_list) 
	for node in neighbour_list:
		#schedule run ping_node(node)
		workers.append(gevent.spawn(ping_node, node))
	#wait until all the workers are done with running the scheduled ping_node()
	gevent.joinall(workers)

def update_graph():
	pass

#call func at every delay seconds
def schedule(delay, func, *args, **kw_args):
    gevent.spawn_later(0, func, *args, **kw_args)
    gevent.spawn_later(delay, schedule, delay, func, *args, **kw_args)

def propagate_neighbour_latencies():
	neighbours = g[this_node]
	if debug: print("attempting propagating my list of latencies: {}".format(neighbours))

	for nodeS in neighbours.keys():
		weightS = neighbours[nodeS]['weight']
		for nodeD in neighbours.keys():
			weightD = neighbours[nodeD]['weight']

			if nodeS == nodeD: continue


			data = [this_node, this_ip, [nodeD, ip_address_dict[nodeD], weightD]]
			data = 'UPDATE\n' + json.dumps(data)

			if debug: print("going to update {} with {}".format(nodeS, data))
			gevent.spawn(send_data, nodeS, data)

		for nodeD in disconnected_neighbours:

			data = [this_node, this_ip, [node, ip_address_dict[nodeD], MAX_DELAY]]
			data = 'UPDATE\n' + json.dumps(data)

			if debug: print("going to update disconnected nodes {} with {}".format(nodeD, data))
			
			gevent.spawn(send_data, nodeS, data)


def main():
    server = StreamServer((serverip, port), handle_connection)
    print 'Starting server on ip address {} and port: '.format(serverip) + str(port)

    gevent.signal(signal.SIGTERM, server.stop)
    gevent.signal(signal.SIGQUIT, server.stop)
    gevent.signal(signal.SIGINT, server.stop)

    server.start()

    #Ping neighbours regularly to check if up 
    schedule(5, populate_neighbour_latencies)


    #send update messages every 10 seconds
    schedule(10, propagate_neighbour_latencies)
	

    server.serve_forever()

if __name__ == "__main__":
	main()
