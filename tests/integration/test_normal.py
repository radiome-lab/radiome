import os
import tempfile
import unittest
from radiome import cli

data = {
    'inputs': 's3://fcp-indi/data/Projects/ABIDE/RawDataBIDS/Leuven_1',
    'outputs': tempfile.mkdtemp(),
    'label': ['0050683', '0050686'],
    'config': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/config.yml')
}


class NormalTestCase(unittest.TestCase):
    def test_run(self):
        args = [data['inputs'],
                data['outputs'],
                '--config', data['config'],
                '--participant_label', *data['label'],
                '--save_working_dir',
                ]
        self.assertEqual(cli.main(args), 0)
        self.assertTrue(os.path.exists(os.path.join(data['outputs'], 'derivatives')))


if __name__ == '__main__':
    unittest.main()
