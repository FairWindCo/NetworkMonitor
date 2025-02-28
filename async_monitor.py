import json
import random
from collections import deque, defaultdict
from datetime import datetime

from icmplib import async_multiping, NameLookupError, is_hostname, async_resolve, resolve
from pyexpat.errors import messages

from async_schuduler import AsyncScheduler
from host_ping_result import HostResult


class AsyncMonitor(AsyncScheduler):

    @classmethod
    def load_config(cls, config_name='config.json'):
        with open(config_name) as config_file:
            config=json.load(config_file)
            return cls.from_config(config), config

    @classmethod
    def from_config(cls, config_dict):
        hosts = config_dict.get('hosts')
        hosts_group = config_dict.get('hosts_group')
        size = config_dict.get('size')
        count = config_dict.get('count')
        interval = config_dict.get('interval', 1)
        timeout = config_dict.get('timeout', 2)
        max_size = config_dict.get('max_size', 356)
        max_count = config_dict.get('max_count', 59)
        return cls(hosts, hosts_group, interval, timeout, size, count, max_count, max_size)

    def __init__(self, hosts:list=None, hosts_group:dict=None,
                 interval:int = 1, timeout:int = 2,
                 size=None, count=None, max_count=59, max_size=356):
        super().__init__()
        self.interval = interval
        self.timeout = timeout
        self.size = size
        self.count = count
        self.max_count = max_count
        self.max_size = max_size
        self.ping_results_query = deque(maxlen=65)
        self.pinged_hosts = set()
        self.last_ping = 0
        self.last_report = 0

        if hosts is not None:
            self.pinged_hosts.update(hosts)
        if hosts_group is not None:
            self.pinged_hosts.update(hosts_group)

        self.hosts_ip = dict()
        self.ips_host = dict()
        for host in self.pinged_hosts:
            if is_hostname(host):
                ips = resolve(host)
                self.hosts_ip[host] = ips
                for ip in ips:
                    self.ips_host[ip] = host

        self.group_hosts = defaultdict(set)
        if hosts_group is not None:
            for host,group_name in hosts_group.items():
                if is_hostname(host):
                    self.group_hosts[group_name].update(self.hosts_ip[host])
                else:
                    self.group_hosts[group_name].add(host)



        self.host_results = {}
        self.group_results = {}
        self.error_resolve_names = set()



    async def seconds_function(self, *args, **kwargs):
        packet_random = self.size if self.size else random.randint(10, self.max_size)
        packet_count = self.count if self.count else random.randint(3, self.max_count)
        try:
            result = map(HostResult.convert, await async_multiping(self.pinged_hosts,
                                           payload_size=packet_random,
                                           count=packet_count,
                                           interval=self.interval,
                                           timeout=self.timeout,))

            #print(result)
            self.ping_results_query.append(result)
            self.last_ping = datetime.now().timestamp()
        except NameLookupError as e:
            host = str(e).split('\'')[1]
            if host in self.pinged_hosts:
                self.pinged_hosts.remove(host)
                self.error_resolve_names.add(host)



    async def minutes_function(self, *args, **kwargs):
        minute_summary = defaultdict(list)
        print(len(self.ping_results_query))
        for i in range(len(self.ping_results_query)):
            second_result = self.ping_results_query[i]
            #print(second_result)
            for host in second_result:
                minute_summary[host.address].append(host)
        self.host_results = {host:HostResult.summary(results)  for host, results in minute_summary.items()}

        self.group_results = { link_name:HostResult.link_summary(link_name, self.host_results, hosts)
                               for link_name, hosts in self.group_hosts.items() }

        print(self.group_results)
        self.last_report = datetime.now().timestamp()

    @property
    def hosts(self):
        return list(self.pinged_hosts)

    @property
    def hosts_json(self):
        return [{'index': host} for host in self.pinged_hosts]


    @property
    def pinged_ip(self):
        return list(self.host_results.keys())


    @property
    def groups(self):
        return {name:list(hosts) for name, hosts in self.group_hosts.items()}

    @property
    def links(self):
        return list(self.group_hosts.keys())

    @property
    def links_json(self):
        return [{'index': link} for link in self.group_hosts.keys()]


    @property
    def hosts_statuses(self):
        return {self.ips_host.get(host_name, host_name):status.get_dict_for_json()
                for host_name, status in self.host_results.items()}

    @property
    def links_statuses(self):
        return {link_name:status.get_dict_for_json() for link_name, status in self.group_results.items()}

    @property
    def is_seconds_task_alive(self):
        delta = datetime.now().timestamp() - self.last_ping
        return delta < 2

    @property
    def is_minute_task_alive(self):
        delta = datetime.now().timestamp() - self.last_report
        return delta < 61

    @property
    def is_alive(self):
        return self.is_seconds_task_alive and self.is_minute_task_alive

    @property
    def error_names(self):
        return list(self.error_resolve_names)

if __name__ == '__main__':

    monitor = {
        'hosts':['127.0.0.1', '192.168.88.1', '8.8.8.8', '192.168.27.3'],
        'hosts_group':{'8.8.8.8':'google',
                              '4.4.4.4': 'google',},
        'count':3,
    }

    AsyncMonitor.from_config(monitor).execute()