from unittest import TestCase
from radiome.resource_pool import Resource, ResourceKey, ResourcePool


class TestResourcePool(TestCase):

    def test_resource_pool(self):

        rp = ResourcePool()

        workflow = object()
        slot = 'output_file'
        tags = ['write_to_mni', 'smooth_before', 'write_at_4mm', 'qc_carpet']

        resource_key = ResourceKey('atlas-aal_roi-112_desc-afni_mask', tags=tags)
        resource = Resource(workflow, slot)

        rp[resource_key] = resource

        self.assertEqual(rp[resource_key], resource)
        self.assertEqual(rp['write_to_mni'][resource_key], resource)
        self.assertEqual(rp['mask'][resource_key], resource)

    def test_resource_pool_extraction(self):

        workflow = object()
        slot = 'output_file'

        rp = ResourcePool()

        rp['space-original_T1w'] = Resource(workflow, slot)

        rp['space-original_desc-skullstrip-afni_mask'] = Resource(workflow, slot)
        rp['space-original_desc-skullstrip-bet_mask'] = Resource(workflow, slot)

        rp['space-original_desc-skullstrip-afni+nuis-gsr_bold'] = Resource(workflow, slot)
        rp['space-original_desc-skullstrip-bet+nuis-gsr_bold'] = Resource(workflow, slot)
        rp['space-original_desc-skullstrip-afni+nuis-nogsr_bold'] = Resource(workflow, slot)
        rp['space-original_desc-skullstrip-bet+nuis-nogsr_bold'] = Resource(workflow, slot)

        rp['space-MNI_desc-nuis-gsr_mask'] = Resource(workflow, slot)
        rp['space-MNI_desc-nuis-nogsr_mask'] = Resource(workflow, slot)

        extraction = dict(rp.extract(
            'space-original_T1w',
            'space-original_mask',
            'space-original_bold',
            'space-MNI_mask'
        ))

        self.assertEqual(len(extraction), 4)

        self.assertEqual(
            extraction['skullstrip-bet+nuis-gsr'][ResourceKey('space-original_T1w')],
            rp[ResourceKey('space-original_T1w')]
        )

        self.assertEqual(
            extraction['skullstrip-bet+nuis-gsr'][ResourceKey('space-original_bold')],
            rp[ResourceKey('space-original_desc-skullstrip-bet+nuis-gsr_bold')]
        )

        self.assertEqual(
            extraction['skullstrip-bet+nuis-gsr'][ResourceKey('space-original_bold')],
            rp[ResourceKey('space-original_desc-skullstrip-bet+nuis-gsr_bold')]
        )

        self.assertEqual(
            extraction['skullstrip-bet+nuis-gsr'][ResourceKey('space-original_bold')],
            rp[ResourceKey('space-original_desc-skullstrip-bet+nuis-gsr_bold')]
        )

        self.assertEqual(
            extraction['skullstrip-bet+nuis-nogsr'][ResourceKey('space-MNI_mask')],
            rp[ResourceKey('space-MNI_desc-nuis-nogsr_mask')]
        )

    def test_resource_key(self):

        key_dict = {'atlas': 'aal',
                    'roi': '112',
                    'desc': 'afni',
                    'suffix': 'mask'}

        key_string = 'atlas-aal_roi-112_desc-afni_mask'

        value = 'now is the time for all good men to come to the aid of their country'

        new_key_from_string = ResourceKey(key_string)
        new_key_from_dict = ResourceKey(key_dict)
        new_key_from_kwargs = ResourceKey(**key_dict)

        self.assertEqual(str(new_key_from_string), str(new_key_from_dict))
        self.assertEqual(str(new_key_from_string), str(new_key_from_kwargs))
        self.assertEqual(str(new_key_from_dict), str(new_key_from_kwargs))
        self.assertEqual(new_key_from_string['desc'], new_key_from_dict['desc'])
        self.assertEqual(new_key_from_dict['atlas'], 'aal')
        with self.assertRaises(KeyError):
            value = new_key_from_dict['space']

        temp_dict_from_string = {new_key_from_string: value}
        temp_dict_from_dict = {new_key_from_dict: value}
        temp_dict_from_kwargs = {new_key_from_kwargs: value}

        self.assertEqual(temp_dict_from_string[new_key_from_string], temp_dict_from_dict[new_key_from_dict])
        self.assertEqual(temp_dict_from_string[new_key_from_string], temp_dict_from_kwargs[new_key_from_kwargs])

        original_key = ResourceKey('atlas-aal_roi-112_desc-skullstripping-afni_mask')

        self.assertTrue(ResourceKey('desc-skullstripping-afni_mask') in original_key)
        self.assertFalse(ResourceKey('desc-nuis-gsr_mask') in original_key)

        # Strategy matching
        self.assertTrue(original_key in ResourceKey('atlas-aal_roi-112_desc-skullstripping-afni+nuis-gsr_mask'))

    def test_invalid_resource_key(self):
        # case 1: invalid entity
        invalid_key_dict = {
            'atlas': 'aal',
            'roi': '112',
            'desc': 'afni',
            'something': 'emmm',
            'suffix': 'mask'
        }
        invalid_key_string = 'atlas-aal_roi-112_desc-afni_something_emmm_mask'

        with self.assertRaises(ValueError):
            ResourceKey(invalid_key_string)

        with self.assertRaises(KeyError):
            ResourceKey(invalid_key_dict)

        with self.assertRaises(KeyError):
            ResourceKey(**invalid_key_dict)

        # case 2: no suffix
        key_dict_without_suffix = {
            'atlas': 'aal',
            'roi': '112',
            'desc': 'afni'
        }

        key_string_without_suffix = 'atlas-aal_roi-112_desc-afni'

        with self.assertRaises(ValueError):
            ResourceKey(key_string_without_suffix)

        with self.assertRaises(ValueError):
            ResourceKey(key_dict_without_suffix)

        with self.assertRaises(ValueError):
            ResourceKey(**key_dict_without_suffix)

        # case 3: Wrong input type
        with self.assertRaises(ValueError):
            ResourceKey([])

        with self.assertRaises(ValueError):
            ResourceKey(bool)

        # case 4: String in invalid format
        # key_string_invalid_form1 = 'atlas-aal-112_desc-afni_mask'
        key_string_invalid_form2 = 'atlas_desc-afni_mask'
        key_string_invalid_form3 = 'mask_atlas'
        key_string_invalid_form4 = 'something'
        key_string_invalid_form5 = '_desc-afni_mask'
        key_string_invalid_form6 = ''

        # with self.assertRaises(ValueError):
        #     ResourceKey(key_string_invalid_form1)

        with self.assertRaises(ValueError):
            ResourceKey(key_string_invalid_form2)

        with self.assertRaises(ValueError):
            ResourceKey(key_string_invalid_form3)

        with self.assertRaises(ValueError):
            ResourceKey(key_string_invalid_form4)

        with self.assertRaises(ValueError):
            ResourceKey(key_string_invalid_form5)

        with self.assertRaises(ValueError):
            ResourceKey(key_string_invalid_form6)
