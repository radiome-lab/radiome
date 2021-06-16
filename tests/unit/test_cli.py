import copy
import os
import tempfile
import unittest
from unittest import mock

from radiome.core import cli


class CLITestCase(unittest.TestCase):
    def setUp(self):
        self.temp_out_dir = tempfile.mkdtemp()
        self.temp_working_dir = tempfile.mkdtemp()
        self.config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/builder.yml')
        self.args = ['s3://fcp-indi/data/Projects/ABIDE/RawDataBIDS/Leuven_1',
                     self.temp_out_dir,
                     '--config', self.config_file_path,
                     '--working_dir', self.temp_working_dir,
                     '--participant_label', '0050683', '0050686',
                     '--n_cpus', '2',
                     '--mem_gb', '4.5',
                     '--save_working_dir',
                     '--disable_file_logging',
                     '--diagnostics'
                     ]
        self.parsed = cli.parse_args(self.args)

    def test_parse_args(self):
        res = self.parsed
        self.assertEqual(res.bids_dir, 's3://fcp-indi/data/Projects/ABIDE/RawDataBIDS/Leuven_1')
        self.assertEqual(res.config_file, self.config_file_path)
        self.assertTrue(res.disable_file_logging)
        self.assertEqual(res.mem_gb, 4.5)
        self.assertEqual(res.n_cpus, 2)
        self.assertEqual(res.outputs_dir, self.temp_out_dir)
        self.assertListEqual(res.participant_label, ['0050683', '0050686'])
        self.assertTrue(res.save_working_dir)
        self.assertFalse(res.enable_bids_validator)
        self.assertEqual(res.working_dir, self.temp_working_dir)
        self.assertTrue(res.diagnostics)

    def test_build_context(self):
        # mutation test
        with self.assertRaises(FileNotFoundError):
            res = copy.copy(self.parsed)
            res.config_file = os.path.abspath('data')
            cli.build_context(res)

        with self.assertRaises(FileNotFoundError):
            res = copy.copy(self.parsed)
            res.bids_dir = os.path.abspath('./NotFound')
            cli.build_context(res)

        res = copy.copy(self.parsed)
        res.outputs_dir = 's3://name1/name2'
        ctx = cli.build_context(res)
        self.assertEqual(str(ctx.outputs_dir), res.outputs_dir)
        self.assertEqual(ctx.working_dir, self.temp_working_dir)
        res.outputs_dir = self.temp_out_dir
        res.working_dir = None
        ctx = cli.build_context(res)
        self.assertEqual(ctx.working_dir, f'{self.temp_out_dir}/scratch')
        self.assertTrue(os.path.exists(f'{self.temp_out_dir}/scratch'))

        res = copy.copy(self.parsed)
        res.mem_gb = None
        res.mem_mb = 1024
        ctx = cli.build_context(res)
        self.assertEqual(ctx.memory, 1024)
        res.mem_mb = None
        ctx = cli.build_context(res)
        self.assertIsInstance(ctx.memory, int)

        # No mutation
        res = self.parsed
        ctx = cli.build_context(self.parsed)
        self.assertEqual(ctx.working_dir, self.temp_working_dir)
        self.assertListEqual(ctx.participant_label, res.participant_label)
        self.assertEqual(ctx.memory, 4.5 * 1024)
        self.assertEqual(ctx.n_cpus, res.n_cpus)

    @mock.patch.dict(os.environ, {'PATH': ''})
    def test_bids_validation_without_executable(self):
        res = copy.deepcopy(self.parsed)
        res.enable_bids_validator = True
        with self.assertRaises(OSError):
            cli.build_context(res)

    @mock.patch.dict(os.environ, {'PATH': ''})
    def test_bids_validation_without_executable(self):
        res = copy.deepcopy(self.parsed)
        res.bids_dir = tempfile.mkdtemp()
        res.enable_bids_validator = True
        with self.assertRaises(OSError):
            cli.build_context(res)

    @mock.patch('shutil.which')
    @mock.patch('subprocess.run')
    def test_bids_validation(self, mock_subproc_run, util):
        res = copy.deepcopy(self.parsed)
        res.bids_dir = tempfile.mkdtemp()
        res.enable_bids_validator = True

        class Object(object):
            pass

        completed_process = Object()
        completed_process.stdout = Object()
        completed_process.stdout.splitlines = lambda: None
        completed_process.returncode = 0
        mock_subproc_run.return_value = completed_process
        cli.build_context(res)
        self.assertEqual(mock_subproc_run.call_args[0][0][1], res.bids_dir)

        with self.assertRaises(ValueError):
            completed_process.returncode = 1
            cli.build_context(res)


if __name__ == '__main__':
    unittest.main()
