#!/usr/bin/env python3

import nmap
import masscan
from app.mysql import Mysql_db

class Port_Scan():
    def __init__(self):
        self.mysqldb = Mysql_db()

    def nmap_scan(self, username, target, scan_ip, min_port, max_port):
        scan_list = []
        print('Nmap starting.....')
        self.mysqldb.update_scan(username, target, '开始扫描端口')
        nm = nmap.PortScanner()
        arguments = '-p %s-%s -sS -sV -Pn -T4 --open' % (min_port, max_port)
        nm.scan(hosts = scan_ip, arguments = arguments)
        try:
            for host in nm.all_hosts():
                for nmap_proto in nm[host].all_protocols():
                    lport = nm[host][nmap_proto].keys()
                    lport = sorted(lport)
                    for nmap_port in lport:
                        scan_list.append(str(host) + ':' + str(nmap_port))
            print('Nmap scanned.....')
            self.mysqldb.update_scan(username, target, '端口扫描结束')
        except Exception as e:
            print(e)
            pass
        finally:
            pass
        return scan_list

    def masscan_scan(self, username, target, scan_ip, min_port, max_port, rate):
        scan_list = []
        print('Masscan starting.....\n')
        self.mysqldb.update_scan(username, target, '开始扫描端口')
        masscan_scan = masscan.PortScanner()
        masscan_scan.scan(hosts = scan_ip, ports = '%s-%s' % (min_port, max_port), arguments = '-sS -Pn -n --randomize-hosts -v --send-eth --open --rate %s' % (rate))
        try:
            for host in masscan_scan.all_hosts:
                for masscan_proto in masscan_scan[host].keys():
                    for masscan_port in masscan_scan[host][masscan_proto].keys():
                        scan_list.append(str(host) + ':' + str(masscan_port))
            print('Masscan scanned.....\n')
            self.mysqldb.update_scan(username, target, '端口扫描结束')
        except Exception as e:
            print(e)
            pass
        finally:
            pass
        return scan_list

if __name__ == '__main__':
    port_scan = port_scan()
    port_scan.masscan_scan('127.0.0.1')