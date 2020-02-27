import glob
import os
import tempfile
import unittest

from radiome import cli
from radiome.resource_pool import ResourceKey
from radiome.utils.s3 import S3Resource

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
    'inputs': S3Resource('s3://fcp-indi/data/Projects/ABIDE/RawDataBIDS/Leuven_1', tempfile.mkdtemp()),
    'outputs': tempfile.mkdtemp(),
    'label': ['0050683', '0050686'],
    'config': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/config.yml')
}, {
    'inputs': S3Resource('s3://fcp-indi/data/Projects/ABIDE/RawDataBIDS/Leuven_1/sub-0050682', tempfile.mkdtemp()),
    'outputs': tempfile.mkdtemp(),
    'config': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/config.yml')
}]


class NormalTestCase(unittest.TestCase):
    def test_run_s3_local(self):
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


if __name__ == '__main__':
    unittest.main()
