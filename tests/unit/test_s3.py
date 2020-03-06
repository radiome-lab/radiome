import filecmp
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import boto3
from moto import mock_s3

from radiome.core.utils.s3 import S3Resource, get_profile_credentials

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
        dst = tempfile.mkdtemp()

        # Test upload
        s3res = S3Resource(f's3://{bucket_name}', dst, aws_cred_path='env')
        s3res.upload(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/s3'))

        # Test download
        sub = s3res / 's3' / 'folder' / 'test1.txt'
        self.assertTrue(
            filecmp.cmp(sub(), os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/s3/folder/test1.txt'),
                        shallow=False))

        sub2 = s3res % f'{bucket_name}/s3/folder/test1.txt'
        self.assertEqual(sub(), sub())
        self.assertTrue(filecmp.cmp(sub(), sub2(), shallow=False))

        # test walk
        res = []
        for x, y, z in s3res.walk():
            res.append((x, y, z))

        self.assertIn(('mybucket', ['s3'], []), res)
        self.assertIn(('mybucket/s3', ['folder'], ['test.txt']), res)
        self.assertIn(('mybucket/s3/folder', [], ['test1.txt', 'test2.txt']), res)

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
