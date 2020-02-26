#!/usr/bin/env python3

import time
import hashlib
import pymysql
import threading
from queue import Queue

class Mysql_db():

    __v=None

    def __init__(self, host = "127.0.0.1", port = 3306, user = "root", passwd = "123456", charset = "utf8" , maxconn = 10):
        self.host, self.port, self.user, self.passwd, self.charset = host, port, user, passwd, charset

    def get_conn(self):
        try:
            conn=pymysql.connect(host = self.host, port = self.port, user = self.user, passwd = self.passwd, db = 'linbing', charset = self.charset)
            conn.autocommit(True)
            return conn
        except Exception as e:
            print(e)
            pass

    def create_database(self,database):
        flag = 0
        sql = "create database linbing character set utf8 collate utf8_general_ci" 
        try:
            conn = pymysql.connect(host = self.host, port = self.port, user = self.user, passwd = self.passwd, charset = self.charset)
            cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute("show databases") 
            result = cursor.fetchall()
            for i in range(len(result)):
                if 'linbing' == result[i]['Database']:
                    flag = 1
            if flag == 0:
                cursor.execute(sql)
        except Exception as e:
            print(e)
            return None
        finally:
            cursor.close()
            conn.close()

    def create_user(self):
        flag = 0
        sql = "create table user (id integer auto_increment primary key, username varchar(128) unique, token varchar(128) unique, email varchar(128) unique, password varchar(128), user_id varchar(128), access varchar(128), avatar varchar(128)) engine = innodb default  charset = utf8;"
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute("show tables")
            result = cursor.fetchall()
            for i in range(len(result)):
                if 'user' == result[i]['Tables_in_linbing']:
                    flag = 1
            if flag == 0:
                try:
                    cursor.execute(sql)
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)
            return None
        finally:
            cursor.close()
            self.close_conn

    def create_target(self):
        flag = 0
        sql = "create table target (id integer auto_increment primary key, username varchar(50), target varchar(50), description varchar(255), create_time varchar(50), scan_time varchar(50), scan_schedule varchar(50), vulner_number varchar(50), scan_status varchar(50), trash_flag varchar(50), scanner varchar(50), min_port varchar(50), max_port varchar(50), rate varchar(50)) engine = innodb default charset = utf8;"
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute("show tables")
            result = cursor.fetchall()
            for i in range(len(result)):
                if 'target'  == result[i]['Tables_in_linbing']:
                    flag = 1
            if flag == 0:
                cursor.execute(sql)
            return 1
        except Exception as e:
            pass
            return 0
        finally:
            cursor.close()
            self.close_conn

    def create_vulnerability(self):
        flag = 0
        sql = "create table vulnerability (id integer auto_increment primary key, username varchar(50), target varchar(50), description varchar(255), ip_port varchar(50), vulner_name varchar(50), vulner_descrip varchar(50), trash_flag varchar(50), time varchar(50)) engine = innodb default  charset = utf8;"
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute("show tables")
            result = cursor.fetchall()
            for i in range(len(result)):
                if 'vulnerability'  == result[i]['Tables_in_linbing']:
                    flag = 1
            if flag == 0:
                cursor.execute(sql)
            return 1
        except Exception as e:
            pass
            return 0
        finally:
            cursor.close()
            self.close_conn

    def create_delete_vulnerability(self):
        flag = 0
        sql = "create table delete_vulnerability (id integer auto_increment primary key, username varchar(50), target varchar(50), description varchar(255), ip_port varchar(50), vulner_name varchar(50), vulner_descrip varchar(50), trash_flag varchar(50), time varchar(50)) engine = innodb default  charset = utf8;"
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute("show tables")
            result = cursor.fetchall()
            for i in range(len(result)):
                if 'delete_vulnerability'  == result[i]['Tables_in_linbing']:
                    flag = 1
            if flag == 0:
                cursor.execute(sql)
            return 1
        except Exception as e:
            pass
            return 0
        finally:
            cursor.close()
            self.close_conn

    def create_delete_target(self):
        flag = 0
        sql = "create table delete_target (id integer auto_increment primary key, username varchar(50), target varchar(50), description varchar(255), create_time varchar(50), vulner_number varchar(50), scan_status varchar(50), scanner varchar(50), min_port varchar(50), max_port varchar(50), rate varchar(50)) engine = innodb default  charset = utf8;"
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute("show tables")
            result = cursor.fetchall()
            for i in range(len(result)):
                if 'delete_target'  == result[i]['Tables_in_linbing']:
                    flag = 1
            if flag == 0:
                cursor.execute(sql)
            return 1
        except Exception as e:
            pass
            return 0
        finally:
            cursor.close()
            self.close_conn

    def query(self, query_str):
        try:
            if query_str['type'] == 'username':
                sql = "select username from user "
            elif query_str['type'] == 'email':
                sql = "select email from user "
            else:
                sql = "select target from target where  username = '%s' and  (trash_flag = 0 or trash_flag = 1)" % (query_str['username'])
            conn = self.get_conn()
            cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(sql)
            result = cursor.fetchall()
            query_list = []
            for item in result:
                query_list.append(item[query_str['type']])
            if query_str['type'] == 'target':
                if query_str['data'] in query_list:
                    return 'Z10010'
            else:
                if query_str['data'] in query_list:
                    if query_str['type'] == 'username':
                        return 'Z1006'
                    else:
                        return 'Z1007'
            return 'Z1000'
        except Exception as e:
            print(e)
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def register(self, username, token, email, password, user_id, access, avatar):
        """
            执行无返回结果集的sql，主要有insert update delete
        """
        sql = "insert into user (username, token, email, password, user_id, access, avatar) values ('%s', '%s', '%s', '%s', '%s', '%s', '%s')" %  (username, token, email, password, user_id, access, avatar)
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(sql)
            return 'Z1000'
        except Exception as e:
            print(e)
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def login(self, username):
        """
            执行无返回结果集的sql，主要有insert update delete
        """
        sql = "select password, token from user where username = '%s' " % (username)
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(sql) 
            result = cursor.fetchone()
            return result
        except Exception as e:
            print(e)
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def userinfo(self, token):
        sql = "select username, email, user_id, access, avatar from user where token = '%s' " % (token)
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(sql) 
            result = cursor.fetchone()
            return result
        except Exception as e:
            print(e)
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def changps(self, data):
        sql = "update user set password = '%s' where %s = '%s'" % (data['password'], data['type'], data['type_data'])
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(sql) 
            return 'Z1000'
        except Exception as e:
            print(e)
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def username(self, query_str):
        sql = "select username from user where %s = '%s' " % (query_str['type'],query_str['data'])
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(sql) 
            result = cursor.fetchone()
            return result
        except Exception as e:
            print(e)
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def save_target(self, username, target, description):
        datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        sql =  "insert target (username, target, description, create_time, scan_time, scan_schedule, vulner_number, scan_status, trash_flag, scanner, min_port, max_port, rate) values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (username, target, description, datetime, '0', '未开始', '0', '0', '0', 'nmap', '1', '65535', '1000')
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(sql)
            print(datetime)
            return 'Z1000'
        except Exception as e:
            print(e)
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def scan_set(self, username, target, scanner, min_port, max_port, rate):
        sql =  "update target set scanner = '%s', min_port = '%s', max_port = '%s', rate = '%s' where username = '%s' and target = '%s'" % (scanner, min_port, max_port, rate, username, target)
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(sql)
            return 'Z1000'
        except Exception as e:
            print(e)
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def get_scan(self, username, target):
        sql = "select scanner, min_port, max_port, rate from target where username = '%s' and target = '%s' " % (username, target)
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(sql) 
            result = cursor.fetchone()
            return result
        except Exception as e:
            print(e)
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def save_scan(self, username, target):
        datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        sql =  "update target set scan_time = '%s', scan_status = '%s', scan_schedule = '%s' where username = '%s' and target = '%s'" % (datetime, '1', '准备开始扫描', username, target)
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(sql)
            return 'Z1000'
        except Exception as e:
            print(e)
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def update_scan(self, username, target, scan_schedule):
        sql =  "update target set scan_schedule = '%s' where username = '%s' and target = '%s'" % (scan_schedule, username, target)
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(sql)
            return 'Z1000'
        except Exception as e:
            print(e)
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def save_vulnerability(self, username, target, description, ip_port, vulner_name, vulner_descrip):
        datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        sql = "insert vulnerability (username, target, description, ip_port, vulner_name, vulner_descrip, trash_flag, time) values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (username, target, description, ip_port, vulner_name, vulner_descrip, '0', datetime)
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(sql)
            return 'Z1000'
        except Exception as e:
            print(e)
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def update_vulnerability(self, username, target, ip_port, vulner_name):
        datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        sql = "update vulnerability set time = '%s' where username = '%s' and target = '%s' and ip_port = '%s', vulner_name = '%s' " % (datetime, username, target, ip_port, vulner_name)
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(sql)
            return 'Z1000'
        except Exception as e:
            print(e)
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def get_vulnerability(self, username, target, ip_port, vulner_name):
        sql = "select * from vulnerability where username = '%s' and target = '%s' and ip_port = '%s' and vulner_name = '%s' " % (username, target, ip_port, vulner_name)
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(sql)
            result = cursor.fetchone()
            return result
        except Exception as e:
            print(e)
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def edit(self, username, old_target, old_description, new_target, new_description):
        sql = "update ignore target set target ='%s', description = '%s' where username = '%s' and target ='%s', description = '%s'" % (new_target, new_description, username, old_target, old_description)
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(sql)
            return 'Z1000'
        except Exception as e:
            print(str(e))
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def target_list(self, username, pagenum, pagesize, flag):
        start = (int(pagenum)-1) * int(pagesize)
        pagesize = int (pagesize)
        trash_sql = "select target, description, create_time, scan_time, vulner_number, scan_schedule from target where username = '%s' and trash_flag = '%s' limit %s, %s" % (username, flag, start, pagesize)
        trash_total_sql = "select count(0) from target where username = '%s' and trash_flag = '%s' " % (username, flag)
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(trash_total_sql)
            total_result = cursor.fetchone()['count(0)']
            cursor.execute(trash_sql)
            result = cursor.fetchall()
            data = {}
            data['total'] = total_result
            data ['result'] = result
            return data
        except Exception as e:
            print(e)
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def scan_list(self, username, pagenum, pagesize, flag):
        start = (int(pagenum)-1) * int(pagesize)
        pagesize = int (pagesize)
        scan_sql = "select target, description, create_time, scan_time, vulner_number, scan_schedule from target where username = '%s' and trash_flag = '%s' and scan_status = '%s' limit %s, %s" % (username, flag, '1', start, pagesize)
        scan_total_sql = "select count(0) from target where username = '%s' and trash_flag = '%s' and scan_status = '%s' " % (username, flag, '1')
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(scan_total_sql)
            total_result = cursor.fetchone()['count(0)']
            cursor.execute(scan_sql)
            result = cursor.fetchall()
            data = {}
            data['total'] = total_result
            data ['result'] = result
            return data
        except Exception as e:
            print(e)
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def vulner_list(self, username, target, pagenum, pagesize):
        start = (int(pagenum)-1) * int(pagesize)
        pagesize = int (pagesize)
        sql = "select id, target, description, ip_port, vulner_name, vulner_descrip, time from vulnerability where username = '%s' and target = '%s' and trash_flag = '%s' limit %s, %s" % (username, target, '0', start, pagesize)
        total_sql = "select count(0) from vulnerability where username = '%s' and target = '%s' and trash_flag = '%s' " % (username, target, '0')
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(total_sql)
            total_result = cursor.fetchone()['count(0)']
            cursor.execute(sql)
            result = cursor.fetchall()
            data = {}
            data['total'] = total_result
            data ['result'] = result
            return data
        except Exception as e:
            print(e)
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def all_vulner_list(self, username, pagenum, pagesize, flag):
        start = (int(pagenum)-1) * int(pagesize)
        pagesize = int (pagesize)
        sql = "select id, target, description, ip_port, vulner_name, vulner_descrip, time from vulnerability where username = '%s' and trash_flag = '%s' limit %s, %s" % (username, flag['data'], start, pagesize)
        total_sql = "select count(0) from vulnerability where username = '%s' and trash_flag = '%s' " % (username, flag['data'])
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(total_sql)
            total_result = cursor.fetchone()['count(0)']
            cursor.execute(sql)
            result = cursor.fetchall()
            data = {}
            data['total'] = total_result
            data ['result'] = result
            return data
        except Exception as e:
            print(e)
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def set_flag(self, username, target, flag):
        if flag['type'] == 'target':
            sql = "update target set trash_flag ='%s'  where username = '%s' and target = '%s'" % (flag['data'], username, target)
            vuln_sql = "update vulnerability set trash_flag ='%s' where username = '%s' and target = '%s'" % (flag['data'], username, target)
        else:
            vuln_sql = "update vulnerability set trash_flag ='%s' where id = '%s'" % (flag['data'], flag['id'])
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            if flag['type'] == 'target':
                cursor.execute(sql)
                cursor.execute(vuln_sql)
            else:
                cursor.execute(vuln_sql)
            return 'Z1000'
        except Exception as e:
            print(e)
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def change_avatar(self, username, imagename):
        """
            用来修改头像的图片
        """
        sql = "update user set avatar ='%s'  where username = '%s' " % (imagename, username,)
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(sql) 
            return 'Z1000'
        except Exception as e:
            print(e)
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def delete(self, username, target, flag):
        if flag['type'] == 'target':
            query_sql = "select * from target where username = '%s' and target = '%s'" % (username, target)
            del_sql = "delete from target where username = '%s' and target = '%s'" % (username, target)
        else:
            query_sql = "select * from vulnerability where id = '%s'" % (flag['id'])
            del_sql = "delete from vulnerability where id = '%s'" % (flag['id'])
        try:
            conn=self.get_conn()
            cursor=conn.cursor(cursor=pymysql.cursors.DictCursor)
            cursor.execute(query_sql)
            result = cursor.fetchall()
            if flag['type'] == 'target':
                save_sql = "insert delete_target (username, target, description, create_time, vulner_number, scan_status, scanner, min_port, max_port, rate) values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (result[0]['username'], result[0]['target'], result[0]['description'], result[0]['create_time'], result[0]['vulner_number'], result[0]['scan_status'], result[0]['scanner'], result[0]['min_port'], result[0]['max_port'], result[0]['rate'])
            else:
                save_sql = "insert delete_vulnerability (username, target, description, ip_port, vulner_name, vulner_descrip, time) values ('%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (result[0]['username'], result[0]['target'], result[0]['description'], result[0]['ip_port'], result[0]['vulner_name'], result[0]['vulner_descrip'], result[0]['time'])
            cursor.execute(save_sql)
            cursor.execute(del_sql)
            return 'Z1000'
        except Exception as e:
            print(e)
            return 'Z1001'
        finally:
            cursor.close()
            self.close_conn

    def close_conn(self, conn):
        try:
            conn.close()
        except Exception as e:
            print(e)
            pass

if __name__ == '__main__':
    mysqldb = Mysql_db()
    mysqldb.create_database('linbing')
    mysqldb.create_user()
    mysqldb.create_target()
    mysqldb.create_vulnerability()
    mysqldb.create_delete_vulnerability()
    mysqldb.create_delete_target()
    #mysqldb.save_vulnerability('username', 'target', 'description', 'ip_port', 'vulner_name', 'vulner_descrip')
    print(mysqldb.get_vulnerability('P09GwBPc/r51GCnmi1YBfA==', 'Ka+lw2Vz4dWAvs4SIP80ZA==s', '3DiNb7CEaG8LhGyRIXCN9w==', '3DiNb7CEaG8LhGyRIXCN9w=='))