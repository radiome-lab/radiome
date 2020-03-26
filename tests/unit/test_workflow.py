import unittest

from radiome.core import workflow, AttrDict, ResourcePool
from radiome.core.execution import loader
from radiome.core.schema import ValidationError
from radiome.core.utils import TemplateDictionaryBuilder
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

    def test_template_dict(self):
        a = {
            'resolution': {
                'type': 'string',
            },
            'template_brain_only_for_anat': {
                'type': 'string',
                'default': '/usr/local/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz'
            }
        }
        res = TemplateDictionaryBuilder(a).build()
        self.assertEqual(res['template_brain_only_for_anat']['default'],
                         '/usr/local/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz')
        a = {
            'resolution': {
                'type': 'string',
                'default': '2mm'
            },
            'template_brain_only_for_anat': {
                'type': 'string',
                'default': '/usr/local/fsl/data/standard/MNI152_T1_{resolution}_brain.nii.gz'
            },
            'template': {
                'type': 'string',
                'default': '[{template_brain_only_for_anat}]'
            }
        }
        res = TemplateDictionaryBuilder(a).build()
        self.assertEqual(a['template_brain_only_for_anat']['default'],
                         '/usr/local/fsl/data/standard/MNI152_T1_{resolution}_brain.nii.gz')
        self.assertEqual(res['template_brain_only_for_anat']['default'],
                         '/usr/local/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz')
        self.assertEqual(res['template']['default'], '[/usr/local/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz]')

        a = {
            'resolution': {
                'type': 'string',
                'default': '2mm'
            },
            'template_brain_only_for_anat': {
                'type': 'string',
                'default': '/usr/local/fsl/data/standard/MNI152_T1_{reseolution}_brain.nii.gz'
            },
            'template': {
                'type': 'string',
                'default': '[{template_brain_only_for_anat}]'
            }
        }
        with self.assertRaises(KeyError):
            res = TemplateDictionaryBuilder(a).build()

        nodefault = {
            'resolution': {
                'type': 'string'
            },
            'template_brain_only_for_anat': {
                'type': 'string',
                'default': '/usr/local/fsl/data/standard/MNI152_T1_{resolution}_brain.nii.gz'
            },
        }
        with self.assertRaises(ValueError):
            TemplateDictionaryBuilder(nodefault).build()

        cycle = {
            'template_brain_only_for_anat': {
                'type': 'string',
                'default': '{template}'
            },
            'template': {
                'type': 'string',
                'default': '{template_brain_only_for_anat}'
            }
        }

        with self.assertRaises(ValueError):
            TemplateDictionaryBuilder(cycle).build()


if __name__ == '__main__':
    unittest.main()
