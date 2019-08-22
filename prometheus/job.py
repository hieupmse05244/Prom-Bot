import sys
import os
import re

import connection.api_connection as api_conn


class Jobs(object):

    def __init__(self, prom):
        self.server = prom.server
        self.auth = prom.auth
        self.jobs = []
        self.aliases = []

    def clear_data(self):
        self.jobs = []
        self.aliases = []

    def get_jobs(self):

        if self.jobs:
            return self.jobs, 0

        api = '/api/v1/label/job/values'
        url = self.server + api

        response = api_conn.do_get(
            url=url,
            auth=self.auth
        )

        if response.status_code != 200:
            return None, response.status_code

        raw = response.json()
        data = raw['data'] \
            if 'data' in raw else None
        if not data:
            return None, 1

        self.jobs = data

        return self.jobs, 0

    def get_all_alias(self):
        if self.aliases:
            return self.aliases, 0

        aliases = []

        jobs, error = self.get_jobs()

        for job in jobs:
            alias, error = self.get_job_aliases(job)
            if error != 0:
                continue
            aliases += alias

        self.aliases = aliases

        return self.aliases, 0

    def get_query(self, query, lables, values):
        opt = ''
        opt_num = len(lables)
        for i in range(opt_num):
            opt += '' + lables[i] + '=\"' + values[i] + '\"'
            if i < opt_num - 1:
                opt += ','
        query = query + '{' + opt + '}'
        return query

    def get_api(self, query, url):
        params = {}
        params['query'] = query
        response = api_conn.do_get(
            url=url,
            params=params,
            auth=self.auth
        )
        if response.status_code != 200:
            return None, response.status_code

        raw = response.json()

        data = raw['data'] \
            if 'data' in raw else None
        if not data:
            return None, 1

        result = data['result'] \
            if 'result' in data else None
        if not result:
            return None, 2

        return result, 0

    def get_job_aliases(self, jobname):
        url = self.server + '/api/v1/query'
        query = self.get_query(
            query='node_exporter_build_info',
            lables=['job'],
            values=[jobname]
        )
        results, error = self.get_api(
            query=query,
            url=url
        )
        if error != 0:
            return None, error
        aliases = []

        for result in results:
            metric, error = get_metric(result)
            if error != 0:
                return None, error
            alias, error = get_label_value(
                record=metric,
                label='alias'
            )
            if error != 0:
                return None, error
            aliases.append(alias)

        return aliases, 0

    def get_cpu_total(self, alias):

        url = self.server + '/api/v1/query'

        query = self.get_query(
            query='node_cpu_seconds_total',
            lables=['alias'],
            values=[alias]
        )
        results, error = self.get_api(
            query=query,
            url=url
        )
        if error != 0:
            return None, error

        cpu_count = 0
        tick = {}

        for result in results:
            metric, error = get_metric(result)
            if error != 0:
                return None, error
            cpu, error = get_label_value(metric, 'cpu')
            if error != 0:
                return None, error
            if cpu in tick:
                continue
            else:
                tick[cpu] = '1'
                cpu_count += 1
        return cpu_count, 0

    def get_cpu_used(self, alias):

        url = self.server + '/api/v1/query'

        query = self.get_query(
            query='node_cpu_seconds_total',
            lables=['alias', 'mode'],
            values=[alias, 'idle']
        )

        query = '100 - (avg(irate(' + query + '[5m])) * 100)'

        results, error = self.get_api(
            query=query,
            url=url
        )
        if error != 0:
            return None, error

        value, error = get_value(results)

        if not value:
            return None, 2

        return str(value) + '%', 0

    def get_memory_total(self, alias):
        url = self.server + '/api/v1/query'

        query = self.get_query(
            query='node_memory_MemTotal_bytes',
            lables=['alias'],
            values=[alias]
        )

        results, error = self.get_api(
            query=query,
            url=url
        )
        if error != 0:
            return None, error

        value, error = get_value(results)

        if not value:
            return None, 2

        value = round(value / 1024 / 1024 / 1024, 2)

        return str(value) + ' GB', 0

    def get_memory_used(self, alias):
        url = self.server + '/api/v1/query'

        sub_q1 = self.get_query(
            query='node_memory_MemTotal_bytes',
            lables=['alias'],
            values=[alias]
        )

        sub_q2 = self.get_query(
            query='node_memory_MemFree_bytes',
            lables=['alias'],
            values=[alias]
        )

        sub_q3 = self.get_query(
            query='node_memory_Cached_bytes',
            lables=['alias'],
            values=[alias]
        )

        sub_q4 = self.get_query(
            query='node_memory_Buffers_bytes',
            lables=['alias'],
            values=[alias]
        )

        query = "({}-{}-{}-{})/{}*100".format(
            sub_q1,
            sub_q2,
            sub_q3,
            sub_q4,
            sub_q1
        )

        results, error = self.get_api(
            query=query,
            url=url
        )
        if error != 0:
            return None, error

        value, error = get_value(results)

        if not value:
            return None, 2

        return str(value) + '%', 0

    def get_swap_used(self, alias):
        url = self.server + '/api/v1/query'

        sub_q1 = self.get_query(
            query='node_memory_SwapTotal_bytes',
            lables=['alias'],
            values=[alias]
        )

        sub_q2 = self.get_query(
            query='node_memory_SwapFree_bytes',
            lables=['alias'],
            values=[alias]
        )

        query = "({}-{})/{}*100".format(
            sub_q1,
            sub_q2,
            sub_q1
        )

        results, error = self.get_api(
            query=query,
            url=url
        )
        if error != 0:
            return None, error

        value, error = get_value(results)

        if not value:
            return None, 2

        return str(value) + '%', 0

    def get_disk_total(self, alias):
        url = self.server + '/api/v1/query'

        query = self.get_query(
            query='node_filesystem_size_bytes',
            lables=['alias', 'mountpoint', 'fstype!'],
            values=[alias, "/", "rootfs"]
        )
        results, error = self.get_api(
            query=query,
            url=url
        )
        if error != 0:
            return None, error

        value, error = get_value(results)

        if not value:
            return None, 2

        value = round(value / 1024 / 1024 / 1024, 2)

        return str(value) + ' GB', 0

    def get_disk_used(self, alias):
        url = self.server + '/api/v1/query'

        sub_q1 = self.get_query(
            query='node_filesystem_size_bytes',
            lables=['alias', 'mountpoint', 'fstype!'],
            values=[alias, "/", "rootfs"]
        )

        sub_q2 = self.get_query(
            query='node_filesystem_free_bytes',
            lables=['alias', 'mountpoint', 'fstype!'],
            values=[alias, "/", "rootfs"]
        )

        query = "({}-{})/{}*100".format(
            sub_q1,
            sub_q2,
            sub_q1
        )

        results, error = self.get_api(
            query=query,
            url=url
        )
        if error != 0:
            return None, error

        value, error = get_value(results)

        if not value:
            return None, 2

        return str(value) + '%', 0


def get_value(result):
    value = re.findall(
        r'value[\'\"]?\:\s*\[[0-9\.]*\,\s*[\"\']?((?:NaN)|(?:[0-9\.e\+\-]+))',
        str(result)
    )
    if not value:
        return None, 2
    value = value[0]
    if value == 'NaN':
        return None, 1
    value = float(value)
    value = round(value, 2)
    return value, 0


def get_metric(result):
    metric = result['metric'] \
        if 'metric' in result else None
    if not metric:
        return None, 2
    return metric, 0


def get_label_value(record, label):
    value = record[label] \
        if label in record else None
    if not value:
        return None, 3
    return value, 0
