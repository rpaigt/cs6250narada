# /*
#  * This program is free software; you can redistribute it and/or modify
#  * it under the terms of the GNU General Public License version 2 as
#  * published by the Free Software Foundation;
#  *
#  * This program is distributed in the hope that it will be useful,
#  * but WITHOUT ANY WARRANTY; without even the implied warranty of
#  * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  * GNU General Public License for more details.
#  *
#  * You should have received a copy of the GNU General Public License
#  * along with this program; if not, write to the Free Software
#  * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#  */

#it seems like to translate C++ import to python import, you take the prefix
#compare this to $NSPATH/examples/tutorial/first.cc
import ns.core
import ns.network
import ns.csma
import ns.internet
import ns.point_to_point
import ns.applications
#import ns.ipv4_global_routing_helper #doesn't exist in python binding yet

class Narada(ns.network.Application):
    def StartApplication(self):
	print("Hi!")

    def StopApplication(self):
	print("Bye!")

    #def DoStart(self):
	#print("In dostart")
	#super(Narada, self).SetStartTime(t)
#Switching between these 2 and compare log.out,
#with udp echo, it recognises the starttime, but not narada.
#going to examine how udpechoclient was written vs Narada was written
nar = Narada()
nar2 = Narada()
#nar = ns.applications.UdpEchoClient()
#nar2 = ns.applications.UdpEchoClient()

nodes = ns.network.NodeContainer()
nodes.Create(2)

pointToPoint = ns.point_to_point.PointToPointHelper()
pointToPoint.SetDeviceAttribute("DataRate", ns.core.StringValue("5Mbps"))
pointToPoint.SetChannelAttribute("Delay", ns.core.StringValue("2ms"))

devices = pointToPoint.Install(nodes)

stack = ns.internet.InternetStackHelper()
stack.Install(nodes)

address = ns.internet.Ipv4AddressHelper()
address.SetBase(ns.network.Ipv4Address("10.1.1.0"), ns.network.Ipv4Mask("255.255.255.0"))

interfaces = address.Assign (devices);

nodes.Get(1).AddApplication(nar)
nodes.Get(0).AddApplication(nar2)

print "nar's node is {}".format(nar2.GetNode())

nar.SetStartTime(ns.core.Seconds(2.0))
nar.SetStartTime(ns.core.Seconds(8.0))
nar2.SetStopTime(ns.core.Seconds(4.0))
nar2.SetStopTime(ns.core.Seconds(9.0))

ns.core.Simulator.Run()
ns.core.Simulator.Destroy()

