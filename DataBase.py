import sqlite3

class DataBase:
    def __init__(self, sql_file):
        self.sql_file = sql_file

        self.connection = sqlite3.connect(self.sql_file, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row

        self.cursor = self.connection.cursor()

    def query(self, query, commit=False, massive=False):
        if(not commit):
            self.cursor.execute(query);
            try:
                data = self.cursor.fetchall()
                if(massive):
                    return data
                else:
                    return dict(data[0])
            except:
                return dict()
        else:
            try:
                self.cursor.execute(query)
                self.connection.commit()
            except Exception as err:
                print('[\033[31mError\033[37m] Query Failed: %s\n[\033[31mError\033[37m] Error: %s' % (query, str(err)))