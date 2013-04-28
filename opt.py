def get_curtime():#stub, needs to be implemented
	pass
	#return the current time, to compare with those in update_dict

def sleep_repair():#stub, sleep for a while, use gevent to call it after k time or just call mesh_repair in a separate thread
	pass

update_dict = {}#stores last_time_node_was_updated as value
utility_dict = {}#stores utility of node

def get_node_utility(trynode):
	utility = 0
	path = nx.all_pairs_shortest_path(g)
	for node in fwd_table.keys():
		if (node == this_node):
			pass
		else:
			oldlat = path[this_node][node]
			newlat = path[this_node][trynode] + path[trynode][node]
			if(newlat < oldlat):
				utility = utility + ((oldlat - newlat) / oldlat)

	return utility

def get_mutual_cost(trynode):
	count1 = 0
	count2 = 0
	f2 = get_fwd_table(trynode)
	f1 = fwd_table

	for i in f1.keys():
		if f1[keys] == trynode:
			count1 = count1 + 1

	for j in f2.keys():
		if f2[keys] == this_node:
			count2 = count2+1

	return max(count1, count2)

def ProbeAndAdd(curnode, newnode):
	delay = ping_node(newnode, update=False)#REPLACE IF NECESSARY :need to know if newnode is alive and if so, link to it
	if(delay != MAX_DELAY):
		#REPLACE IF NECESSARY: add link from curnode to newnode
		g.add_edge(curnode, newnode, weight=delay)
		graph_modified = True
	
def mesh_repair(curnode):#
	MAX_DELAY=9999
	T=100
	while True: ## We can just call mesh repair at regular intervals. Does this need to be while(true)?
		curtime = get_curtime()#IMPLEMENT
		#L contains tuples of (node,last_update_time) for curnode
		#Q is list of nodes for which curnode has not recieved an update yet for time T=timeout
		Q=[]
		for e in L:
			if (e[1] - curtime) >= T:
				Q.append(e)
		Q = sorted(Q, key=lambda e: e[1])
		while len(Q) and (Q[0] >= T):
			front = Q.pop(0)
			ProbeAndAdd(curnode, front)
		if len(Q):
			prob = len(Q) / len(L)#REPLACE IF NECESSARY:len(L) is the number of all nodes
			if random.random() >= (1-prob):
				front = Q.pop(0)
				ProbeAndAdd(curnode,front)
		sleep(time)#REPLACE IF NECESSARY:with whatever sleep function gevent uses

def optimise_all():#called every T seconds
	mesh_repair()

	for node in update_dict.keys():
		if not utility_dict.has_key(node):
			utility_dict[node] = [0,0]
		
		utility = get_node_utility(node)
		
		if utility_dict(node)[0] < utility:
			utility_dict(node)[0] = utility

	for node in update_dict.keys():
		cost = get_mutual_cost(node)
		
		if utility_dict(node)[1] < cost:
			utility_dict(node)[1] = cost
