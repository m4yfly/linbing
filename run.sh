#!/bin/bash

# chkconfig: 2345 10 90 
# description: myservice ....

nginx
nohup mysqld_safe &
uwsgi --ini /root/flask/uwsgi.ini