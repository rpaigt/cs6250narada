#!/bin/sh

##### Run some local tests on routing2.py ####

#kill existing server instances first
pkill routing2.py

#start server
../routing2.py &
sleep 1s

echo "Trying to send the server a DATA packet"
nc 127.0.0.1 30000 < testdata.txt

#clean up
pkill routing2.py
