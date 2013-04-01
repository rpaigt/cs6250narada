cs6250narada
============

implementation of narada platform


Need two files in the same folder as script to run the program.

ipaddresses.txt

format
A,1.1.1.1
B,2.2.2.2
C,3.3.3.3

these are the neighbours node names and ip addresses separated by a comma. The
first line/node is the current host itself.

neighbours.txt

format
B
C

these are the nodes adjacent to the current host.

Create a network using some VM's and fill in the ip addresses. Add print statements wherever neccessary and figure out if the updates are propagating directly.


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
