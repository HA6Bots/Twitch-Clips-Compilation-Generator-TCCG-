import mysql.connector
from mysql.connector import pooling
from datetime import date
import pickle
import settings
current_date = date.today()
connection_pool = None

def startDatabase():
    beginDatabaseConnection()
    initDatabase()

def initDatabase():
    global connection_pool
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()
    cursor.execute("SET sql_notes = 0; ")
    cursor.execute("CREATE SCHEMA IF NOT EXISTS `twitchclipdb` ;")
    cursor.execute("USE twitchclipdb;")
    cursor.execute("SET sql_notes = 0;")
    cursor.execute("set global max_allowed_packet=67108864;")
    cursor.execute("create table IF NOT EXISTS clip_bin (clip_num int NOT NULL AUTO_INCREMENT, PRIMARY KEY (clip_num), game varchar(140), clip_id int, date varchar(20), status varchar(100), clipwrapper BLOB);")
    cursor.execute("create table IF NOT EXISTS saved_games (num int NOT NULL AUTO_INCREMENT, PRIMARY KEY (num), game_name varchar(70), game_id varchar(20));")
    cursor.execute("SET sql_notes = 1; ")

def beginDatabaseConnection():
    global connection_pool
    connection_pool = pooling.MySQLConnectionPool(
    pool_size=32,
        pool_reset_session=True,
      host=settings.databasehost,
      user=settings.databaseuser,
      passwd=settings.databasepassword,
    )
    print("Started database connection")
    
def checkClipID():
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()
    cursor.execute("USE twitchclipdb;")
    query = f"SELECT clip_id FROM clip_bin;"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    connection_object.close()
    list(result)
    res = [''.join(i) for i in result]
    return res

def addFoundClip(twitchclip, game):
    global connection_pool
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()
    cursor.execute("USE twitchclipdb;")

    id = twitchclip.id
    twitchclip = pickle.dumps(twitchclip)
    query = "INSERT INTO clip_bin(clip_id, date, game, status, clipwrapper) VALUES(%s, %s, %s, 'FOUND', %s);"
    args = (id, current_date, game, twitchclip)

    cursor.execute(query, args)

    connection_object.commit()
    cursor.close()
    connection_object.close()

def getFoundGameClips(game, limit):
    global connection_pool
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()
    cursor.execute("USE twitchclipdb;")

    query = "select * FROM clip_bin WHERE game = %s and status = 'FOUND' LIMIT %s;"
    args = (game,limit)

    cursor.execute(query, args)
    result = cursor.fetchall()
    results = []
    for res in result:
        results.append(pickle.loads(res[5]))
    connection_object.commit()
    cursor.close()
    connection_object.close()
    return results




def addUsedClipID(clip_id):
    global connection_pool
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()
    cursor.execute("USE twitchclipdb;")
    query = f"INSERT INTO clip_bin(`clip_id`, `date`) VALUES('{clip_id}', '{current_date}');"
    cursor.execute(query)
    connection_object.commit()
    cursor.close()
    connection_object.close()
    
def addGameToDatabase(game_name, game_id):
    global connection_pool
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()
    cursor.execute("USE twitchclipdb;")
    query = f"INSERT INTO saved_games(`game_name`, `game_id`) VALUES('{game_name}', '{game_id}');"
    cursor.execute(query)
    connection_object.commit()
    cursor.close()
    connection_object.close()
    
def getAllSavedGames():
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()
    cursor.execute("USE twitchclipdb;")
    query = "SELECT game_name FROM saved_games;"
    cursor.execute(query)
    result = cursor.fetchall()
    results = []
    for res in result:
        results.append(res)
    cursor.close()
    connection_object.close()
    return results

def getGameClipCount(game):
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()
    cursor.execute("USE twitchclipdb;")
    query = "SELECT COUNT(*) FROM clip_bin WHERE game = %s"
    args = (game,)
    cursor.execute(query, args)
    result = cursor.fetchall()
    results = []
    for res in result:
        results.append(res)
    cursor.close()
    connection_object.close()
    return results

def getGameClipCountByStatus(game,status):
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()
    cursor.execute("USE twitchclipdb;")
    query = "SELECT COUNT(*) FROM clip_bin WHERE game = %s and status = %s"
    args = (game,status)
    cursor.execute(query, args)
    result = cursor.fetchall()
    results = []
    for res in result:
        results.append(res)
    cursor.close()
    connection_object.close()
    return results

def getGameClipsByStatusLimit(game, status, limit):
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()
    cursor.execute("USE twitchclipdb;")
    query = "SELECT * FROM clip_bin WHERE game = %s and status = %s LIMIT %s;"
    args = (game,status, limit)
    cursor.execute(query, args)
    result = cursor.fetchall()
    results = []
    for res in result:
        results.append(pickle.loads(res[5]))
    cursor.close()
    connection_object.close()
    return results

def getGameClipsByStatusWithoutClips(game, status, limit, clips):
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()
    cursor.execute("USE twitchclipdb;")
    query = "SELECT * FROM clip_bin WHERE game = %s and status = %s" \
            "and clip_id not in (%s)" \
            " LIMIT %s;"

    old_id_list = []
    for clip in clips:
        old_id_list.append(str(clip.id))

    args = (game,status, ",".join(old_id_list), limit)
    cursor.execute(query, args)
    result = cursor.fetchall()
    results = []
    for res in result:
        results.append(pickle.loads(res[5]))
    cursor.close()
    connection_object.close()
    return results


def getGameClipsByStatusWithoutIds(game, status, limit, idlist):
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()
    cursor.execute("USE twitchclipdb;")
    format_strings = ','.join(["%s"] * len(idlist))

    query = f"SELECT * FROM clip_bin WHERE game = '{game}' and status = '{status}'" \
            f" and clip_id not in ({format_strings})" \
            f" LIMIT {int(limit)};"

    cursor.execute(query, tuple(idlist))
    result = cursor.fetchall()
    results = []
    for res in result:
        results.append(pickle.loads(res[5]))
    cursor.close()
    connection_object.close()
    return results

def getGameClipsByIds(idlist):
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()
    cursor.execute("USE twitchclipdb;")
    format_strings = ','.join(["%s"] * len(idlist))

    query = f"SELECT * FROM clip_bin WHERE" \
            f" clip_id in ({format_strings});" \

    cursor.execute(query, tuple(idlist))
    result = cursor.fetchall()
    results = []
    for res in result:
        clip_id = res[2]
        wrapper = pickle.loads(res[5])
        results.append((clip_id, wrapper))
    cursor.close()
    connection_object.close()
    return results


def getClipById(id):
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()
    cursor.execute("USE twitchclipdb;")
    query = "SELECT clipwrapper FROM clip_bin WHERE clip_id = %s;"
    args = (id, )
    cursor.execute(query, args)
    result = cursor.fetchall()
    results = []
    for res in result:
        results.append(pickle.loads(res[0]))
    cursor.close()
    connection_object.close()
    return results[0]

def getClipsByStatus(status):
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()
    cursor.execute("USE twitchclipdb;")
    query = "SELECT clipwrapper FROM clip_bin WHERE status = %s;"
    args = (status, )
    cursor.execute(query, args)
    result = cursor.fetchall()
    results = []
    for res in result:
        results.append(pickle.loads(res[0]))
    cursor.close()
    connection_object.close()
    return results

def getGameClipsByStatus(game, status):
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()
    cursor.execute("USE twitchclipdb;")
    query = "SELECT clipwrapper FROM clip_bin WHERE status = %s and game=%s;"
    args = (status, game)
    cursor.execute(query, args)
    result = cursor.fetchall()
    results = []
    for res in result:
        results.append(pickle.loads(res[0]))
    cursor.close()
    connection_object.close()
    return results


def getAllSavedGameIDs():
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()
    cursor.execute("USE twitchclipdb;")
    query = "SELECT clip_id FROM clip_bin;"
    cursor.execute(query)
    result = cursor.fetchall()
    results = []
    for res in result:
        results.append(res)
    cursor.close()
    connection_object.close()
    return results

def updateStatus(clip_id, status):
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()
    cursor.execute("USE twitchclipdb;")
    query = "UPDATE clip_bin SET status = %s WHERE clip_id = %s;"
    args = (status, clip_id)
    cursor.execute(query, args)
    connection_object.commit()
    cursor.close()
    connection_object.close()

def updateStatusWithClip(clip_id, status, clip):
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()
    cursor.execute("USE twitchclipdb;")
    query = "UPDATE clip_bin SET status = %s, clipwrapper = %s WHERE clip_id = %s;"
    twitchclip = pickle.dumps(clip)
    args = (status, twitchclip, clip_id)
    cursor.execute(query, args)
    connection_object.commit()
    cursor.close()
    connection_object.close()


def getSavedGame(game_name):
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()
    cursor.execute("USE twitchclipdb;")
    query = f"SELECT game_name FROM clip_bin WHERE game_name = '{game_name}';"
    cursor.execute(query)
    result = cursor.fetchall()
    results = []
    for res in result:
        results.append(res)
    cursor.close()
    connection_object.close()
    return results

def getSavedGameID(game_id):
    connection_object = connection_pool.get_connection()
    cursor = connection_object.cursor()
    cursor.execute("USE twitchclipdb;")
    query = f"SELECT game_name FROM clip_bin WHERE game_name = '{game_id}';"
    cursor.execute(query)
    result = cursor.fetchall()
    results = []
    for res in result:
        results.append(res)
    cursor.close()
    connection_object.close()
    return results
