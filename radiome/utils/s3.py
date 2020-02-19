import logging
import os
from configparser import ConfigParser, NoOptionError, NoSectionError, ParsingError
from typing import Callable

import s3fs

from radiome.resource_pool import Resource

logger = logging.getLogger(__name__)


class S3Resource(Resource):
    def __init__(self, content: str, working_dir: str = None, aws_cred_path: str = None, aws_cred_profile: str = None):
        if not content.lower().startswith("s3://"):
            raise KeyError(f'{content} is not a valid S3 address.')
        if aws_cred_profile is not None:
            self._client = s3fs.S3FileSystem(profile=aws_cred_profile)
        elif aws_cred_path is not None:
            if aws_cred_path == 'env':
                self._client = s3fs.S3FileSystem()
            else:
                if os.path.isfile(aws_cred_path):
                    self._client = s3fs.S3FileSystem(**get_profile_credentials(aws_cred_path))
                else:
                    raise FileNotFoundError(f'File {aws_cred_path} not found.')
        else:
            self._client = s3fs.S3FileSystem(anon=True)
        if not self._client.exists(content):
            raise KeyError(f"{content} can't be visited. Check your url or permission setting.")
        super().__init__(content)
        self._cwd = working_dir
        self._aws_cred_path = aws_cred_path
        self._aws_cred_profile = aws_cred_profile
        self._cached = None

    def __call__(self, *args):
        logger.info(f'Pulling s3 file from {self.content}')
        if self._cached is not None and os.path.exists(self._cached):
            return self._cached
        else:
            self._cached = os.path.join(self._cwd, os.path.basename(self.content))
            # TODO: dir vs file
            self._client.get(self.content, self._cached)
            return self._cached

    def upload(self, path) -> None:
        if not os.path.exists(path):
            raise IOError(f"Can't read the path {path}.")
        self._client.put(path, self.content, recursive=True)

    def walk(self, callback: Callable = None, filter: Callable = None, file_only: bool = False) -> None:
        def apply(*args):
            if filter is None:
                callback(*args)
            else:
                if filter(*args):
                    callback(*args)

        for root, dir, files in self._client.walk(self.content):
            if file_only:
                for file in files:
                    apply(root, dir, file)
            else:
                apply(root, dir, files)

    def __truediv__(self, key: str) -> 'S3Resource':
        if not isinstance(key, str):
            raise NotImplementedError
        else:
            return S3Resource(os.path.join(self.content, key), self._cwd, self._aws_cred_path, self._aws_cred_profile)

    def __mod__(self, key: str) -> 'S3Resource':
        if not isinstance(key, str):
            raise NotImplementedError
        else:
            return S3Resource(key, self._cwd, self._aws_cred_path, self._aws_cred_profile)


def get_profile_credentials(path: str, profile_name='default'):
    config = ConfigParser()
    config.read(path)
    try:
        aws_access_key_id = config.get(profile_name, 'aws_access_key_id')
        aws_secret_access_key = config.get(profile_name, 'aws_secret_access_key')
    except (ParsingError, NoSectionError, NoOptionError):
        logger.error(f'Error parsing config file: {path}.')
        raise
    return {
        'key': aws_access_key_id,
        'secret': aws_secret_access_key
    }
