import unittest

from radiome.core import workflow, AttrDict, ResourcePool
from radiome.core.execution import loader
from radiome.core.schema import ValidationError
from .helpers import data_path


class WorkflowTestCase(unittest.TestCase):
    def test_attr_dict(self):
        a = {'a': 1, 'b': False}
        attr_dict = AttrDict(a)
        self.assertEqual(attr_dict.a, 1)
        self.assertEqual(attr_dict['a'], 1)
        self.assertFalse(attr_dict.b)
        self.assertFalse(attr_dict['b'])

    def test_decorator(self):
        @workflow(validate_inputs=False)
        def func1(config, rp, ctx):
            return config.a

        self.assertEqual(func1({'a': 1}, {}, {}), 1)

        module_path = data_path(__file__, 'fake_workflow')
        entry = loader.load(module_path)
        decorated = workflow()(entry)
        with self.assertRaises(ValidationError):
            decorated({'msg': 123}, ResourcePool(), {})
        self.assertEqual(entry({'msg': 123}, ResourcePool(), {}), 'test')


if __name__ == '__main__':
    unittest.main()
