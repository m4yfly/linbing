由于较多人搭建时失败了，加上之前写的代码有点烂，所以我打算抽时间重新修改下，添加备注，生成docker镜像，这段时间如有不及时回复，还请见谅

# 临兵漏洞扫描系统

> 本系统是对目标进行漏洞扫描的一个系统,前端采用vue技术,后端采用flask.核心原理是扫描主机的开放端口情况,然后根据端口情况逐个去进行poc检测,poc有110多个,包含绝大部分的中间件漏洞,本系统的poc皆来源于网络或在此基础上进行修改,在centons7环境下使用nginx和uwsgi部署,部署起来可能有点麻烦,烦请多点耐心

## 安装python3依赖库

> pip3 install -r requirements.txt

## 打包vue源代码(进入到vue_src目录下)

> npm run build(有打包好的,即vue文件夹,可直接使用,自行打包需要安装node和vue,参考<https://www.runoob.com/nodejs/nodejs-install-setup.html>, <https://www.runoob.com/vue2/vue-install.html>)

## 部署

### nmap

#### 安装nmap

> yum install -y nmap

### masscan

#### 安装masscan

> yum install -y masscan

### nginx

#### 安装nginx

> yum install -y nginx

#### 启动nginx

> systemctl start nginx

#### 开机自启动nginx

> systemctl enable nginx

#### 添加nginx用户

> useradd -s /sbin/nologin -M nginx

#### 配置

> 配置文件已配置好,可以直接使用,可以根据自己的需求修改文件路径及端口.
> 在/etc/nginx/conf.d目录下放入flask.conf和vue.conf文件
> 在/etc/nginx目录下放入nginx.conf文件
> conf配置文件中有注释
> 把vue目录移到/usr/share/nginx/html中

### mariadb

#### 安装mariadb

> yum install -y mariadb-server

#### 启动mariadb

> systemctl start mariadb

#### 设置mariadb开机自启动

> systemctl enable mariadb

#### 进行数据库配置(如设置密码等)

> mysql_secure_installation(具体步骤略去,可参考<https://www.cnblogs.com/yhongji/p/9783065.html>)
> 配置数据库密码后需要在flask/app文件夹下的mysql文件中配置连接maridab数据库的用户名,密码等信息

### 邮件

> 我使用的是QQ邮箱发送的邮件,需要授权码,需要自行到flask/app/sendmail.py文件中去设置,参考<https://blog.csdn.net/Momorrine/article/details/79881251>


### uwsgi

#### 安装uwsgi

> yum install -y libpq-dev

> yum install -y python3-dev

> yum install -y uwsgi

> yum install uwsgi-plugin-python3

#### 配置uwsgi

> 把uwsgi.ini文件放到flask文件夹的根目录下((配置文件中有注释))

#### 启动uwsgi

> 进入到/root/flask/目录下,uwsgi --ini uwsgi.ini(uwsgi文件的路径)

## 访问

> 访问<http://yourip:11000/login>即可

## 致谢

> 感谢vulhub项目提供的靶机环境:<https://github.com/vulhub/vulhub>,还有<https://hub.docker.com/r/2d8ru/struts2>

> POC也参考了很多项目:<https://github.com/Xyntax/POC-T>、<https://github.com/ysrc/xunfeng>、<https://github.com/se55i0n/DBScanner>、<https://github.com/vulscanteam/vulscan>

> 感谢师傅pan带我入门安全,也感谢呆橘同学在vue上对我的指导

## 免责声明

工具仅用于安全研究以及内部自查，禁止使用工具发起非法攻击，造成的后果使用者负责
