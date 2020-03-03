import glob
import os
import tempfile
import unittest
from unittest import mock

import boto3
import s3fs
from moto import mock_s3

from radiome import cli
from radiome.resource_pool import ResourceKey
from radiome.utils.s3 import S3Resource
from .utils import MockJob

cases = [{
    'inputs': 's3://fcp-indi/data/Projects/ABIDE/RawDataBIDS/Leuven_1',
    'outputs': tempfile.mkdtemp(),
    'label': ['0050683', '0050686'],
    'config': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/config.yml')
}, {
    'inputs': 's3://fcp-indi/data/Projects/ABIDE/RawDataBIDS/Leuven_1/sub-0050682',
    'outputs': tempfile.mkdtemp(),
    'config': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/config.yml')
}, {
    'inputs': S3Resource('s3://fcp-indi/data/Projects/ABIDE/RawDataBIDS/Leuven_1/sub-0050682', tempfile.mkdtemp()),
    'outputs': tempfile.mkdtemp(),
    'config': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/config.yml')
}]


class NormalTestCase(unittest.TestCase):
    def test_run_s3_local(self):
        with MockJob():
            for data in cases:
                if 'label' in data:
                    if isinstance(data['inputs'], S3Resource):
                        args = [data['inputs'](),
                                data['outputs'],
                                '--config', data['config'],
                                '--participant_label', *data['label'],
                                '--save_working_dir',
                                ]
                    else:
                        args = [data['inputs'],
                                data['outputs'],
                                '--config', data['config'],
                                '--participant_label', *data['label'],
                                '--save_working_dir',
                                ]
                else:
                    if isinstance(data['inputs'], S3Resource):
                        args = [data['inputs'](),
                                data['outputs'],
                                '--config', data['config'],
                                '--save_working_dir',
                                ]
                    else:
                        args = [data['inputs'],
                                data['outputs'],
                                '--config', data['config'],
                                '--save_working_dir',
                                ]
                self.assertEqual(cli.main(args), 0)
                working_path = os.path.join(os.path.join(data['outputs'], 'scratch'))
                self.assertTrue(os.path.exists(working_path))

                # Check log file
                logs = [x for x in os.listdir(working_path) if len(x) >= 4 and x[-4:] == ".log"]
                self.assertTrue(logs)

                # Check output file
                self.assertTrue(os.path.exists(os.path.join(data['outputs'], 'derivatives')))
                outputs = glob.glob(f'{data["outputs"]}/derivatives/*/*/*/*.nii.gz')
                for out in outputs:
                    filename = os.path.basename(out)
                    key = ResourceKey(filename.split('.')[0])

    @mock.patch.dict(os.environ, {'AWS_ACCESS_KEY_ID': 'testing', 'AWS_SECRET_ACCESS_KEY': 'testing'})
    def test_run_local_s3(self):
        data = cases[1]
        input = S3Resource(data['inputs'], tempfile.mkdtemp())()

        with MockJob():
            with mock_s3():
                s3_client = boto3.client('s3')
                bucket_name = 'mybucket'
                s3_client.create_bucket(Bucket=bucket_name)
                s3 = s3fs.S3FileSystem()
                bucket_path = f's3://{bucket_name}/outputs'
                s3.makedir(bucket_path, create_parents=True)
                working_dir = tempfile.mkdtemp()
                args = [input,
                        bucket_path,
                        '--config', data['config'],
                        '--working_dir', working_dir,
                        '--save_working_dir'
                        ]
                cli.main(args)
                self.assertEqual(cli.main(args), 0)

                # Check working dir
                self.assertTrue(os.listdir(working_dir))

                # Check S3 Files
                self.assertTrue(s3.listdir(f'{bucket_path}/derivatives'))


if __name__ == '__main__':
    unittest.main()
