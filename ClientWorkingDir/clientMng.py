# -*- coding: utf-8 -*-
"""

@author: Shafik
"""

import LocationModule
import Pyro4
import os
import time
import win32com.shell.shell as shell
import uuid
import threading
from signal import signal, SIGINT
from sys import exit



baseVolumeId = ''
def getBaseVolId(Id):
    global baseVolumeId
    baseVolumeId = Id

clientUuid = str(uuid.uuid4())
clientLocFile = LocationModule.LocationFile(clientUuid)

def addRoute():
    with open(clientLocFile, "r") as f:
        readServerUri = f.readline()
        f.flush()
    ipAndPort = readServerUri.split("@",1)[1]
    readServerIp = ipAndPort.split(":")[0]
    #print("server IP = " + readServerIp)
    global deletableRouteIp
    deletableRouteIp = readServerIp
    commands = "route add 172.17.0.0/16 " + readServerIp
    shell.ShellExecuteEx(lpVerb='runas', lpFile='cmd.exe', lpParameters='/c '+commands)
    
def deleteRoute():
    commands = "route delete 172.17.0.0/16 " + deletableRouteIp
    shell.ShellExecuteEx(lpVerb='runas', lpFile='cmd.exe', lpParameters='/c '+commands)

def getServerUri():
    with open(clientLocFile, "r") as f:
        serverMngUri = f.readline()
        f.flush()
    return serverMngUri




serverMngUri = getServerUri()
addRoute()
oldServerUri = serverMngUri
serverMng = Pyro4.Proxy(serverMngUri)   #reads server uri and create a remote object
serverMng._pyroAsync()


def initServerSide():     #inits serverside(serverMng runs a container,doesn't return anything)
    print("ServerMng Uri = " + serverMngUri)    
    asyncResult = serverMng.runContainer(clientUuid, baseVolumeId) 
    while asyncResult.ready != True:  #waiting async resut halted the execution until the value is available
        pass
    print("connected new container")
    return

def giveContainerUriToClientApp():
    containerUri = serverMng.returnServerAppUri(clientUuid)
    while containerUri.ready != True:
        pass
    print("containerUri = " + containerUri.value)
    containerObject = Pyro4.Proxy(containerUri.value)
    containerObject._pyroAsync()
    return containerObject

def controlServerUri(stopEvent, opCont): # stopEvent=pill2kill
    filename = clientLocFile
    _cached_stamp = os.stat(filename).st_mtime  #cache the time
    while True:
        while True:
            if os.path.exists(filename):
                stamp = os.stat(filename).st_mtime
            if stamp != _cached_stamp:  # compare stamp time with cache                   
                _cached_stamp = stamp
                # File has changed, so do something... 
                print(" ")
                print("Server changed")
                deleteRoute()
                stopEvent.set()
                break      
        global serverMngUri
        oldServerUri = serverMngUri
        serverMngUri = getServerUri()      #read new uri for new serverMng
        print("New serverMng Uri = " + serverMngUri)
        global serverMng
        serverMng._pyroRelease()
        serverMng = Pyro4.Proxy(serverMngUri)   #connect new serverMng
        serverMng._pyroAsync()
        addRoute()
        if(opCont.is_set() == True): #there is an operation on server
            print("there is a process on server")    
            previousResult = serverMng.getUnfinishedOpResult(oldServerUri, clientUuid, baseVolumeId)           
            print("getting list from old server")
            print(previousResult.value)
            stopEvent.clear()
            opCont.clear()
            serverMng.deleteFromNewServer(clientUuid)
        else: #no unfinished operation on server
            print("no process on server")
            isVolSent = serverMng.getVolume(oldServerUri, clientUuid, baseVolumeId)
            while isVolSent.ready != True:
                pass
            serverMng.deleteFromNewServer(clientUuid)
            stopEvent.clear()
            
def setOperationCont():
    operationCont.set()
    
def clearOperationCont():
    operationCont.clear()

operationCont = threading.Event()
operationCont.clear()

pill2kill = threading.Event()
pill2kill.clear()
     
t1 = threading.Thread(target=controlServerUri, args=(pill2kill, operationCont, ))
t1.start()

def handler(signal_received, frame):
    isFileExists = os.path.isfile(clientLocFile)
    if isFileExists:
        os.remove(clientLocFile)
    serverMng._pyroRelease()
    deleteRoute()
    print("exitting")
    exit(0)
    
signal(SIGINT, handler)


