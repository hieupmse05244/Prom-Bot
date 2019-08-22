import math


class StatusBot(object):

    def __init__(self, resource, soul):
        self.server = resource
        self.soul = soul
        self.status = None
        self.last_update_data = 0

    def get_status(self, key):

        # self.status = None
        list_suggestion = self.get_suggestion(key)

        if not list_suggestion['jobs'] and \
           not list_suggestion['aliases']:
            self.status = '/status'
            return 'Not found!', None

        if list_suggestion['jobs']:
            best_job = list_suggestion['jobs'][0]
            score = best_job['score']
            name = best_job['key']
            if score == 100:
                result = '\nJob: {}\n======================'.format(name)
                list_alias, error = self.server.get_job_aliases(name)
                if error != 0:
                    return ErrorHandle.get_error_message(
                        error_code=error
                    ), None
                for alias in list_alias:
                    result += self.server.get_overview(alias)

                return result, None

        if list_suggestion['aliases']:
            best_alias = list_suggestion['aliases'][0]
            score = best_alias['score']
            name = best_alias['key']
            if score == 100:
                return self.server.get_overview(name), None

        return None, list_suggestion

    def get_suggestion(self, key):

        suggestion = {
            'jobs': [],
            'aliases': []
        }

        jobs, error = self.server.get_jobs()
        if error != 0:
            return None

        aliases, error = self.server.get_all_alias()
        if error != 0:
            return None

        list_jobs = []
        list_aliases = []

        for job in jobs:
            score = compare_score(key.lower(), job.lower())
            if score > 0:
                list_jobs.append({'key': job, 'score': score})

        for alias in aliases:
            score = compare_score(key.lower(), alias.lower())
            if score > 0:
                list_aliases.append({'key': alias, 'score': score})

        list_jobs.sort(key=lambda item: item['score'], reverse=True)
        list_aliases.sort(key=lambda item: item['score'], reverse=True)

        suggestion['jobs'] = list_jobs
        suggestion['aliases'] = list_aliases

        return suggestion


def compare_score(key, resource):
    score = 0

    key_len = len(key)
    src_len = len(resource)
    sub_len = lcs(key, resource)

    base_score = max(key_len, src_len) * 2
    tmp_score = sub_len * 2
    bonus_score = 0

    if sub_len == key_len:
        bonus_score += min(base_score - tmp_score, tmp_score) \
            * (tmp_score / base_score)
    if sub_len == src_len:
        bonus_score += min(base_score - tmp_score, tmp_score) \
            * (tmp_score / base_score)

    score = tmp_score + bonus_score

    return round(100 * score / base_score, 2)


def lcs(s1, s2):
    s = ''
    f = [[0]]

    for i in range(len(s1)):
        if len(f) < i+2:
            f.append([])
        f[i+1].append(0)
        for j in range(len(s2)):
            if len(f[i+1]) < j+2:
                f[i+1].append(0)
            f[0].append(0)
            if s1[i] == s2[j]:
                f[i+1][j+1] = f[i][j] + 1
            else:
                f[i+1][j+1] = max(
                    f[i+1][j],
                    f[i][j+1]
                )

    return f[len(s1)][len(s2)]


class ErrorHandle(object):

    @staticmethod
    def get_error_message(error_code, mess={}):
        e_msg = ''

        if error_code == -1:
            e_msg = mess['content']

        if error_code == 1:
            e_msg = 'Data not found!'

        if error_code == 2:
            e_msg = 'Result not found!'

        if error_code == 3:
            e_msg = 'Label not found!'

        if len(e_msg) == 0:
            e_msg = 'HTTP error code ' + str(error_code)

        return e_msg
