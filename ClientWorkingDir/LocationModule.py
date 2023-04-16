"""

@author: Shafik
"""

def LocationFile(clientUuid):
    clientLocFile = 'writeYourFolderHere\\loc_' + clientUuid + '.txt'
    with open("writeYourFolderHere\\urifile.txt", "r") as k:
        ServerUri = k.readline()
        k.flush()
        k.close()
    with open(clientLocFile, "w") as f: #A text file is created for client,server uri is written
        f.write(ServerUri)
        f.flush()
        f.close()
    return clientLocFile