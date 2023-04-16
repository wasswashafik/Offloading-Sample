
"""
@author: shafik
"""

from volumeFolder import serverTODO
#import sys
import socket
import Pyro4



instance = serverTODO.ToDoClass
exposedClass = Pyro4.expose(instance)

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)

with open("volumeFolder/containerPort.txt", "r") as f:
    var = f.read()
    f.flush()

daemon = Pyro4.Daemon(host=local_ip,port=int(var))    # make a Pyro daemon
uri = daemon.register(exposedClass)

with open("volumeFolder/serverTODOuri.txt", "w") as w: #write uri to shared file
     w.write(str(uri))
     w.flush()

print("Ready. Object uri =", uri)      # print the uri
daemon.requestLoop()
