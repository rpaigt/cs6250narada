#!/usr/bin/python
import gevent
import networkx as nx
import datetime
import json
import signal
from gevent import socket
from gevent.server import StreamServer
import argparse

class routing:
	def __init__(self):
		self.MAX_DELAY = 9999

		self.serverip = '0.0.0.0'
		self.port = 30000


		self.g = nx.Graph()

		#parse command line arguments
		self.debug = False
		#parse some command line arguments
		parser = argparse.ArgumentParser(description='Start to listen and send refresh messsages')
		parser.add_argument('-d', '--debug', action='store_true', help='enable debugging output')
		args = parser.parse_args()
		if args.debug: 
			self.debug = True
			print("Debugging output enabled.")




		with open('ipaddresses.txt') as f:
			self.ip_node_mapping = f.readlines()
			
		with open('neighbours.txt') as f:
			self.neighbours = f.readlines()
			

		self.ip_address_dict = {}
		self.ip_node_mapping = [ip_node.strip().split(',') for ip_node in self.ip_node_mapping]
		if self.debug: print ("got ip_node_mapping as {}".format(self.ip_node_mapping))


		self.this_node = self.ip_node_mapping[0][0]	# First entry in the ipaddress file is the host node and ip pair
		self.this_ip = self.ip_node_mapping[0][1]

		self.g.add_node(self.this_node) ## g[this_node] is setup.



		for node, ip in self.ip_node_mapping:
			self.ip_address_dict[node] = ip


		neighbour_list = [n.strip() for n in self.neighbours]
		if self.debug: print ("got neighbours as {}".format(neighbour_list))

		self.disconnected_neighbours = {}
		self.update_dict = {}#stores last_time_node_was_updated as value
		self.utility_dict = {}#stores utility of node

	def send_data(self,node, data):#sends data to node
		ip_address = self.ip_address_dict[node]

		client = socket.socket()
		try:
			client.connect((ip_address, self.port))

			sent_bytes = client.send(data)
			gevent.sleep(0)
			client.close()
			return sent_bytes
		except:
			if self.debug: "sending data to {}, {} failed".format(node, data)
			return -1

	def send_to_neighbours(self,data, origin):#propagates to all neighbours except origin
		for node in neighbour_list:
			if node == self.this_node or node == origin: continue
			gevent.spawn(send_data, node, data)
			gevent.sleep(0)
			

	def ping_node(self,node, update=True):#returns delay from self to node@ip_address:port
		ip_address = self.ip_address_dict[node]

		tries = 0
		delay = 0
		MAX_TRIES = 2

		while tries < MAX_TRIES:
			try:
				client = socket.socket()
				client.settimeout(5)
				client.connect((ip_address, self.port))

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
					delay = self.MAX_DELAY

		if self.debug: 
			print("attempted to ping node {} at {}:{}".format(node, ip_address,self.port))
			print("pinged and measured a delay of {}".format(delay))

		if update: ## graph needs to be updated even if the ping time is MAX_DELAY since that indicates a connection being lost.		
			if delay != self.MAX_DELAY:
				if self.debug:
					print("adding edge {}--{}-->{} to graph".format(self.this_node, delay, node))
				self.g.add_node(node)
				self.g.add_edge(self.this_node, node, weight=delay)

				if node in self.disconnected_neighbours: self.disconnected_neighbours.pop(node, None)
			elif delay == self.MAX_DELAY:
				if node in g[self.this_node]:
					self.g.remove_edge(self.this_node, node)
				self.disconnected_neighbours[self.this_node] = 1

			

		return delay


	## update_data = [neighbour, neighbourip, [node, nodeip, delay], ... ]
	def handle_update(self,update_data):
		if self.debug: print("got update data of {}".format(update_data))
		if len(update_data) >= 2:
			incoming_node = update_data[0]
			incoming_node_ip = update_data[1]

			#if it's an entirely new node
			if not incoming_node in self.ip_address_dict.keys():
				self.ip_address_dict[incoming_node] = incoming_node_ip

			#if it's a known node that's requesting to be neighbour
			if not incoming_node in neighbour_list:
				neighbour_list.append(incoming_node)

			if not g[self.this_node].has_key(incoming_node):
				ping_node(incoming_node)

			if incoming_node in self.disconnected_neighbours:
				self.disconnected_neighbours.pop(incoming_node, None)


			if len(update_data) > 2:
				handle_route_vector(incoming_node, update_data[2:])

	def handle_route_vector(self,incoming_node, route_vector):
		previous_node = incoming_node

		for (node, ip_address, delay) in route_vector:
			if not node in self.ip_address_dict.keys():
				self.ip_address_dict[node] = ip_address


			if delay != self.MAX_DELAY:
				self.g.add_node(node)
				self.g.add_edge(previous_node, node, weight=delay)
			else:
				if node in g[previous_node]:
					self.g.remove_edge(previous_node, node)

			previous_node = node

	def propagate_update(self,update_data):

		if len(update_data) >= 2:
			incoming_node = update_data[0]
			incoming_node_ip = update_data[1]

		data = [self.this_node, self.this_ip, [incoming_node, incoming_node_ip, g[self.this_node][incoming_node]['weight']]]
		
		for vector in update_data[2:]:
			data.append(vector)
		data = json.dumps(data)
		data = "UPDATE\n" + data

		send_to_neighbours(data, origin=incoming_node)

	def handle_connection(self,socket, address):

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
			status += 'Node: ' + self.this_node + '\n'
			status += 'Connected nodes: ' + str(self.g.nodes()) + '\n'

			for a,b in self.g.edges():
				status += str(a) + ' ' + str(b) + ' ' + str(g[a][b]['weight']) + '\n'

			socket.send(status)
			socket.close()

		else:
			print 'UNRECOG: '
			print data


	#this function pings each of its neighbours
	def populate_neighbour_latencies(self,only_ping_dead=False):
		workers = []

		if self.debug and not only_ping_dead:
			print "in schedule and neighbour_list is {}".format(neighbour_list) 

		#schedule run ping_node(node)
		for node in neighbour_list:

			if only_ping_dead:
				if node not in g[self.this_node]:
					if self.debug: print "Pinging dead neighbour {}".format(node) 
					workers.append(gevent.spawn(ping_node, node))
			else:
				workers.append(gevent.spawn(ping_node, node))
		#wait until all the workers are done with running the scheduled ping_node()
		gevent.joinall(workers)

	def update_graph(self):
		pass

	#call func at every delay seconds
	def schedule(self,delay, func, *args, **kw_args):
		gevent.spawn_later(0, func, *args, **kw_args)
		gevent.spawn_later(delay, schedule, delay, func, *args, **kw_args)



	def propagate_neighbour_latencies(self):
		neighbours = g[self.this_node]
		if self.debug: print("attempting propagating my list of latencies: {}".format(neighbours))

		for nodeS in neighbours.keys():
			weightS = neighbours[nodeS]['weight']
			for nodeD in neighbours.keys():
				weightD = neighbours[nodeD]['weight']

				if nodeS == nodeD: continue


				data = [self.this_node, self.this_ip, [nodeD, self.ip_address_dict[nodeD], weightD]]
				data = 'UPDATE\n' + json.dumps(data)

				if self.debug: print("going to update {} with {}".format(nodeS, data))
				gevent.spawn(send_data, nodeS, data)

			for nodeD in self.disconnected_neighbours:

				data = [self.this_node, self.this_ip, [node, self.ip_address_dict[nodeD], self.MAX_DELAY]]
				data = 'UPDATE\n' + json.dumps(data)

				if self.debug: print("going to update disconnected nodes {} with {}".format(nodeD, data))
				
				gevent.spawn(send_data, nodeS, data)

	def populate_and_propogate(self):
		populate_neighbour_latencies()
		propagate_neighbour_latencies()
		generate_spanning_tree()

	def generate_spanning_tree(self):
		mst = nx.minimum_spanning_tree(g)
		

	def get_curtime(self):#stub, needs to be implemented
		pass
		#return the current time, to compare with those in update_dict

	def sleep_repair(self):#stub, sleep for a while, use gevent to call it after k time or just call mesh_repair in a separate thread
		pass


	def get_node_utility(self,trynode):
		utility = 0
		path = nx.all_pairs_shortest_path(g)
		for node in fwd_table.keys():
			if (node == self.this_node):
				pass
			else:
				oldlat = path[self.this_node][node]
				newlat = path[self.this_node][trynode] + path[trynode][node]
				if(newlat < oldlat):
					utility = utility + ((oldlat - newlat) / oldlat)

		return utility

	def get_mutual_cost(self,trynode):
		count1 = 0
		count2 = 0
		f2 = get_fwdtable(trynode)
		f1 = fwd_table

		for i in f1.keys():
			if f1[keys] == trynode:
				count1 = count1 + 1

		for j in f2.keys():
			if f2[keys] == self.this_node:
				count2 = count2+1

		return max(count1, count2)

	def mesh_repair(self):#called every T intervals
		T = 1000#timeout, now need to repair these nodes since they did nto update for T

		while(True): ## We can just call mesh repair at regular intervals. Does this need to be while(true)?
			curtime = get_curtime()
			update_list = []

			for e in self.update_dict.keys():
				if (self.update_dict[e] - curtime) >= T:
					update_list.append(e,self.update_dict[e])

			update_list = sorted(update_list, key=lambda e: e[1])

			while(len(update_list) and (update_list[0] >= T)):
				temp = update_list.pop(0)
				delay = ping_node(temp, update=False)

				if(delay != self.MAX_DELAY):
					self.update_dict[temp] = 0

					if(nx.path.bidirectional_dijkstra(g, self.this_node, temp)):
						self.g.add_node(temp)

					self.g.add_edge(self.this_node, temp, weight=delay)

			if len(update_list):
				prob = len(update_list) / len(self.update_dict)

				if random.random() >= (1-prob):
					temp = update_list.pop(0)
					delay = ping_node(temp, update=False)

					if(delay!=self.MAX_DELAY):
						self.update_dict[temp] = 0
						if nx.path.bidirectional_dijkstra(g, self.this_node, temp):
							self.g.add_node(temp)
						self.g.add_edge(self.this_node, temp, weight=delay)

			sleep_repair(time)	

	def optimiseall(self):#called every T seconds
		mesh_repair()

		for node in self.update_dict.keys():
			if not self.utility_dict.has_key(node):
				self.utility_dict[node] = [0,0]
			
			utility = get_node_utility(node)
			
			if self.utility_dict(node)[0] < utility:
				self.utility_dict(node)[0] = utility

		for node in self.update_dict.keys():
			cost = get_mutual_cost(node)
			
			if self.utility_dict(node)[1] < cost:
				self.utility_dict(node)[1] = cost


	def main(self):
		server = StreamServer((self.serverip, self.port), handle_connection)
		print 'Starting server on ip address {} and port: '.format(self.serverip) + str(self.port)

		gevent.signal(signal.SIGTERM, server.stop)
		gevent.signal(signal.SIGQUIT, server.stop)
		gevent.signal(signal.SIGINT, server.stop)

		server.start()

		#send update messages every 10 seconds
		schedule(60, populate_and_propogate)
		schedule(10, populate_neighbour_latencies, only_ping_dead=True)
		

		server.serve_forever()

if __name__ == "__main__":
	temp=routing()
	temp.main()
