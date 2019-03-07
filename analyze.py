import requests
import hashlib
from datetime import datetime
import os
import json
import sys

INDEX_URL = 'https://index.taskcluster.net/v1/tasks/project.releng.services.project.{env}.static_analysis_bot.phabricator.diff'
TASK_URL = 'https://queue.taskcluster.net/v1/task/{taskId}/status/'
CACHE = os.path.realpath(os.path.join(os.path.dirname(__file__), 'cache'))
assert os.path.isdir(CACHE), 'mkdir {}'.format(CACHE)


def err(msg):
    sys.stderr.write('{}\n'.format(msg))


def fetch(url, params=None, use_cache=True):

    # Check cache
    cache_key = url + (params and json.dumps(params, sort_keys=True) or '')
    path = os.path.join(CACHE, hashlib.md5(cache_key).hexdigest())
    if use_cache and os.path.exists(path):
        return json.load(open(path))

    # Load url
    resp = requests.get(url, params)
    resp.raise_for_status()
    data = resp.json()

    # Cache payload
    json.dump(data, open(path, 'w'), indent=4)
    err('Cached {}'.format(url))

    return data


class Task(object):
    def __init__(self, diff):
        self.id = diff['taskId']
        self.diff = diff
        self.status = fetch(TASK_URL.format(taskId=self.id))['status']

    @property
    def state(self):
        return self.status['state']

    @property
    def runtime(self):
        # Calc runtime
        def dt(date_str):
            if not date_str:
                return
            return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        started = dt(self.status['runs'][-1]['started'])
        resolved = dt(self.status['runs'][-1].get('resolved'))
        return resolved and resolved - started

class Env(object):

    def __init__(self, name, cache_root=False):
        self.name = name
        self.tasks = []
        self.cache_root = cache_root
        self.load_index()

        self.diffs = {
            task['data']['diff_phid']: task
            for task in self.tasks
        }

        self.states = {}

    def __str__(self):
        return self.name

    def load_index(self, batch_size=500):
        '''
        Load all tasks listed in this index
        '''
        assert isinstance(batch_size, int)
        params = {
            'limit': batch_size,
        }

        nb = 1
        while True:
            data = fetch(
                INDEX_URL.format(env=self.name),
                params,
                use_cache=nb > 1 or self.cache_root,
            )
            err('Loaded {} page {}'.format(self.name, nb))
            nb += 1

            # Use all tasks
            self.tasks += data['tasks']

            # Continue loading all available tasks
            params['continuationToken'] = data.get('continuationToken')
            if params['continuationToken'] is None:
                break

    def load_task(self, diff_id):
        '''
        Load full informations for this diff + env
        - task state + id
        - diff infos
        '''
        assert diff_id in self.diffs

        task = Task(self.diffs[diff_id])

        # Save on instance
        self.states[diff_id] = task

        return task




def compare(env_a, env_b):
    assert isinstance(env_a, Env)
    assert isinstance(env_b, Env)

    # Compare common diffs only
    common = set(env_a.diffs.keys()).intersection(env_b.diffs.keys())

    # Load common tasks
    tasks = [
        (
            env_a.load_task(diff_id),
            env_b.load_task(diff_id),
        )
        for diff_id in common
    ]

    # List different final states
    diff_states = [
        (a, b)
        for a, b in tasks
        if a.state != b.state and a.runtime and b.runtime
    ]

    # Count completed from final diff states
    diff_completed_a, diff_completed_b = map(sum, zip(*[
        (a.state == 'completed', b.state == 'completed')
        for a, b in diff_states
    ]))

    # Calc runtimes
    runtime_stats = []
    for env_tasks in zip(*tasks):
        runtimes = [
            task.runtime.total_seconds()
            for task in env_tasks
            if task.runtime
        ]
        total = sum(runtimes)
        nb = len(runtimes)
        average = total / nb
        runtime_stats.append((total, nb, average))


    # Display stats
    nb = len(common)
    nb_a = len(env_a.diffs)
    nb_b = len(env_b.diffs)
    print('-'*80)
    print('{} vs. {}'.format(env_a.name, env_b.name))
    print('-'*80)
    print('tasks {}: {}/{} - {:.2f}%'.format(env_a.name, nb, nb_a, nb * 100.0 / nb_a))
    print('tasks {}: {}/{} - {:.2f}%'.format(env_b.name, nb, nb_b, nb * 100.0 / nb_b))
    print('time {} total = {}, nb = {}, average = {}'.format(env_a, *runtime_stats[0]))
    print('time {} total = {}, nb = {}, average = {}'.format(env_b, *runtime_stats[1]))
    print('{}/{} diff states'.format(len(diff_states), len(tasks)))
    print('{} : {}/{} diff completed'.format(env_a.name, diff_completed_a, len(diff_states)))
    print('{} : {}/{} diff completed'.format(env_b.name, diff_completed_b, len(diff_states)))

    completion = diff_completed_a > diff_completed_b and (env_a, env_b) or (env_b, env_a)
    print('{} has more diff completion than {}'.format(*completion))
    runtime = runtime_stats[0][-1] < runtime_stats[1][-1] and (env_a, env_b) or (env_b, env_a)
    print('{} is faster on average than {}'.format(*runtime))


if __name__ == '__main__':

    testing = Env('testing')
    staging = Env('staging')
    production = Env('production')

    compare(testing, staging)
    compare(staging, production)
    compare(testing, production)
