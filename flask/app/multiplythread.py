#/usr/bin/python3

import os
import time
import sched
import threading
import importlib
from app.scan import Port_Scan
from app.mysql import Mysql_db
from app.aes import Aes_Crypto

class Multiply_Thread():
    def __init__(self):
        self.port_scan = Port_Scan()
        self.mysqldb = Mysql_db()
        self.aes_crypto = Aes_Crypto()
        self.plugin_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"plugins")
        if not os.path.isdir(self.plugin_path):
            raise EnvironmentError
        self.items = os.listdir(self.plugin_path)

    def async_exe(self, func, args = None, kwargs = None, delay = 0):
        """异步执行方法
        
        :param func: 待执行方法
        :param args: 方法args参数
        :param kwargs: 方法kwargs参数
        :param delay: 执行延迟时间
        :return: 执行线程对象
        """
        args = args or ()
        kwargs = kwargs or {}
        def tmp():
            self.run(*args, **kwargs)
        scheduler = sched.scheduler(time.time, time.sleep)
        scheduler.enter(delay, 10, tmp, ())
        thread = threading.Thread(target = scheduler.run)
        thread.start()
        return thread

    def run(self, *args, **kwargs):
        scan_set = self.mysqldb.get_scan(kwargs['username'], kwargs['target'])
        if scan_set['scanner'] == 'nmap':
            scan_list = self.port_scan.nmap_scan(kwargs['username'], kwargs['target'], kwargs['scan_ip'], scan_set['min_port'], scan_set['max_port'])
        else:
            scan_list = self.port_scan.masscan_scan(kwargs['username'], kwargs['target'], kwargs['scan_ip'], scan_set['min_port'], scan_set['max_port'], scan_set['rate'])
        self.mysqldb.update_scan(kwargs['username'], kwargs['target'], '开始POC检测')
        for ip_port in scan_list:
            for item in self.items:
                poc_path = os.path.join(self.plugin_path, item)
                if '.py' not in poc_path:
                    poc_items = os.listdir(poc_path)
                    for poc_item in poc_items:
                        if poc_item.endswith(".py") and not poc_item.startswith('__'):
                            plugin_name = poc_item[:-3]
                            module = importlib.import_module('app.plugins.' + item + '.' + plugin_name)
                            try:
                                class_name = plugin_name + '_BaseVerify'
                                url = 'http://' + ip_port
                                get_class = getattr(module, class_name)(url)
                                result = get_class.run()
                                if result:
                                    if not self.mysqldb.get_vulnerability(kwargs['username'], kwargs['target'], self.aes_crypto.encrypt(ip_port), self.aes_crypto.encrypt(plugin_name)):
                                        self.mysqldb.save_vulnerability(kwargs['username'], kwargs['target'], self.aes_crypto.encrypt(plugin_name), self.aes_crypto.encrypt(ip_port), self.aes_crypto.encrypt(plugin_name), self.aes_crypto.encrypt(plugin_name))
                                    else:
                                        self.mysqldb.update_vulnerability(kwargs['username'], kwargs['target'], self.aes_crypto.encrypt(ip_port), self.aes_crypto.encrypt(plugin_name))
                                else:
                                    pass
                            except:
                                pass
                        else:
                            continue
        self.mysqldb.update_scan(kwargs['username'], kwargs['target'], '扫描结束')

if __name__ == '__main__':
    multiply_thread = Multiply_Thread()
    data = {
        'username': '127.0.0.1',
        'target': 'http://baidu.com'
    }
    multiply_thread.async_exe(multiply_thread.run, (), data)