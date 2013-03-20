import socket               # Import socket module
import datetime				# Import dateTime module

s = socket.socket()         # Create a socket object
host = socket.gethostname() # Get local machine name
port = 12345                # Reserve a port for your service.
now = datetime.datetime.now()
s.connect((host, port))
print s.recv(1024)
nowNew = datetime.datetime.now()
print "TTL is = ", (nowNew - now)/2

s.close                     # Close the socket when done
