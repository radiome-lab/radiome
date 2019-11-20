from unittest import TestCase
from radiome import resource_pool


class TestResourcePool(TestCase):

    def test_resource_pool(self):

        rp = resource_pool.ResourcePool()

        workflow = object()
        slot = 'output_file'
        flags = ['write_to_mni', 'smooth_before', 'write_at_4mm', 'qc_carpet']

        resource_key = resource_pool.ResourceKey('atlas-aal_roi-112_desc-afni_mask')
        resource = resource_pool.Resource(workflow, slot, flags)

        rp[resource_key] = resource

        self.assertEqual(rp[resource_key], resource)
        self.assertEqual(rp['write_to_mni'][resource_key], resource)
        self.assertEqual(rp['mask'][resource_key], resource)

    def test_resource_key(self):

        key_dict = {'atlas': 'aal',
                    'roi': '112',
                    'desc': 'afni',
                    'suffix': 'mask'}

        key_string = 'atlas-aal_roi-112_desc-afni_mask'

        value = 'now is the time for all good men to come to the aid of their country'

        new_key_from_string = resource_pool.ResourceKey(key_string)
        new_key_from_dict = resource_pool.ResourceKey(key_dict)
        new_key_from_kwargs = resource_pool.ResourceKey(**key_dict)

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

    def test_invalid_resource_key(self):
        # case 1: invalid entity
        invalid_key_dict = {'atlas': 'aal',
                    'roi': '112',
                    'desc': 'afni',
                    'something': 'emmm',
                    'suffix': 'mask'}
        invalid_key_string = 'atlas-aal_roi-112_desc-afni_something_emmm_mask'

        with self.assertRaises(KeyError):
            new_key_from_string = resource_pool.ResourceKey(invalid_key_string)
            new_key_from_dict = resource_pool.ResourceKey(invalid_key_dict)
            new_key_from_kwargs = resource_pool.ResourceKey(**invalid_key_dict)

        # case 2: no suffix
        key_dict_without_suffix = {'atlas': 'aal',
                    'roi': '112',
                    'desc': 'afni'}

        key_string_without_suffix = 'atlas-aal_roi-112_desc-afni'

        with self.assertRaises(ValueError):
            new_key_from_string = resource_pool.ResourceKey(key_string_without_suffix)
            new_key_from_dict = resource_pool.ResourceKey(key_dict_without_suffix)
            new_key_from_kwargs = resource_pool.ResourceKey(**key_dict_without_suffix)

        # case 3: Wrong input type
        with self.assertRaises(ValueError):
            resource_pool.ResourceKey([])
            resource_pool.ResourceKey()

        # case 4: String in invalid format
        key_string_invalid_form1 = 'atlas-aal-112_desc-afni_mask'
        key_string_invalid_form2 = 'atlas_desc-afni_mask'
        key_string_invalid_form3 = 'mask_atlas'
        key_string_invalid_form4 = 'something'
        key_string_invalid_form5 = '_desc-afni_mask'
        key_string_invalid_form6 = ''

        with self.assertRaises(ValueError):
            resource_pool.ResourceKey(key_string_invalid_form1)
            resource_pool.ResourceKey(key_string_invalid_form5)
            resource_pool.ResourceKey(key_string_invalid_form6)

        self.assertEqual(str(resource_pool.ResourceKey(key_string_invalid_form2)), 'desc-afni_mask')
        self.assertEqual(str(resource_pool.ResourceKey(key_string_invalid_form3)), 'atlas')
        self.assertEqual(str(resource_pool.ResourceKey(key_string_invalid_form4)), 'something')
