
"""
@author: Shafik
"""

import sqlite3
import time
from itertools import permutations

class ToDoClass(object):
    def SearchInList(self, word):
        open('volumeFolder/result.txt', 'w').close() #delete content of result.txt
        letterList = list(word)
        sqlstr = "SELECT DISTINCT word FROM entries WHERE"  
        count = 0
        for i in permutations(letterList, 4):
            word = ''.join(i)
            word = "'%" + word + "%'"
            if count == 0:
                sqlstr = sqlstr + " word like " + word
            else:
                sqlstr = sqlstr + " or word like " + word
            count = count + 1
        sqliteConnection = sqlite3.connect('volumeFolder/dictionary.db')
        cursor = sqliteConnection.cursor()
        cursor.execute(sqlstr,)
        results = cursor.fetchall()
        sqliteConnection.close()
        feedback = "Here are the words:"
        time.sleep(30)
        for row in results:     
            feedback += "\n" + str(row)
        with open("volumeFolder/result.txt","w") as w:
   	        w.write(feedback)
   	        w.flush()
        return feedback
               
    