cs6250narada
============

Implementation of Narada platform


How to run
==========
For each node in the overlay running Narada, it needs two files in the same
folder as routing.py to run the program.

ipaddresses.txt

format:
A,1.1.1.1
B,2.2.2.2
C,3.3.3.3
D,4.4.4.4

These are the node names and ip addresses separated by a comma. The first
line/node is the current host itself.

neighbours.txt

format:
B
C
D

These are the nodes adjacent to the current host (i.e. A)

Then just run ./routing.py -v or python routing.py

How to test using VM
====================
1. Create a network of a few VM's (using NAT in VMWare player). 
2. For each VM,
    a. git clone the repository
    b. create ipaddresses.txt with the VM's name and ipaddress as the first
       entry
    c. create neighbours.txt with all nodes except the current VM (you cannot
       be neighbours with yourself)
3. Run ./routing.py -v on each VM. Recommend 1 VM to use ssh to issue commands
   to all other VMs simultaneously.


How to install
==============
Libraries needed:
Networkx
Gevent

Check the installation guides online. 

For ubuntu try this

sudo apt-get install python-dev
sudo apt-get install libevent-dev
sudo apt-get install python-pip

sudo pip install networkx
sudo pip install gevent

or alternatively for python libraries try:
sudo easy_install gevent
sudo easy_install networkx


