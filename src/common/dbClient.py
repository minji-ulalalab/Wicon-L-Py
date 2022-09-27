'''
Created on 2022. 03. 13.

@author: sg.an
'''
import traceback, time
import sqlite3

class BACKUPDBCLIENT:
    conf = None
    exh = None
    logger = None
    _db_conn = None
    _db_cur = None
    
    ## 생성자
    def __init__(self, resources):
        self.conf = resources["conf"]
        self.exh = resources["exh"]
        self.logger = resources["logger"]

    def db_connect(self):
        self._db_conn = sqlite3.connect(self.conf.backup_dir + "backup.db")
        self._db_cur = self._db_conn.cursor()

    def db_read_data(self):
        self._db_cur.execute("select id from backup order by data_time, id limit 1")
        min_id = self._db_cur.fetchall()
        print(f"min_id : {min_id}")
        
        self._db_cur.execute("select packet from backup order by data_time, id limit 10")
        rows = self._db_cur.fetchall()
        print(f"rows : {rows}")

        return rows

    def db_read_and_delete_data(self):
        self._db_cur.execute("select id from backup order by data_time, id limit 1")
        min_id = self._db_cur.fetchall()
        print(f"min_id : {min_id}")
        
        self._db_cur.execute("select packet from backup order by data_time, id limit 10")
        rows = self._db_cur.fetchall()
        print(f"rows : {rows}")

        self._db_cur.execute("delete from backup order by data_time, id limit 10")

        return rows

    # 86,400개 제한
    # 86,400개를 넘으면 1부터 덮어서 쓸 것
    # 1부터 다시 덮어쓸때 latest_id가 가장 최근의 id
    # 1부터 덮어서 쓰기 전이라면 max_id가 가장 최근의 id
    def db_write_data(self, packet):
        
        self._db_cur.execute("select id from backup order by data_time desc, id desc limit 1")
        latest_id = self._db_cur.fetchall()
        print(f"latest_id : {latest_id}")
        self.logger.debug(f"latest_id : {latest_id}")
        self._db_cur.execute("select id from backup order by id desc limit 1")
        max_id = self._db_cur.fetchall()
        print(f"max_id : {max_id}")
        self.logger.debug(f"max_id : {max_id}")

        # db가 비어있을 때
        if( (len(latest_id) == 0) and (len(max_id) == 0) ):
            query = "insert into backup (id, packet) values (1,'%s')" %(packet)
        # 같다는 것은 86,400개를 넘지 않았다는 것
        elif(latest_id[0][0] == max_id[0][0]):
            if(latest_id[0][0] < 100):
                query = "insert into backup (id, packet) values (%d, '%s')" %(latest_id[0][0] + 1, packet)
            else:
                query = "select id from backup where id = 1"
                self._db_cur.execute(query)
                is_id = self._db_cur.fetchall()
                if(len(is_id)==0):
                    query = "insert into backup (id, packet) values (1, '%s')" %(packet)
                else:
                    query = "update backup set packet='%s', data_time = datetime('now') where id = 1" % (packet)            
        # 86,400개를 넘었음
        elif(latest_id[0][0] < max_id[0][0]):
            query = "select id from backup where id = %d" % (latest_id[0][0] + 1)
            self._db_cur.execute(query)
            is_id = self._db_cur.fetchall()
            if(len(is_id)==0):
                query = "insert into backup (id, packet) values (%d, '%s')" %(latest_id[0][0] + 1, packet)
            else:
                query = "update backup set packet='%s', data_time = datetime('now') where id = %d" % (packet, latest_id[0][0] + 1)
        
        print(query)
        self._db_cur.execute(query)



    def db_commit(self):
        self._db_conn.commit()

    def db_close(self):
        self._db_conn.close()
