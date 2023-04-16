"""
@author: shafik
"""

import clientMng
import time
import threading

word = ""
def getInput():
    global word
    word = "x"
    while True:
        if word == "":
            word = input("Enter 4 letters: ").strip()
            if len(word) != 4:
                word = ""
                print("Please enter 4 letters")

    
    
t1 = threading.Thread(target=getInput)
t1.start()

if __name__ == "__main__":

    clientMng.getBaseVolId("searchApp")   
    while True:        
        clientMng.initServerSide()
        mySearch = clientMng.giveContainerUriToClientApp()
        word = ""
        print("Ready for input")
        while True:
            clientMng.clearOperationCont()
            if(word != ""): #if input written
                asyncResult = mySearch.SearchInList(word)
                print("searching")
                while asyncResult.ready == False:
                    clientMng.setOperationCont()
                    #while waiting for asyncResult, pill2kill is set in thread, then break this while
                    if clientMng.pill2kill.is_set() == True:
                        print("new server is found")
                        mySearch._pyroRelease()
                        break #break from this while
                if clientMng.pill2kill.is_set() == True:
                    break #location change, break from second while
                print(asyncResult.value)
                word = ""
            else:
                if(clientMng.pill2kill.is_set() == True):
                    break     #no input, but location change, break from second while
        print("waiting result from previous server")
        while clientMng.pill2kill.is_set() == True:
            #old result is get in thread, pill2kill false, then out from this while
            pass
            