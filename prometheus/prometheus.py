import sys
import os

from prometheus.job import Jobs


class Prometheus(object):

    def __init__(self, server, auth):

        self.server = server
        self.auth = auth
        self.job = Jobs(self)

    def get_job_aliases(self, jobname):
        return self.job.get_job_aliases(jobname)

    def get_jobs(self):
        return self.job.get_jobs()

    def get_all_alias(self):
        return self.job.get_all_alias()

    def get_overview(self, alias):

        overview = '\nAlias: {}'.format(alias)
        # CPU total
        cpu_total, error = self.job.get_cpu_total(alias)
        if error != 0:
            cpu_total = 'N/A'
        overview += '\n{:<15}{:>15}'.format('CPU total:', cpu_total)
        # CPU used
        cpu_used, error = self.job.get_cpu_used(alias)
        if error != 0:
            cpu_used = 'N/A'
        overview += '\n{:<15}{:>15}'.format('CPU used:', cpu_used)
        # Memory total
        memory_total, error = self.job.get_memory_total(alias)
        if error != 0:
            memory_total = 'N/A'
        overview += '\n{:<15}{:>15}'.format('Memory total:', memory_total)
        # Memory used
        memory_used, error = self.job.get_memory_used(alias)
        if error != 0:
            memory_used = 'N/A'
        overview += '\n{:<15}{:>15}'.format('Memory used:', memory_used)
        # SWAP used
        swap_used, error = self.job.get_swap_used(alias)
        if error != 0:
            swap_used = 'N/A'
        overview += '\n{:<15}{:>15}'.format('SWAP used:', swap_used)
        # Disk total
        disk_total, error = self.job.get_disk_total(alias)
        if error != 0:
            disk_total = 'N/A'
        overview += '\n{:<15}{:>15}'.format('Disk total:', disk_total)
        # Disk used
        disk_used, error = self.job.get_disk_used(alias)
        if error != 0:
            disk_used = 'N/A'
        overview += '\n{:<15}{:>15}'.format('Disk used:', disk_used)

        overview += '\n______________'

        return overview

    def clear_data(self):
        return self.job.clear_data()
