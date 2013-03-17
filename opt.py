import sys, math, os, copy,random
"""
assumptions--
   getLatency(id1,id2)//return stored latency
   computeLatency(id1, id2)//use sockets to compute the latency
"""
class Members:
    def __init__(self):
        self.memberlist=[]
class Routing:
    def __init__(self):
        self.table={}#id to IP/MAC mapping
    def queryCost(self):
class Member:
    def __init__(self, members=None, routing=None):
        self.members=members
        self.id=(int)(random.random()*10000)
        for i in xrange(len(self.members.memberlist)):
            while((i.id)!=self.id):
                self.id=(int)(random.random()*10000)            
        self.routing=routing
        if(self.routing==None):
            self.routing=Routing()
        self.nexthop={}#dest id-> nexthop id mapping
        self.seq=0
    def evaluate_utility(self,id_j):
        jutility=0
        for i in self.members.memberlist:
            if (i.id!=self.id):
                lat_cur=self.routing.getLatency(self.id,i.id)
                lat_new=self.routing.computeLatency(self.id,id_j)+self.routing.computeLatency(id_j,i.id)
                if(lat_new<lat_cur):
                    jutility=jutility+((lat_new-lat_cur)/lat_new)
        return jutility
    def getCostToI(self,id_i):
        cost=0
        for k in self.nexthop.keys():
            if(self.nexthop[k]==id_i):
                cost=cost+1
        return cost
    def eval_consensus_cost(self,id_j):
        costIJ=self.getCostToI(id_j)
        temp=self.seq
        self.send(self.id, self.seq,id_j,0, ("getCostToI", [id_j,self.id]))
        costJI=self.waituntilnotified(!self.receive(temp))
        return max(costIJ,costJI)
    def receive(self,insdata):
        self.notifyfunc()
        pass
        #use self.routing to receive, process and return data
    def send(self, from_id, from_seq,to_id,rrtype,insdata):
        self.seq=self.seq+1
        pass
        #use self.routing to send instruction and data
    



