import logging
import os
from configparser import ConfigParser, NoOptionError, NoSectionError, ParsingError
from typing import Iterator, Tuple

import s3fs

from radiome.core.resource_pool import Resource

logger = logging.getLogger(__name__)


class S3Resource(Resource, os.PathLike):
    """ Amazon AWS S3 Resource.

    An representation of S3 resource. It is bind to a specific s3 bucket url and credentials.
    Once the resource is initialized, files can be downloaded, cached and uoloaded to this
    bucket.

    """

    def __init__(self, content: str, working_dir: str, aws_cred_path: str = None, aws_cred_profile: str = None):
        """
        Initialize an S3 client, provide credentials through aws_cred_path or aws_cred_profile. Otherwise the client
        will try to connect anonymously.

        Args:
            content: the S3 bucket url.
            working_dir: the temporary dir for caching S3 files.
            aws_cred_path: the path of credit files, If the value is 'env', read from environment based on boto3 rules.
            aws_cred_profile: the aws profile name. Read from env.
        """
        if not content.lower().startswith("s3://"):
            content = f's3://{content}'
        if aws_cred_profile is not None:
            self._client = s3fs.S3FileSystem(anon=False, profile_name=aws_cred_profile)
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
        super().__init__(content)
        self._cwd = working_dir
        self._aws_cred_path = aws_cred_path
        self._aws_cred_profile = aws_cred_profile
        self._cached = None

    def __call__(self, *args, **kwargs):
        """
        Download files or directories to the working dir. Cache will be used if called multiple times.

        Args:
            *args: For further use.

        Returns:
            The path of downloaded files and directories.

        """
        logger.info(f'Pulling s3 file from {self.content}')
        if self._cached is not None and os.path.exists(self._cached):
            return self._cached
        else:
            self._cached = os.path.join(self._cwd, os.path.basename(self.content))
            if self._client.isfile(self.content):
                self._client.get(self.content, self._cached)
            else:
                self._client.get(self.content, self._cached, recursive=True)
            return self._cached

    def __fspath__(self):
        return self.__call__()

    def __str__(self):
        return self.content

    def upload(self, path) -> None:
        """
        Upload path to the S3 bucket.

        Args:
            path: The source directory.
        """
        if not os.path.exists(path):
            raise IOError(f"Can't read the path {path}.")
        self._client.put(path, self.content, recursive=True)

    def walk(self) -> Iterator[Tuple[str, list, list]]:
        """
        Iterate the S3 bucket, the behavior is the same as os.walk.
        """
        for root, dirs, files in self._client.walk(self.content):
            yield root, dirs, files

    def __truediv__(self, key: str) -> 'S3Resource':
        """
        Append key to the current bucket and form a new path. Use the same configuration.

        Args:
            key: File or subdirectory under the current bucket.

        Returns:
            A new S3 client with updated path.

        """
        if not isinstance(key, str):
            raise NotImplementedError
        else:
            return S3Resource(os.path.join(self.content, key), self._cwd, self._aws_cred_path, self._aws_cred_profile)

    def __mod__(self, key: str) -> 'S3Resource':
        """
        Replace the current path with key and return a new client. Use the same configuration.

        Args:
            key: S3 path to replace current one.

        Returns:
            A new S3 client with updated path.

        """
        if not isinstance(key, str):
            raise NotImplementedError
        else:
            return S3Resource(key, self._cwd, self._aws_cred_path, self._aws_cred_profile)


def get_profile_credentials(path: str, profile_name='default'):
    config = ConfigParser()
    config.read(path)
    if profile_name != 'default':
        profile_name = f'profile {profile_name}'
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
