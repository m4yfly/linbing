# 底层为centos
FROM centos:7
MAINTAINER taomujian

# 更新yum源及安装依赖
RUN mv /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.backup \
&& curl -o /etc/yum.repos.d/epel.repo http://mirrors.aliyun.com/repo/epel-7.repo \
&& curl -o /etc/yum.repos.d/CentOS-Base.repo https://mirrors.aliyun.com/repo/Centos-7.repo \
&& sed -i -e '/mirrors.cloud.aliyuncs.com/d' -e '/mirrors.aliyuncs.com/d' /etc/yum.repos.d/CentOS-Base.repo \
&& yum clean all && yum makecache && yum update -y && yum install -y epel-release && yum install -y mariadb-server && yum install -y gcc \
&& yum install -y nmap && yum install -y masscan && yum install -y nginx && yum install -y initscripts && yum install -y postgresql-devel \
&& yum install -y python3-devel && yum install -y uwsgi && yum install -y uwsgi-plugin-python3 && mkdir /root/flask && mkdir /var/log/uwsgi

# 设置相关环境变量
ENV MARIADB_USER root
ENV MARIADB_PASS 1234567
ENV LC_ALL en_US.UTF-8
# 暴露端口
EXPOSE 3306 11000

# 复制本地文件到docker 中
ADD db_init.sh /root/db_init.sh
ADD nginx/flask.conf /etc/nginx/conf.d/flask.conf
ADD nginx/vue.conf /etc/nginx/conf.d/vue.conf
ADD nginx/nginx.conf /etc/nginx/nginx.conf
ADD vue /usr/share/nginx/html/vue
ADD flask /root/flask
ADD flask/uwsgi.ini /root/flask/uwsgi.ini
ADD run.sh /run.sh

RUN chmod 775 /root/db_init.sh && /root/db_init.sh && pip3 install -r /root/flask/requirements.txt \
&& chmod 775 /run.sh && cp /run.sh /etc/profile.d/run.sh && cp /run.sh /etc/init.d/run.sh
