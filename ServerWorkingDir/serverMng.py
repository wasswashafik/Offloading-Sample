"""
@author: Shafik
"""

#import sqlite3
import time
import Pyro4
import socket
import os
import subprocess
import shutil
import sys
import threading
import getpass
from signal import signal, SIGINT
from sys import exit

#get ip address of ubuntu vm
cmd = ["hostname", "-I"]
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
stdout, stderr = proc.communicate()
ip = stdout.decode('ascii').split()[0]



dictionary = {} #used for keeping client uuid-volumeFolder pairs
containerIdDictionary = {} #used for keeping client uuid-containerId pairs
uri = ""

@Pyro4.expose
class ServerManager(object):
    def runContainer(self, clientUuid, baseVolumeId):
        #copy a volume from base volume and make uuid-volume pair 
        #however, maybe volume already exists since it comes from old server, so check it
        volumeName = ""
        volumePath = ""
        if clientUuid in dictionary:
            volumeName = dictionary[clientUuid]
            volumePath = os.getcwd() + "/volumes/" + volumeName
        else:
            volumeName = "volumeFolder_" + str(clientUuid)
            dictionary[clientUuid] = volumeName
            volumePath = os.getcwd() + "/volumes/" + volumeName
            isDirExists = os.path.isdir(volumePath)
            if isDirExists:
                pass
            else:
                shutil.copytree(os.getcwd() + "/baseVolumes/baseVol_" + baseVolumeId, volumePath)
            
        
        #get an available port for container
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        addr = s.getsockname()
        s.close()
        #you need to wait for volume transfer if it takes time
        isFileExists = os.path.isfile(volumePath + "/containerPort.txt") 
        while isFileExists == False:
            isFileExists = os.path.isfile(volumePath + "/containerPort.txt")
        with open(volumePath + "/containerPort.txt","w") as w:
   	        w.write(str(addr[1]))
   	        w.flush() 
    	      
        #get image name
        imgNamePath = volumePath + "/imgName.txt"
        #you need to wait for volume transfer if it takes time
        isFileExists = os.path.isfile(imgNamePath) 
        while isFileExists == False:
            isFileExists = os.path.isfile(imgNamePath)
        with open(imgNamePath, "r") as f:
            imgName = f.read()
            f.flush()
        
        command = "sudo docker run -d -p " + str(addr[1]) + ":" + str(addr[1]) + " -v " + os.getcwd() + "/volumes/"+ volumeName +":/code/volumeFolder " + imgName
        containerId = subprocess.getoutput(command)
        containerIdDictionary[clientUuid] = containerId
        print(containerId)
        print("container is created")
        time.sleep(0.5)
        return 1
        
    def returnServerAppUri(self, clientUuid):
        #read container pyro uri from file
        volumePath = os.getcwd() + "/volumes/" + dictionary[clientUuid]
        path = volumePath + "/serverTODOuri.txt"
        isFileExists = os.path.isfile(path)
        while isFileExists == False:
            isFileExists = os.path.isfile(path)
        with open(path, "r") as f:
            var = f.read()
            f.flush()
        return var
        
    def getVolume(self, oldServerUri, clientUuid, baseVolumeId):
        volumeName = "volumeFolder_" + str(clientUuid)
        dictionary[clientUuid] = volumeName
        global oldServerMng
        oldServerMng = Pyro4.Proxy(oldServerUri)    #connect to old serverMng
        oldServerMng._pyroAsync()
        username = getpass.getuser()
        path = username + "@" + ip + ":" + os.getcwd() + "/volumes"
        oldServerMng.giveVolume(clientUuid, path, username, baseVolumeId)
        volumePath = os.getcwd() + "/volumes/" + volumeName
        isDirExists = os.path.isdir(volumePath)
        while isDirExists == False:
            isDirExists = os.path.isdir(volumePath)
        return 1
        
    def giveVolume(self, clientUuid, path, username, baseVolumeId):
        volumeName = dictionary[clientUuid]
        volumePath = os.getcwd() + "/volumes/" + volumeName
        rsyncCommand = "/usr/bin/rsync -av --rsh=\"/usr/bin/sshpass -p ssh -o StrictHostKeyChecking=no -l " + username + "\" " + os.getcwd() + "/volumes/" + volumeName + " " + path
        os.system(rsyncCommand)
        return 1
      
    
    def getUnfinishedOpResult(self, oldServerUri, clientUuid, baseVolumeId):
        volumeName = "volumeFolder_" + str(clientUuid)
        dictionary[clientUuid] = volumeName
        global oldServerMng
        oldServerMng = Pyro4.Proxy(oldServerUri)    #connect to old serverMng
        oldServerMng._pyroAsync()
        username = getpass.getuser()
        path = username + "@" + ip + ":" + os.getcwd() + "/volumes"
        result = oldServerMng.givePreviousResult(clientUuid, path, username, baseVolumeId)
        if result.ready == True:
            oldServerMng._pyroRelease()
        return result.value    #return result to client
    
    def giveUnfinishedOpResult(self, clientUuid, path, username, baseVolumeId):
        volumeName = dictionary[clientUuid]
        volumePath = os.getcwd() + "/volumes/" + volumeName
        rsyncCommand = "/usr/bin/rsync -av --rsh=\"/usr/bin/sshpass -p ssh -o StrictHostKeyChecking=no -l " + username + "\" " + os.getcwd() + "/volumes/" + volumeName + " " + path
        os.system(rsyncCommand)
        while os.path.getsize(volumePath + "/result.txt") == 0:  
            pass    #do nothing,wait till the result is written
       
        with open(volumePath + "/result.txt", "r") as f:
            result = f.read()
            f.flush()
                
        os.system(rsyncCommand)             
        return result
        
    def deleteFromNewServer(self, clientUuid):
        oldServerMng.deleteOldContainer(clientUuid)         
        return              
        
    def deleteOldContainer(self, clientUuid):
        #stop and delete container and delete the volume from this server
        stopCommand = "sudo docker stop " + containerIdDictionary[clientUuid]
        containerId = subprocess.getoutput(stopCommand)
        
        volumeName = dictionary[clientUuid]
        volumePath = os.getcwd() + "/volumes/" + volumeName    
        deleteVolumeCommand = "sudo rm -rf " + volumePath
        os.system(deleteVolumeCommand)
        dictionary.pop(clientUuid)
        containerIdDictionary.pop(clientUuid)
        
        deleteCommand = "sudo docker rm " + containerId    
        containerId = subprocess.getoutput(deleteCommand)
        print(containerId)
        print("container is deleted")
        return
        


daemon = Pyro4.Daemon(host=ip)                # make a Pyro daemon
uri = daemon.register(ServerManager)   # register Server Manager
print("Ready. Object uri =", uri)      # print the uri
desktopPath = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')

#write server uri to shared file
with open(desktopPath + "/guest_share/urifile.txt", "a") as w:
     w.write(str(uri) + "\n")
     w.flush()
     w.close()
     
def handler(signal_received, frame):
    with open(desktopPath + "/guest_share/urifile.txt", "r") as t:
        lines = t.readlines()
        t.close()
    with open(desktopPath + "/guest_share/urifile.txt", "w") as t:
        t.close()
    with open(desktopPath + "/guest_share/urifile.txt", "a") as t:
        for line in lines:
            if line.strip("\n") != str(uri):
                t.write(line)
        t.close()
    print("exitting")
    exit(0)
                
signal(SIGINT, handler)     

daemon.requestLoop()                   # start the event loop of the server to wait for calls

