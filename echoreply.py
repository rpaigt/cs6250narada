import socket               # Import socket module
import sys

if len(sys.argv) < 2:
	print 'Usage: %s <ip address>' % sys.argv[0]
	sys.exit(1)

server = socket.socket()         # Create a socket object
host = sys.argv[1]		        # Get local machine name
port = 30000                # Reserve a port for your service.

server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
	server.bind((host, port))        # Bind to the port
except:
	print "Cannot bind to %", argv[1]

print "Echo reply listening at %s:%s" % (host, port)

server.listen(5)                 # Now wait for client connection.

active = True
while active:
	try:
		client, addr = server.accept()     # Establish connection with client.
		print 'Ping from ', addr
		client.send('ECHO REPLY')
		client.close()                # Close the connection
	except KeyboardInterrupt:
		active = False

server.close()

	