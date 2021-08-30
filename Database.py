from Config import Config
import MySQLdb

class Database(object):

    __host       = None
    __user       = None
    __password   = None
    __database   = None
    __connection = None
    __cursor     = None

    def __init__(self, user=Config.DATABASE_CONFIG['user'], password=Config.DATABASE_CONFIG['password'], host=Config.DATABASE_CONFIG['server'], database=Config.DATABASE_CONFIG['name']):
        self.__user     = user
        self.__password = password
        self.__host     = host
        self.__database = database
    ## End of __init__

    def __open(self):
        try:
            cnx = MySQLdb.connect(self.__host, self.__user, self.__password, self.__database)
            self.__connection = cnx
            self.__cursor     = cnx.cursor()
        except MySQLdb.Error as e:
            print("Error %d: %s" % (e.args[0],e.args[1]))
    ## End def __open

    def __close(self):
        self.__cursor.close()
        self.__connection.close()
    ## End def __close

    def save_to_db(self):
        sql = "INSERT INTO feeding (time) VALUES (CURRENT_TIMESTAMP())"
        self.__open()
        self.__cursor.execute(sql)
        self.__connection.commit()
        self.__close()
    ## End def save_to_db

    def select_from_db(self):
        sql = "SELECT * FROM feeding WHERE DATE(time) = CURRENT_DATE"
        self.__open()
        self.__cursor.execute(sql)
        results = self.__cursor.rowcount
        self.__close()
        return results
    ## End def select_from_db