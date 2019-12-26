from unittest import TestCase
from radiome.resource_pool import Resource, ResourceKey, ResourcePool
from itertools import product

class TestResourcePool(TestCase):

    def test_resource_pool(self):

        rp = ResourcePool()

        slot = 'output_file'
        tags = ['write_to_mni', 'smooth_before', 'write_at_4mm', 'qc_carpet']

        resource_key = ResourceKey('atlas-aal_roi-112_desc-skullstripping-afni_mask', tags=tags)
        resource = Resource(slot)

        rp[resource_key] = resource

        _, extracted_rp = next(rp[[ResourceKey('atlas-*_mask', tags=['write_to_mni'])]])
        _, extracted_rp = next(rp[[ResourceKey('mask', tags=['write_to_mni'])]])

        self.assertEqual(rp[resource_key], resource)
        self.assertEqual(rp['write_to_mni'][resource_key], resource)
        self.assertEqual(rp['mask'][resource_key], resource)

    def test_resource_pool_extraction(self):

        slot = ''

        rp = ResourcePool()

        rp['space-orig_T1w'] = Resource(slot)

        rp['space-orig_desc-skullstrip-afni_mask'] = Resource(slot)
        rp['space-orig_desc-skullstrip-bet_mask'] = Resource(slot)

        rp['space-orig_desc-skullstrip-afni+nuis-gsr_bold'] = Resource(slot)
        rp['space-orig_desc-skullstrip-bet+nuis-gsr_bold'] = Resource(slot)
        rp['space-orig_desc-skullstrip-afni+nuis-nogsr_bold'] = Resource(slot)
        rp['space-orig_desc-skullstrip-bet+nuis-nogsr_bold'] = Resource(slot)

        rp['space-MNI_desc-nuis-gsr_mask'] = Resource(slot)
        rp['space-MNI_desc-nuis-nogsr_mask'] = Resource(slot)

        extraction = dict(rp.extract(
            'space-orig_T1w',
            'space-orig_mask',
            'space-orig_bold',
            'space-MNI_mask'
        ))

        self.assertEqual(len(extraction), 4)

        self.assertEqual(
            extraction[ResourceKey(desc='skullstrip-bet+nuis-gsr')][ResourceKey('space-orig_T1w')],
            rp[ResourceKey('space-orig_T1w')]
        )

        self.assertEqual(
            extraction[ResourceKey(desc='skullstrip-bet+nuis-gsr')][ResourceKey('space-orig_bold')],
            rp[ResourceKey('space-orig_desc-skullstrip-bet+nuis-gsr_bold')]
        )

        self.assertEqual(
            extraction[ResourceKey(desc='skullstrip-bet+nuis-gsr')][ResourceKey('space-orig_bold')],
            rp[ResourceKey('space-orig_desc-skullstrip-bet+nuis-gsr_bold')]
        )

        self.assertEqual(
            extraction[ResourceKey(desc='skullstrip-bet+nuis-gsr')][ResourceKey('space-orig_bold')],
            rp[ResourceKey('space-orig_desc-skullstrip-bet+nuis-gsr_bold')]
        )

        self.assertEqual(
            extraction[ResourceKey(desc='skullstrip-bet+nuis-nogsr')][ResourceKey('space-MNI_mask')],
            rp[ResourceKey('space-MNI_desc-nuis-nogsr_mask')]
        )

    def test_resource_pool_extraction_subsesrun(self):

        rp = ResourcePool()

        subs = 4
        sess = 3
        runs = 2

        for sub, ses in product(range(subs), range(sess)):
            ses_prefix = 'sub-%03d_ses-%03d_' % (sub, ses)
            rp[ses_prefix + 'space-orig_T1w'] = Resource(ses_prefix + 'space-orig_T1w')
            rp[ses_prefix + 'space-orig_desc-skullstrip-afni_mask'] = Resource(ses_prefix + 'space-orig_desc-skullstrip-afni_mask')
            rp[ses_prefix + 'space-orig_desc-skullstrip-bet_mask'] = Resource(ses_prefix + 'space-orig_desc-skullstrip-bet_mask')

        for sub, ses, run in product(range(subs), range(sess), range(runs)):
            run_prefix = 'sub-%03d_ses-%03d_run-%03d_' % (sub, ses, run)
            rp[run_prefix + 'space-orig_desc-skullstrip-afni+nuis-gsr_bold'] = Resource(run_prefix + 'space-orig_desc-skullstrip-afni+nuis-gsr_bold')
            rp[run_prefix + 'space-orig_desc-skullstrip-bet+nuis-gsr_bold'] = Resource(run_prefix + 'space-orig_desc-skullstrip-bet+nuis-gsr_bold')
            rp[run_prefix + 'space-orig_desc-skullstrip-afni+nuis-nogsr_bold'] = Resource(run_prefix + 'space-orig_desc-skullstrip-afni+nuis-nogsr_bold')
            rp[run_prefix + 'space-orig_desc-skullstrip-bet+nuis-nogsr_bold'] = Resource(run_prefix + 'space-orig_desc-skullstrip-bet+nuis-nogsr_bold')

        extraction = list(rp[[
            'space-orig_T1w',
            'space-orig_mask',
        ]])

        self.assertEqual(len(extraction), 2 * subs * sess)

        extraction = list(rp[[
            'space-orig_T1w',
            'space-orig_mask',
            'space-orig_bold',
        ]])

        self.assertEqual(len(extraction), 4 * subs * sess * runs)

        extraction = list(rp[[
            'sub-*_space-orig_T1w',
            'sub-*_space-orig_mask',
            'sub-*_space-orig_bold',
        ]])

        self.assertEqual(len(extraction), 4 * sess * runs)


    def test_resource_key(self):

        key_dict = {'atlas': 'aal',
                    'roi': '112',
                    'desc': 'skullstripping-afni',
                    'suffix': 'mask'}

        key_string = 'atlas-aal_roi-112_desc-skullstripping-afni_mask'

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

        self.assertEqual(ResourceKey(new_key_from_string, atlas='mni').entities['atlas'], 'mni')

        original_key = ResourceKey('atlas-aal_roi-112_desc-skullstripping-afni_mask')

        self.assertTrue(ResourceKey('desc-skullstripping-afni_mask') in original_key)
        self.assertTrue(ResourceKey('desc-nuis-gsr_mask') in original_key)

        # Strategy matching
        self.assertTrue(original_key in ResourceKey('atlas-aal_roi-112_desc-skullstripping-afni+nuis-gsr_mask'))
        self.assertTrue(ResourceKey('space-MNI_desc-nuis-nogsr_mask') in ResourceKey('space-MNI_desc-nuis-nogsr_mask'))
        self.assertTrue(ResourceKey('space-MNI_desc-nuis-nogsr_mask') not in ResourceKey('space-MNI_desc-nuis-gsr_mask'))

        self.assertTrue(
            ResourceKey('sub-000_ses-000_run-000_space-orig_T1w') in
            ResourceKey('space-orig_desc-skullstripping-bet+nuis-nogsr_T1w')
        )

        # Wildcard matching
        self.assertTrue(ResourceKey('sub-001_mask') in ResourceKey('sub-*_mask'))


    def test_invalid_resource_key(self):

        # Case: invalid entity
        invalid_key_dict = {
            'atlas': 'aal',
            'roi': '112',
            'desc': 'skullstripping-afni',
            'something': 'emmm',
            'suffix': 'mask'
        }
        invalid_key_string = 'atlas-aal_roi-112_desc-skullstripping-afni_something_emmm_mask'

        with self.assertRaises(ValueError):
            ResourceKey(invalid_key_string)

        with self.assertRaises(KeyError):
            ResourceKey(invalid_key_dict)

        with self.assertRaises(KeyError):
            ResourceKey(**invalid_key_dict)

        # Case: String in invalid format
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
