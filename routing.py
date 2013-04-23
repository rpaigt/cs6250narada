#!/usr/bin/python


import gevent
import networkx as nx
import datetime
import json
import signal
from gevent import socket
from gevent.server import StreamServer
import argparse




class Routing:
    MAX_DELAY = 9999

    def __init__(self, server_ip='0.0.0.0', port=30000, ip_file='ipaddresses.txt', 
                    neighbour_file='neighbours.txt', debug=False):
        
        self.server_ip = server_ip
        self.port = port

        self.g = nx.Graph()
        self.mst = nx.Graph()

        self.debug = debug


        with open(ip_file) as f:
            temp_ip_node_mapping = f.readlines()
            
        with open(neighbour_file) as f:
            temp_neighbours = f.readlines()
            
        #self.disconnected_neighbours = {}
        self.fwd_table = {}
        self.ip_address_dict = {}


        ip_node_mapping = [ip_node.strip().split(',') for ip_node in temp_ip_node_mapping]
        if self.debug: print ("Got ip_node_mapping as {}".format(ip_node_mapping))


        self.this_node = ip_node_mapping[0][0]    # First entry in the ipaddress file is the host node and ip pair
        self.this_ip = ip_node_mapping[0][1]

        self.g.add_node(self.this_node) # self.g[self.this_node] is setup.
        self.graph_modified = True  # Set this to to True whenever we change the graph, reset when MST is generated


        for node, ip in ip_node_mapping:
            self.ip_address_dict[node] = ip


        self.neighbour_list = [n.strip() for n in temp_neighbours]
        if self.debug: print ("Got neighbours as {}".format(self.neighbour_list))

        

    def send_data(self, node, data):#sends data to node
        ip_address = self.ip_address_dict[node]

        client = socket.socket()
        try:
            client.connect((ip_address, self.port))

            sent_bytes = client.send(data)
            gevent.sleep(0)
            client.close()
            return sent_bytes
        except:
            if self.debug: "Sending data to {}, {} failed".format(node, data)
            return -1

    def send_to_neighbours(self, data, origin):
        for node in self.g[self.this_node]: #send to all connected nodes
            if node == self.this_node or node == origin: continue
            gevent.spawn(self.send_data, node, data)
            gevent.sleep(0)
            

    def ping_node(self, node, update=True):#returns delay from self to node@ip_address:port
        ip_address = self.ip_address_dict[node]

        tries = 0
        delay = 0
        MAX_TRIES = 2

        while tries < MAX_TRIES:
            try:
                client = socket.socket()
                client.settimeout(5)
                print "hi, trying", (ip_address, self.port)
                client.connect((ip_address, self.port))
                print "bye"

                start = datetime.datetime.now()
                
                if self.debug: 
                    print("Attempted to ping node {} at {}:{}".format(node, ip_address,self.port))
                client.send('ECHO\n')
                client.recv(1024)
                end = datetime.datetime.now()
                
                client.close()

                delay = (((end - start) / 2).microseconds) / 1000.0
                break

            except Exception as e:
                print("Exception encountered", e)
                tries += 1
                if tries == MAX_TRIES:
                    delay = Routing.MAX_DELAY

            print("Pinged and measured a delay of {}".format(delay))

        if update: ## graph needs to be updated even if the ping time is Routing.MAX_DELAY since that indicates a connection being lost.        
            old_delay = self.g[self.this_node][node]['weight'] if node in self.g[self.this_node] \
                                                                            else Routing.MAX_DELAY

            if self.debug: print("Delay {} to {}, old {}, new {}").format(self.this_node, node, old_delay, delay)
            if delay != old_delay:
                if delay != Routing.MAX_DELAY:
                    if self.debug:
                        print("Adding edge {}--{}-->{} to graph".format(self.this_node, delay, node))
                    self.g.add_node(node)
                    self.g.add_edge(self.this_node, node, weight=delay)

                    #if node in self.disconnected_neighbours: self.disconnected_neighbours.pop(node, None)
                elif delay == Routing.MAX_DELAY:
                    if node in self.g[self.this_node]:
                        self.g.remove_edge(self.this_node, node)

                self.graph_modified = True
                #self.disconnected_neighbours[self.this_node] = 1

        return delay


    ## update_data = [neighbour, neighbourip, [node, nodeip, delay], ... ]
    def handle_update(self, update_data):
        if self.debug: print("Got update data of {}".format(update_data))
        if len(update_data) >= 2:
            incoming_node = update_data[0]
            incoming_node_ip = update_data[1]

            #if it's an entirely new node
            if not incoming_node in self.ip_address_dict.keys():
                self.ip_address_dict[incoming_node] = incoming_node_ip

            #if it's a known node that's requesting to be neighbour
            if not incoming_node in self.neighbour_list:
                self.neighbour_list.append(incoming_node)

            if not self.g[self.this_node].has_key(incoming_node):
                self.ping_node(incoming_node)

            #if incoming_node in self.disconnected_neighbours:
            #    self.disconnected_neighbours.pop(incoming_node, None)


            if len(update_data) > 2:
                self.handle_route_vector(incoming_node, update_data[2:])

    def handle_route_vector(self, incoming_node, route_vector):
        previous_node = incoming_node


        for (node, ip_address, delay) in route_vector:
            if node == self.this_node:    # handles the loop case
                break

            if not node in self.ip_address_dict.keys():
                self.ip_address_dict[node] = ip_address

            old_delay = self.g[previous_node][node]['weight'] if previous_node in self.g and \
                                                        node in self.g[previous_node] else Routing.MAX_DELAY

            if delay != old_delay:

                if delay != Routing.MAX_DELAY:
                        self.g.add_node(node)
                        self.g.add_edge(previous_node, node, weight=delay)
                        
                else:
                    if node in self.g[previous_node]:
                        self.g.remove_edge(previous_node, node)

                self.graph_modified = True


            previous_node = node

    def propagate_update(self, update_data):

        if len(update_data) >= 2:
            incoming_node = update_data[0]
            incoming_node_ip = update_data[1]

        data = [self.this_node, self.this_ip, [incoming_node, incoming_node_ip,
                                            self.g[self.this_node][incoming_node]['weight']]]
        
        for vector in update_data[2:]:
            data.append(vector)
        data = json.dumps(data)
        data = "UPDATE\n" + data

        self.send_to_neighbours(data, origin=incoming_node)

    def handle_connection(self, socket, address):

        data = socket.recv(1024)
        data = data.split('\n')

        print("New incoming {} connection from {}".format(data[0], address))
        if data[0] == 'ECHO':
            socket.send(data[0])
            socket.close()

        elif data[0] == 'UPDATE':
            data = json.loads(data[1])

            self.handle_update(data)
            self.propagate_update(data)

            socket.close()

        elif data[0] == 'DATA':
            data = json.loads(data[1])

            self.handle_data(data)
            self.propagate_data(data)

            socket.close();

        elif data[0] == 'STATUS':
            status = 'Node: ' + self.this_node + '\n'
            status += 'Connected nodes: ' + str(self.g.nodes()) + '\n'

            for a,b in self.g.edges():
                status += str(a) + ' ' + str(b) + ' ' + str(self.g[a][b]['weight']) + '\n'

            if self.debug: print status
            socket.send(status)
            socket.close()

        else:
            print 'UNRECOG: '
            print data



    def propagate_data(self, data):

        if len(data) >= 2:
            incoming_node = data[0]
            incoming_node_ip = data[1]

            new_data = [self.this_node, self.this_ip, data[2]]
            new_data = 'DATA\n' + json.dumps(new_data)

            for node in self.mst[self.this_node]:
                if ip_node_mapping[node] == incoming_node_ip: continue
                gevent.spawn(self.send_data, node, new_data)
                gevent.sleep(0)

    def handle_data(self, data):

        if len(data) >= 2:
            incoming_node = data[0]
            incoming_node_ip = data[1]

            print 'Received Data From: {}:{}'.format(incoming_node, incoming_node_ip)
            print data
                


    #this function pings each of its neighbours
    def populate_neighbour_latencies(self, only_ping_dead=False):
        workers = []

        if self.debug and not only_ping_dead:
            print "Scheduled populate_neighbour_latencies, list is {}".format(self.neighbour_list) 

        #schedule run ping_node(node)
        for node in self.neighbour_list:

            if only_ping_dead:
                if node not in self.g[self.this_node]:
                    if self.debug: print "Pinging dead neighbour {}".format(node) 
                    workers.append(gevent.spawn(self.ping_node, node))
            else:
                workers.append(gevent.spawn(self.ping_node, node))
        #wait until all the workers are done with running the scheduled ping_node()
        gevent.joinall(workers)


    def ping_dead_neighbours(self):
        self.populate_neighbour_latencies(only_ping_dead=True)
        if self.graph_modified:
            self.generate_spanning_tree()
            self.generate_fwd_table()

    def generate_spanning_tree(self):
        if self.debug: print 'Graph modified, regenerating mst'
        self.mst = nx.minimum_spanning_tree(self.g)
        self.graph_modified = False


    #call func at every delay seconds
    def schedule(self, delay, func, *args, **kw_args):
        gevent.spawn_later(0, func, *args, **kw_args)
        gevent.spawn_later(delay, self.schedule, delay, func, *args, **kw_args)



    def propagate_neighbour_latencies(self):
        connected_neighbours = self.g[self.this_node]
        if self.debug: print("Attempting to propagate my list of latencies to: {}".format(connected_neighbours))

        for nodeS in connected_neighbours.keys():
            weightS = connected_neighbours[nodeS]['weight']
            for nodeD in self.neighbour_list:
                if nodeS == nodeD: continue

                weightD = connected_neighbours[nodeD]['weight'] if nodeD in connected_neighbours \
                                                                        else Routing.MAX_DELAY

                data = [self.this_node, self.this_ip, [nodeD, self.ip_address_dict[nodeD], weightD]]
                data = 'UPDATE\n' + json.dumps(data)

                if self.debug: print("Going to update {} with {}, disconnected={}".\
                                                            format(nodeS, data, nodeD not in connected_neighbours))
                gevent.spawn(self.send_data, nodeS, data)


    def populate_and_propogate(self):
        self.populate_neighbour_latencies()
        self.propagate_neighbour_latencies()

        if self.graph_modified: 
            self.generate_spanning_tree()
            self.generate_fwd_table()



    def generate_fwd_table(self):
        path = None
        if self.this_node in self.mst:
            self.fwd_table = nx.shortest_path(self.g, source=self.this_node)

    def get_next_node_to(self, dest):
        if self.this_node in self.fwd_table and dest in self.fwd_table[self.this_node]:
            return self.fwd_table[self.this_node][dest][1]  #fwd table of the format [source, A, B, C, dest]
        return None

    def get_fwd_table(self, node):
        return nx.shortest_path(self.g, source=node)

    def run(self):
        server = StreamServer((self.server_ip, self.port), self.handle_connection)
        print 'Starting server on ip address {} and port: '.format(self.server_ip) + str(self.port)

        gevent.signal(signal.SIGTERM, server.stop)
        gevent.signal(signal.SIGQUIT, server.stop)
        gevent.signal(signal.SIGINT, server.stop)

        server.start()

        #send update messages every 10 seconds
        self.schedule(20, self.populate_and_propogate)
        self.schedule(10, self.ping_dead_neighbours)

        server.serve_forever()

if __name__ == "__main__":
    #parse some command line arguments
    parser = argparse.ArgumentParser(description='Start to listen and send refresh messsages')
    parser.add_argument('-d', '--debug', action='store_true', help='enable debugging output')
    
    debug_opt = False
    args = parser.parse_args()
    if args.debug: 
        debug_opt = True
        print("Debugging output enabled.")


    routing = Routing(debug=debug_opt)
    routing.run()
