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

def mesh_repair():#called every T intervals
	global graph_modified
	T = 1000#timeout, now need to repair these nodes since they did nto update for T

	while True: ## We can just call mesh repair at regular intervals. Does this need to be while(true)?

		curtime = get_curtime()
		update_list = []

		for e in update_dict.keys():
			if (update_dict[e] - curtime) >= T:
				update_list.append(e,update_dict[e])

		update_list = sorted(update_list, key=lambda e: e[1])

		while len(update_list) and (update_list[0] >= T):
			temp = update_list.pop(0)
			delay = ping_node(temp, update=False)

			if(delay != MAX_DELAY):
				update_dict[temp] = 0

				if(nx.path.bidirectional_dijkstra(g, this_node, temp)):
					g.add_node(temp)

				g.add_edge(this_node, temp, weight=delay)
				graph_modified = True

		if len(update_list):
			prob = len(update_list) / len(update_dict)

			if random.random() >= (1-prob):
				temp = update_list.pop(0)
				delay = ping_node(temp, update=False)

				if(delay!=MAX_DELAY):
					update_dict[temp] = 0
					if nx.path.bidirectional_dijkstra(g, this_node, temp):
						g.add_node(temp)
					g.add_edge(this_node, temp, weight=delay)
					graph_modified = True

		sleep_repair(time)	

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
