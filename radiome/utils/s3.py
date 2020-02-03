import logging
import os
from configparser import ConfigParser, NoOptionError, NoSectionError, ParsingError

import s3fs

logger = logging.getLogger(__name__)


def get_profile_credentials(path: str, profile_name='default'):
    config = ConfigParser()
    config.read(path)
    try:
        aws_access_key_id = config.get(profile_name, 'aws_access_key_id')
        aws_secret_access_key = config.get(profile_name, 'aws_secret_access_key')
    except (ParsingError, NoSectionError, NoOptionError):
        logger.error(f'Error parsing config file: {path}')
        raise
    return {
        'key': aws_access_key_id,
        'secret': aws_secret_access_key
    }


def download_file(url: str, save_path: str, cred_path: str = None):
    if cred_path is None:
        s3 = s3fs.S3FileSystem(anon=True)
    elif cred_path == 'env':
        s3 = s3fs.S3FileSystem()
    else:
        s3 = s3fs.S3FileSystem(**get_profile_credentials(cred_path))
    s3.get(url, os.path.join(save_path, os.path.basename(url)))
    logger.info(f'Download {url} to {save_path}.')
    return os.path.join(save_path, os.path.basename(url))
