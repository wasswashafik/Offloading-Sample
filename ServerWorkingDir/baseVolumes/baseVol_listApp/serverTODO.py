
"""
@author: Shafik
"""

# saved as serverTODO.py
import sqlite3
import Pyro4
import time


#@Pyro4.expose                          # to say ToDoClass class is remotely accessible
class ToDoClass(object):
    def addToList(self, work):
        sqliteConnection = sqlite3.connect('volumeFolder/list.db')
        cursor = sqliteConnection.cursor()
        sqlstr = "INSERT INTO ToDoList (Works) VALUES (?);"
        cursor.execute(sqlstr,(work,))
        sqliteConnection.commit()
        sqliteConnection.close()
        return
               
    def sendList(self):
        open('volumeFolder/result.txt', 'w').close() #delete content of result.txt
        time.sleep(5)
        sqliteConnection = sqlite3.connect('volumeFolder/list.db')
        cursor = sqliteConnection.cursor()
        sqlstr = "SELECT * FROM ToDoList"
        cursor.execute(sqlstr)
        results = cursor.fetchall()
        sqliteConnection.close()
        feedback = "Here is the ToDo List:"
        time.sleep(30)
        for row in results:
            feedback += "\n" + str(row[0])
        #bu feedback'i bir file'a yazmak gerekecek migration durumu için
        #böylece servermng o file'dan okuyarak yeni servermng'ye gönderebilir
        with open("volumeFolder/result.txt","w") as w:
   	        w.write(feedback)
   	        w.flush()
        return feedback


