import json
import os
import platform
import random
import re
import string
import subprocess
import sys
import time
from ipaddress import IPv4Address, ip_address
from pathlib import Path
from stat import S_IXUSR

import dns
import requests
import tenacity
from dns.resolver import Resolver

from app.oneforall.common.database import Database
from app.oneforall.common.domain import Domain
from app.oneforall.common.records import Record, RecordCollection
from app.oneforall.config import settings
from app.oneforall.config.log import logger

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/68.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:61.0) '
    'Gecko/20100101 Firefox/68.0',
    'Mozilla/5.0 (X11; Linux i586; rv:31.0) Gecko/20100101 Firefox/68.0']


def gen_random_ip():
    """
    Generate random decimal IP string
    """
    while True:
        ip = IPv4Address(random.randint(0, 2 ** 32 - 1))
        if ip.is_global:
            return ip.exploded


def gen_fake_header():
    """
    Generate fake request headers
    """
    headers = settings.request_default_headers
    if not isinstance(headers, dict):
        headers = dict()
    if settings.enable_random_ua:
        ua = random.choice(user_agents)
        headers['User-Agent'] = ua
    headers['Accept-Encoding'] = 'gzip, deflate'
    return headers


def get_random_header():
    """
    Get random header
    """
    headers = gen_fake_header()
    if not isinstance(headers, dict):
        headers = None
    return headers


def get_random_proxy():
    """
    Get random proxy
    """
    try:
        return random.choice(settings.request_proxy_pool)
    except IndexError:
        return None


def get_proxy():
    """
    Get proxy
    """
    if settings.enable_request_proxy:
        return get_random_proxy()
    return None


def split_list(ls, size):
    """
    Split list

    :param list ls: list
    :param int size: size
    :return list: result

    >>> split_list([1, 2, 3, 4], 3)
    [[1, 2, 3], [4]]
    """
    if size == 0:
        return ls
    return [ls[i:i + size] for i in range(0, len(ls), size)]


def match_main_domain(domain):
    if not isinstance(domain, str):
        return None
    item = domain.lower().strip()
    return Domain(item).match()


def read_target_file(target):
    domains = list()
    with open(target, encoding='utf-8', errors='ignore') as file:
        for line in file:
            domain = match_main_domain(line)
            if not domain:
                continue
            domains.append(domain)
    sorted_domains = sorted(set(domains), key=domains.index)
    return sorted_domains


def get_from_target(target):
    domains = set()
    if isinstance(target, str):
        if target.endswith('.txt'):
            logger.log('FATAL', 'Use targets parameter for multiple domain names')
            exit(1)
        domain = match_main_domain(target)
        if not domain:
            return domains
        domains.add(domain)
    return domains


def get_from_targets(targets):
    domains = set()
    if not isinstance(targets, str):
        return domains
    try:
        path = Path(targets)
    except Exception as e:
        logger.log('ERROR', e.args)
        return domains
    if path.exists() and path.is_file():
        domains = read_target_file(targets)
        return domains
    return domains


def get_domains(target, targets=None):
    logger.log('DEBUG', f'Getting domains')
    target_domains = get_from_target(target)
    targets_domains = get_from_targets(targets)
    domains = list(target_domains.union(targets_domains))
    if targets_domains:
        domains = sorted(domains, key=targets_domains.index)  # 按照targets原本的index排序
    logger.log('INFOR', f'Get {len(domains)} domains')
    if not domains:
        logger.log('ERROR', f'Did not get a valid domain name')
    logger.log('DEBUG', f'The obtained domains \n{domains}')
    return domains


def check_dir(dir_path):
    if not dir_path.exists():
        logger.log('INFOR', f'{dir_path} does not exist, directory will be created')
        dir_path.mkdir(parents=True, exist_ok=True)


def check_path(path, name, format):
    """
    检查结果输出目录路径

    :param path: 保存路径
    :param name: 导出名字
    :param format: 保存格式
    :return: 保存路径
    """
    filename = f'{name}.{format}'
    default_path = settings.result_save_dir.joinpath(filename)
    if isinstance(path, str):
        path = repr(path).replace('\\', '/')  # 将路径中的反斜杠替换为正斜杠
        path = path.replace('\'', '')  # 去除多余的转义
    else:
        path = default_path
    path = Path(path)
    if not path.suffix:  # 输入是目录的情况
        path = path.joinpath(filename)
    parent_dir = path.parent
    if not parent_dir.exists():
        logger.log('ALERT', f'{parent_dir} does not exist, directory will be created')
        parent_dir.mkdir(parents=True, exist_ok=True)
    if path.exists():
        logger.log('ALERT', f'The {path} exists and will be overwritten')
    return path


def check_format(format, count):
    """
    检查导出格式

    :param format: 传入的导出格式
    :param count: 数量
    :return: 导出格式
    """
    formats = ['csv', 'json', ]
    if format in formats:
        return format
    else:
        logger.log('ALERT', f'Does not support {format} format')
        logger.log('ALERT', 'So use csv format by default')
        return 'csv'


def load_json(path):
    with open(path) as fp:
        return json.load(fp)


def save_db(name, data, module):
    """
    Save request results to database

    :param str  name: table name
    :param list data: data to be saved
    :param str module: module name
    """
    db = Database()
    db.drop_table(name)
    db.create_table(name)
    db.save_db(name, data, module)
    db.close()


def save_data(path, data):
    """
    保存数据到文件

    :param path: 保存路径
    :param data: 待存数据
    :return: 保存成功与否
    """
    try:
        with open(path, 'w', errors='ignore', newline='') as file:
            file.write(data)
            return True
    except TypeError:
        with open(path, 'wb') as file:
            file.write(data)
            return True
    except Exception as e:
        logger.log('ERROR', e.args)
        return False


def remove_data(path):
    """
    删除保存数据的文件

    :param path: 路径
    :return: 删除成功与否
    """
    try:
        path.unlink()
    except Exception as e:
        logger.log('ERROR', e.args)
        return False
    return True


def check_response(method, resp):
    """
    检查响应 输出非正常响应返回json的信息

    :param method: 请求方法
    :param resp: 响应体
    :return: 是否正常响应
    """
    if resp.status_code == 200 and resp.content:
        return True
    logger.log('ALERT', f'{method} {resp.url} {resp.status_code} - '
                        f'{resp.reason} {len(resp.content)}')
    content_type = resp.headers.get('Content-Type')
    if content_type and 'json' in content_type and resp.content:
        try:
            msg = resp.json()
        except Exception as e:
            logger.log('DEBUG', e.args)
        else:
            logger.log('ALERT', msg)
    return False


def mark_subdomain(old_data, now_data):
    """
    标记新增子域并返回新的数据集

    :param list old_data: 之前子域数据
    :param list now_data: 现在子域数据
    :return: 标记后的的子域数据
    :rtype: list
    """
    # 第一次收集子域的情况
    mark_data = now_data.copy()
    if not old_data:
        for index, item in enumerate(mark_data):
            item['new'] = 1
            mark_data[index] = item
        return mark_data
    # 非第一次收集子域的情况
    old_subdomains = {item.get('subdomain') for item in old_data}
    for index, item in enumerate(mark_data):
        subdomain = item.get('subdomain')
        if subdomain in old_subdomains:
            item['new'] = 0
        else:
            item['new'] = 1
        mark_data[index] = item
    return mark_data


def remove_invalid_string(string):
    # Excel文件中单元格值不能直接存储以下非法字符
    return re.sub(r'[\000-\010]|[\013-\014]|[\016-\037]', r'', string)


def export_all_results(path, name, format, datas):
    path = check_path(path, name, format)
    logger.log('ALERT', f'The subdomain result for all main domains: {path}')
    row_list = list()
    for row in datas:
        if 'header' in row:
            row.pop('header')
        if 'response' in row:
            row.pop('response')
        keys = row.keys()
        values = row.values()
        row_list.append(Record(keys, values))
    rows = RecordCollection(iter(row_list))
    content = rows.export(format)
    save_data(path, content)


def export_all_subdomains(alive, path, name, datas):
    path = check_path(path, name, 'txt')
    logger.log('ALERT', f'The txt subdomain result for all main domains: {path}')
    subdomains = set()
    for row in datas:
        subdomain = row.get('subdomain')
        if alive:
            if not row.get('alive'):
                continue
            subdomains.add(subdomain)
        else:
            subdomains.add(subdomain)
    data = '\n'.join(subdomains)
    save_data(path, data)


def export_all(alive, format, path, datas):
    """
    将所有结果数据导出

    :param bool alive: 只导出存活子域结果
    :param str format: 导出文件格式
    :param str path: 导出文件路径
    :param list datas: 待导出的结果数据
    """
    format = check_format(format, len(datas))
    timestamp = get_timestring()
    name = f'all_subdomain_result_{timestamp}'
    export_all_results(path, name, format, datas)
    export_all_subdomains(alive, path, name, datas)


def dns_resolver():
    """
    dns解析器
    """
    resolver = Resolver()
    resolver.nameservers = settings.resolver_nameservers
    resolver.timeout = settings.resolver_timeout
    resolver.lifetime = settings.resolver_lifetime
    return resolver


def dns_query(qname, qtype):
    """
    查询域名DNS记录

    :param str qname: 待查域名
    :param str qtype: 查询类型
    :return: 查询结果
    """
    logger.log('TRACE', f'Try to query {qtype} record of {qname}')
    resolver = dns_resolver()
    try:
        answer = resolver.query(qname, qtype)
    except Exception as e:
        logger.log('TRACE', e.args)
        logger.log('TRACE', f'Query {qtype} record of {qname} failed')
        return None
    else:
        logger.log('TRACE', f'Query {qtype} record of {qname} succeeded')
        return answer


def get_timestamp():
    return int(time.time())


def get_timestring():
    return time.strftime('%Y%m%d_%H%M%S', time.localtime(time.time()))


def get_classname(classobj):
    return classobj.__class__.__name__


def python_version():
    return sys.version


def count_alive(data):
    return len(list(filter(lambda item: item.get('alive') == 1, data)))


def get_subdomains(data):
    return set(map(lambda item: item.get('subdomain'), data))


def set_id_none(data):
    new_data = []
    for item in data:
        item['id'] = None
        new_data.append(item)
    return new_data


def get_filtered_data(data):
    filtered_data = []
    for item in data:
        resolve = item.get('resolve')
        if resolve != 1:
            filtered_data.append(item)
    return filtered_data


def get_sample_banner(headers):
    temp_list = []
    server = headers.get('Server')
    if server:
        temp_list.append(server)
    via = headers.get('Via')
    if via:
        temp_list.append(via)
    power = headers.get('X-Powered-By')
    if power:
        temp_list.append(power)
    banner = ','.join(temp_list)
    return banner


def check_ip_public(ip_list):
    for ip_str in ip_list:
        ip = ip_address(ip_str)
        if not ip.is_global:
            return 0
    return 1


def ip_is_public(ip_str):
    ip = ip_address(ip_str)
    if not ip.is_global:
        return 0
    return 1


def get_process_num():
    process_num = settings.brute_process_num
    if isinstance(process_num, int):
        return min(os.cpu_count(), process_num)
    else:
        return 1


def get_request_count():
    return os.cpu_count() * 10


def uniq_dict_list(dict_list):
    return list(filter(lambda name: dict_list.count(name) == 1, dict_list))


def delete_file(*paths):
    for path in paths:
        try:
            path.unlink()
        except Exception as e:
            logger.log('ERROR', e.args)


@tenacity.retry(stop=tenacity.stop_after_attempt(3))
def check_net():
    logger.log('INFOR', 'Checking Internet environment')
    urls = ['http://www.baidu.com', 'http://www.bing.com',
            'http://www.apple.com', 'http://www.microsoft.com']
    url = random.choice(urls)
    logger.log('INFOR', f'Trying to access {url}')
    session = requests.Session()
    session.trust_env = False
    try:
        rsp = session.get(url, proxies=get_proxy())
    except Exception as e:
        logger.log('ERROR', e.args)
        logger.log('ALERT', 'Can not access Internet, retrying')
        raise tenacity.TryAgain
    if rsp.status_code != 200:
        logger.log('ALERT', f'{rsp.request.method} {rsp.request.url} '
                            f'{rsp.status_code} {rsp.reason}')
        logger.log('ALERT', 'Can not access Internet normally, retrying')
        raise tenacity.TryAgain
    logger.log('INFOR', 'Access to Internet OK')


def check_pre():
    logger.log('INFOR', 'Checking dependent environment')
    implementation = platform.python_implementation()
    version = platform.python_version()
    if implementation != 'CPython':
        logger.log('FATAL', f'OneForAll only passed the test under CPython')
        exit(1)
    if version < '3.6':
        logger.log('FATAL', 'OneForAll requires Python 3.6 or higher')
        exit(1)


def check_env():
    logger.log('INFOR', 'Checking the environment')
    try:
        check_net()
    except Exception as e:
        logger.log('DEBUG', e.args)
        logger.log('FATAL', 'Can not access Internet')
        exit(1)
    check_pre()


def check_version(local):
    logger.log('INFOR', 'Checking for the latest version')
    api = 'https://api.github.com/repos/shmilylty/OneForAll/releases/latest'
    header = get_random_header()
    proxy = get_proxy()
    timeout = settings.request_timeout_second
    verify = settings.request_ssl_verify
    session = requests.Session()
    session.trust_env = False
    try:
        resp = session.get(url=api, headers=header, proxies=proxy,
                           timeout=timeout, verify=verify)
        resp_json = resp.json()
        latest = resp_json['tag_name']
    except Exception as e:
        logger.log('ERROR', 'An error occurred while checking the latest version')
        logger.log('DEBUG', e.args)
        return
    if latest > local:
        change = resp_json.get("body")
        logger.log('ALERT', f'The current version is {local} '
                            f'but the latest version is {latest}')
        logger.log('ALERT', f'The {latest} version mainly has the following changes')
        logger.log('ALERT', change)
    else:
        logger.log('INFOR', f'The current version {local} is already the latest version')


def get_main_domain(domain):
    if not isinstance(domain, str):
        return None
    return Domain(domain).registered()


def call_massdns(massdns_path, dict_path, ns_path, output_path, log_path,
                 query_type='A', process_num=1, concurrent_num=10000,
                 quiet_mode=False):
    logger.log('DEBUG', 'Start running massdns')
    quiet = ''
    if quiet_mode:
        quiet = '--quiet'
    status_format = settings.brute_status_format
    socket_num = settings.brute_socket_num
    resolve_num = settings.brute_resolve_num
    cmd = f'{massdns_path} {quiet} --status-format {status_format} ' \
          f'--processes {process_num} --socket-count {socket_num} ' \
          f'--hashmap-size {concurrent_num} --resolvers {ns_path} ' \
          f'--resolve-count {resolve_num} --type {query_type} ' \
          f'--flush --output J --outfile {output_path} ' \
          f'--root --error-log {log_path} {dict_path} --filter OK ' \
          f'--sndbuf 0 --rcvbuf 0'
    logger.log('DEBUG', f'Run command {cmd}')
    subprocess.run(args=cmd, shell=True)
    logger.log('DEBUG', f'Finished massdns')


def get_massdns_path(massdns_dir):
    path = settings.brute_massdns_path
    if path:
        return path
    system = platform.system().lower()
    machine = platform.machine().lower()
    name = f'massdns_{system}_{machine}'
    if system == 'windows':
        name = name + '.exe'
        if machine == 'amd64':
            massdns_dir = massdns_dir.joinpath('windows', 'x64')
        else:
            massdns_dir = massdns_dir.joinpath('windows', 'x84')
    path = massdns_dir.joinpath(name)
    path.chmod(S_IXUSR)
    if not path.exists():
        logger.log('FATAL', 'There is no massdns for this platform or architecture')
        logger.log('INFOR', 'Please try to compile massdns yourself '
                            'and specify the path in the configuration')
        exit(0)
    return path


def is_subname(name):
    chars = string.ascii_lowercase + string.digits + '.-'
    for char in name:
        if char not in chars:
            return False
    return True


def ip_to_int(ip):
    if isinstance(ip, int):
        return ip
    try:
        ipv4 = IPv4Address(ip)
    except Exception as e:
        logger.log('ERROR', e.args)
        return 0
    return int(ipv4)


def match_subdomains(domain, html, distinct=True, fuzzy=True):
    """
    Use regexp to match subdomains

    :param  str domain: main domain
    :param  str html: response html text
    :param  bool distinct: deduplicate results or not (default True)
    :param  bool fuzzy: fuzzy match subdomain or not (default True)
    :return set/list: result set or list
    """
    logger.log('TRACE', f'Use regexp to match subdomains in the response body')
    if fuzzy:
        regexp = r'(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.){0,}' \
                 + domain.replace('.', r'\.')
        result = re.findall(regexp, html, re.I)
        if not result:
            return set()
        deal = map(lambda s: s.lower(), result)
        if distinct:
            return set(deal)
        else:
            return list(deal)
    else:
        regexp = r'(?:\>|\"|\'|\=|\,)(?:http\:\/\/|https\:\/\/)?' \
                 r'(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.){0,}' \
                 + domain.replace('.', r'\.')
        result = re.findall(regexp, html, re.I)
    if not result:
        return set()
    regexp = r'(?:http://|https://)'
    deal = map(lambda s: re.sub(regexp, '', s[1:].lower()), result)
    if distinct:
        return set(deal)
    else:
        return list(deal)


def check_random_subdomain(subdomains):
    if not subdomains:
        logger.log('ALERT', f'The generated dictionary is empty')
        return
    for subdomain in subdomains:
        if subdomain:
            logger.log('ALERT', f'Please check whether {subdomain} is correct or not')
            return


def get_url_resp(url):
    logger.log('INFOR', f'Attempting to request {url}')
    timeout = settings.request_timeout_second
    verify = settings.request_ssl_verify
    session = requests.Session()
    session.trust_env = False
    try:
        resp = session.get(url, params=None, timeout=timeout, verify=verify)
    except Exception as e:
        logger.log('ALERT', f'Error request {url}')
        logger.log('DEBUG', e.args)
        return None
    return resp


def decode_resp_text(resp):
    content = resp.content
    if not content:
        return str('')
    try:
        # 先尝试用utf-8严格解码
        content = str(content, encoding='utf-8', errors='strict')
    except (LookupError, TypeError, UnicodeError):
        try:
            # 再尝试用gb18030严格解码
            content = str(content, encoding='gb18030', errors='strict')
        except (LookupError, TypeError, UnicodeError):
            # 最后尝试自动解码
            content = str(content, errors='replace')
    return content


def sort_by_subdomain(data):
    return sorted(data, key=lambda item: item.get('subdomain'))


def ping(host, path):
    """

    :param host:
    :param path:
    :return:
    """
    param = '-n' if platform.system().lower() == 'windows' else '-c'

    command = ['ping', param, '3', host]
    with open(path, "w") as f:
        return subprocess.call(command, stdout=f, stderr=f)


def ping_avg_time(nameserver):
    """

    :param nameserver:
    :return:
    """
    check_dir(settings.temp_save_dir)
    temp_path = settings.temp_save_dir.joinpath('ping')
    ping(nameserver, path=temp_path)
    with open(temp_path, 'r')as f:
        text = f.readlines()[-1]
        if '100.0% packet loss' in text:
            logger.log('ALERT', f'100.0% packet loss, ping {nameserver} failed.')
            return None
        elif 'round-trip' in text:
            avg_time = re.findall(r'\d+\.\d+', text)[1]
            logger.log('INFOR', f'ping {nameserver} average time {avg_time} ms.')
            return avg_time
        else:
            logger.log('ALERT', f'{text}')
            return None


def auto_select_nameserver():
    """"""
    logger.log('INFOR', f'Ping test start, to select nameservers.')
    avg_time1 = ping_avg_time('114.114.114.114')
    avg_time2 = ping_avg_time('8.8.8.8')
    if avg_time1 and avg_time2:
        if avg_time1 < avg_time2:
            change_nameservers_file('cn')
            logger.log('INFOR', f'Ping test finished, use cn nameservers.')
        else:
            change_nameservers_file('common')
            logger.log('INFOR', f'Ping test finished, use common nameservers.')
    elif avg_time1 and not avg_time2:
        change_nameservers_file('cn')
        logger.log('INFOR', f'Ping test finished, use cn nameservers.')
    elif not avg_time1 and avg_time1:
        change_nameservers_file('common')
        logger.log('INFOR', f'Ping test finished, use common nameservers.')
    elif not avg_time1 and not avg_time1:
        change_nameservers_file('default')
        logger.log('INFOR', f'Ping test finished, use default nameservers.')
        return


def change_nameservers_file(option):
    text = ''
    if option == 'cn':
        with open(settings.data_storage_dir.joinpath('cn_nameservers.txt'), 'r') as f:
            text = f.read()
    elif option == 'common':
        with open(settings.data_storage_dir.joinpath('common_nameservers.txt'), 'r') as f:
            text = f.read()
    elif option == 'default':
        for n in default_nameserver():
            text = '\n'.join(n)
    with open(settings.data_storage_dir.joinpath('nameservers.txt'), 'w') as f:
        f.write(text)
    return


def default_nameserver():
    """

    :return: system default nameservers
    """
    try:
        dns_resolver: Resolver = dns.resolver.Resolver()
        return dns_resolver.nameservers
    except dns.resolver.NoResolverConfiguration:
        logger.log('ERROR', 'Resolver configuration could not be read or specified no nameservers.')
        exit(0)
