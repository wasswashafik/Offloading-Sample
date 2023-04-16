"""
@author: Shafik
"""

import clientMng
import time
import threading


work = ""
def getInput():
    global work
    work = "x"
    while True:
        if work == "":
            work = input("Add to list: ").strip()


t1 = threading.Thread(target=getInput)
t1.start()

if __name__ == "__main__":
    
    clientMng.getBaseVolId("listApp")
    while True:  
        clientMng.initServerSide()        
        myTodo = clientMng.giveContainerUriToClientApp()
        work = ""
        print("Ready for input")
        while True: 
            clientMng.clearOperationCont()
            if(work != ""): #if input written           
                myTodo.addToList(work)
                print("adding work to list")
                asyncResult = myTodo.sendToDoList()
                print("result not ready yet")
                while asyncResult.ready == False:
                    clientMng.setOperationCont()
                    #while waiting for asyncResult, pill2kill is set in thread, then break this while
                    if clientMng.pill2kill.is_set() == True:
                        print("new server is found")
                        myTodo._pyroRelease()
                        break #break from this while
                if clientMng.pill2kill.is_set() == True:
                    break #location change, break from second while
                print(asyncResult.value)
                work = ""
            else:
                if(clientMng.pill2kill.is_set() == True):
                    break     #no input, but location change, break from second while      
        print("waiting result from previous server")
        while clientMng.pill2kill.is_set() == True:
            #old result is get in thread, pill2kill false, then out from this while
            pass
        