import os.path
from collections import OrderedDict

import yaml

from please_cli.config import POSTGRESQL_CONF
from please_cli.config import SRC_DIR


class Project(object):
    """
    A single project and its local configuration
    """
    def __init__(self, folder, config=None):
        self.folder = folder
        self.name = self.folder.replace('_', '-')
        if config is None:
            # Load configuration from folder
            self.path = os.path.join(SRC_DIR, self.folder)
            conf_path = os.path.join(self.path, 'config.yml')
            assert os.path.exists(conf_path), \
                'Missing configuration {}'.format(conf_path)
            self.config = yaml.load(open(conf_path))
        else:
            # Use provided configuration for internal tools
            self.config = config
            self.path = None

    def __getitem__(self, name):
        return self.config.get(name)

    def requires(self, requirement):
        return requirement in self.config.get('requires', [])

    def list_required(self):
        pass

    def check(self):
        '''
        Check loaded configuration
        '''

    def is_deployable(self):
        return 'deploy' in self.config


class Projects(object):
    """
    Manage all the projects contained in the src folder
    """
    def __init__(self):
        projects = list(map(lambda x: Project(x),
                    filter(lambda x: os.path.exists(os.path.join(SRC_DIR, x, 'default.nix')),
                           os.listdir(SRC_DIR))))

        projects.append(Project('postgresql', POSTGRESQL_CONF))

        # Use an orderect dict here
        self.projects = OrderedDict(
            (project.name, project)
            for project in sorted(projects, key=lambda p: p.name)
        )

    def __str__(self):
        return ''.join([' - {}\n'.format(name) for name in self.projects.keys()])

    def __getitem__(self, name):
        return self.projects.get(name)

    def names(self):
        return list(self.projects.keys())

    def __iter__(self):
        return self.projects.__itervalues__()

    def list_deployable(self):
        return list(filter(lambda p : p.is_deployable(), self.projects))

# Shared instance used throughout please_cli
ALL = Projects()
