import sys, os, re, copy.deepcopy

class routing:
	def __init__():
		self.fwdtable={}#(unique node id, ip)
		self.bestroutes={}#route store
		self.cache={}#id,ip cache
		self.timer=Timer #timer 																	#find
		self.opt=False
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
		if(timer.expires):#when timer expires the node build its reverse spanning tree, computes the forwarding table and resets timer
			graph=computeGraph(bestroutes)#graph=[nodes, edges]										#create
			spantree=computeSpanningTree(graph)#same as above										#create
			updateFwdTable(spantree, fwdtable)#find out where to send packet when it is received	#create
			timer.reset()																			#find
	def sendData(data,destid):
		ip=cache[fwdtable[destid]]
		send(data, ip)
	def updateTimer():
		#update
		if(timer.longtimerexpire):
			self.opt=True
