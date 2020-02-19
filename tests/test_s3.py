import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import filecmp
import boto3
import s3fs
from moto import mock_s3

from radiome.utils.s3 import S3Resource, get_profile_credentials

bucket_name = 'mybucket'
test_data = [
    {'bucket': bucket_name,
     'dir': f'{bucket_name}/build',
     'file': os.path.join(os.path.dirname(os.path.abspath(__file__)), os.curdir, 'data/builder.yml')
     },
    {
        'bucket': bucket_name,
        'dir': f'{bucket_name}/config/file',
        'file': os.path.join(os.path.dirname(os.path.abspath(__file__)), os.curdir, 'data/config.yml')
    }
]


class S3ClientTestCase(unittest.TestCase):
    @mock_s3
    @mock.patch.dict(os.environ, {'AWS_ACCESS_KEY_ID': 'testing', 'AWS_SECRET_ACCESS_KEY': 'testing'})
    def test_s3(self):
        s3_client = boto3.client('s3')
        s3_client.create_bucket(Bucket=bucket_name)
        s3 = s3fs.S3FileSystem()

        # Test download
        s3.makedir(test_data[0]['dir'], create_parents=True)
        target = os.path.join(test_data[0]['dir'], os.path.basename(test_data[0]['file']))
        s3.upload(test_data[0]['file'], target)

        s3res = S3Resource(f's3://{target}', tempfile.mkdtemp(), aws_cred_path='env')
        self.assertTrue(filecmp.cmp(s3res(), test_data[0]['file'], shallow=False))

        # Test upload
        s3res = S3Resource(f's3://{bucket_name}', tempfile.mkdtemp(), aws_cred_path='env')
        s3res.upload(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'))
        # Test operator /
        sub = s3res / 'data' / 'builder.yml'
        # Test operator %
        sub2 = s3res % f's3://{bucket_name}/data/builder.yml'
        self.assertTrue(filecmp.cmp(sub(), test_data[0]['file'], shallow=False))
        self.assertTrue(filecmp.cmp(sub(), sub2(), shallow=False))

        # Test walk
        res = []
        s3res.walk(lambda x, y, z: res.append(z), filter=lambda x, y, z: len(z) == 2)
        self.assertListEqual(res[0], ['builder.yml', 'config.yml'])

    @mock.patch.dict(os.environ, {'HOME': tempfile.mkdtemp()})
    def test_credentials(self):
        fake_home = os.environ['HOME']
        aws_path = f'{fake_home}/.aws'
        Path(aws_path).mkdir(parents=True, exist_ok=True)
        Path(f'{aws_path}/config').write_text('[default]\n'
                                              'aws_access_key_id = testing\n'
                                              'aws_secret_access_key = testing1\n\n'
                                              '[profile project1]\n'
                                              'aws_access_key_id = testing\n'
                                              'aws_secret_access_key = testing2\n')

        key, secret = get_profile_credentials(f'{aws_path}/config').values()
        self.assertEqual(key, 'testing')
        self.assertEqual(secret, 'testing1')

        key, secret = get_profile_credentials(f'{aws_path}/config', profile_name='project1').values()
        self.assertEqual(key, 'testing')
        self.assertEqual(secret, 'testing2')

        s3_from_env = S3Resource('s3://mybucket', tempfile.mkdtemp(), aws_cred_path='env')
        s3_from_file = S3Resource('s3://mybucket', tempfile.mkdtemp(), aws_cred_path=f'{aws_path}/config')
        s3_with_profile = S3Resource('s3://mybucket', tempfile.mkdtemp(), aws_cred_profile='project1')
