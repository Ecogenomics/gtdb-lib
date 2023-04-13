import os
from pathlib import Path

import yaml

GTDB_LIB_ENV_VAR = 'GTDBLIB_CONFIG'


class _Config:

    def __init__(self):
        self._yaml = None

    @property
    def config_file(self):
        if self._yaml is None:
            path_var = os.environ.get(GTDB_LIB_ENV_VAR)
            if path_var is None:
                raise ValueError(f'Environment variable {GTDB_LIB_ENV_VAR} not set')
            path = Path(path_var)
            if not path.exists():
                raise IOError(f'Path {path} does not exist')
            with path.open() as f:
                self._yaml = yaml.safe_load(f)
        return self._yaml

    @property
    def db_host(self):
        return self.config_file['db']['host']

    @property
    def db_user(self):
        return self.config_file['db']['user']

    @property
    def db_pass(self):
        return self.config_file['db']['pass']

    @property
    def redis_host(self):
        return self.config_file['redis']['host']

    @property
    def redis_pass(self):
        return self.config_file['redis']['pass']


CONFIG = _Config()
