import os
import tempfile
import unittest

from radiome.core.execution import loader


class LoaderTestCase(unittest.TestCase):
    def test_git(self):
        dest = tempfile.mkdtemp()
        loader._resolve_git('gh://octocat/Hello-World', dest)
        self.assertTrue(os.path.isfile(f'{dest}/README'))

        dest = tempfile.mkdtemp()
        with self.assertRaises(ValueError):
            loader._resolve_git('gh://^$$^@*#@*$#@', dest)
            loader._resolve_git('git://a/b', dest)

        with self.assertRaises(FileExistsError):
            loader._resolve_git('gh://octocat/Hello-World', os.path.abspath('..'))

    def test_load(self):
        module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/fake_workflow')
        self.assertEqual(loader.load(module_path)(None, None, None), 'test')


if __name__ == '__main__':
    unittest.main()
