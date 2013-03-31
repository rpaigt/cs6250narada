import sys, os, re, copy.deepcopy
import networkx as nx

class routing:
	def __init__(member,nodeid):
		self.fwdtable={}#(unique node id, ip)
		self.bestroutes={}#route store
		self.cache={}#id,ip cache
		self.timer=Timer #timer 																	#find
		self.opt=False
		self.neighbors=[]
		self.nodeid=nodeid
		self.member=member
	def propagateUpdate(newroute):
		for node in neighbors:
			sendData(pickle(self.nodeid,newroute))
	def checkRoute(route):#assume route updates are like (senderID, [(revnoceid, prevhopdistance),(,)])
		nodeid=route[0]
		nodevec=route[1]
		#update routestore
		routelen=sum([i[1] for i in nodevec])+getNodeDist(nodeid)
		if !(nodeid in self.bestroutes.keys()):
			self.bestroute[nodeid]=[]
		if (routelen<bestroutes[nodeid][0]):
			self.bestroutes[nodeid].insert(route,0)
			self.bestroutes.pop[-1]
		elif (routelen<bestroutes[nodeid][1]):
			self.bestroutes[nodeid].insert(route,1)
			self.bestroutes.pop[-1]
		if nodeid not in self.neighbors:
			self.neighbors.append(nodeid)
		route[1].append(self.nodeid,getNodeDist(nodeid))
		propagateUpadate(route)
		if(timer.expires):#when timer expires the node build its reverse spanning tree, computes the forwarding table and resets timer
			graph=computeGraph(bestroutes)#graph=[nodes, edges]										#create
			spantree=computeSpanningTree(graph)#same as above										#create
			updateFwdTable(spantree, fwdtable)#find out where to send packet when it is received	#create
			timer.reset()																			#find
	def sendData(data,destid):
		ip=cache[fwdtable[destid]]
		send(pickle(self.nodeid,data), ip)					#find
	def updateTimer():
		#update
		if(timer.longtimerexpire):
			self.opt=True

	def computeGraph(bestroutes):
		G = nx.Graph()
		for(key in bestroutes.keys()): # This adds the nodes in the graph
			G.add_node(key)
			
		for(key in bestroutes.keys()): # This is to add the edges in the graph
			route = bestroutes[key]
			for(i in range len(route))
				if(route[i + 1]):      #please check if this condition will work
					G.add_edge(i,i+1)
		return G

	def computeSpanningTree(graph):
		T = nx.minimum_spanning_tree(G)
		return T

	def updateFwdTable(spantree, fwdtable):



