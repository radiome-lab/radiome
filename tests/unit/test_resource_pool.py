from itertools import product
from unittest import TestCase

from radiome.core.resource_pool import Resource, ResourceKey as R, ResourcePool


class TestResourcePool(TestCase):

    def test_resource_pool(self):

        rp = ResourcePool()

        slot = 'output_file'
        tags = ['write_to_mni', 'smooth_before', 'write_at_4mm', 'qc_carpet']

        resource_key = R('atlas-aal_roi-112_desc-skullstripping-afni_mask', tags=tags)
        resource = Resource(slot)

        rp[resource_key] = resource

        self.assertEqual(rp[resource_key], resource)

        # TODO review case
        # self.assertEqual(rp[R(tags=['write_to_mni'])], resource)
        # self.assertEqual(rp['write_to_mni'][resource_key], resource)
        # self.assertEqual(rp['mask'][resource_key], resource)

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
            extraction[R(desc='skullstrip-bet+nuis-gsr')][R('space-orig_T1w')],
            rp[R('space-orig_T1w')]
        )

        self.assertEqual(
            extraction[R(desc='skullstrip-bet+nuis-gsr')][R('space-orig_bold')],
            rp[R('space-orig_desc-skullstrip-bet+nuis-gsr_bold')]
        )

        self.assertEqual(
            extraction[R(desc='skullstrip-bet+nuis-gsr')][R('space-orig_bold')],
            rp[R('space-orig_desc-skullstrip-bet+nuis-gsr_bold')]
        )

        self.assertEqual(
            extraction[R(desc='skullstrip-bet+nuis-gsr')][R('space-orig_bold')],
            rp[R('space-orig_desc-skullstrip-bet+nuis-gsr_bold')]
        )

        self.assertEqual(
            extraction[R(desc='skullstrip-bet+nuis-nogsr')][R('space-MNI_mask')],
            rp[R('space-MNI_desc-nuis-nogsr_mask')]
        )

    def test_resource_pool_extraction_sameresourcetype(self):

        rp = ResourcePool()

        rp['sub-001_T1w'] = Resource('001-A')
        rp['sub-001_label-initial_T1w'] = Resource('001-B')
        rp['sub-002_T1w'] = Resource('002-A')
        rp['sub-002_label-initial_T1w'] = Resource('002-B')

        for k, srp in rp[['T1w']]:
            sub = k['sub']
            self.assertEqual(srp[R(k, suffix='T1w')], Resource(f'{sub}-A'))
            self.assertEqual(srp[R(k, label='initial', suffix='T1w')], Resource(f'{sub}-B'))

    def test_resource_pool_extraction_subsesrun(self):

        rp = ResourcePool()

        subs = 4
        sess = 3
        runs = 2

        for sub, ses in product(range(subs), range(sess)):
            ses_prefix = 'sub-%03d_ses-%03d_' % (sub, ses)
            rp[ses_prefix + 'space-orig_T1w'] = Resource(ses_prefix + 'space-orig_T1w')
            rp[ses_prefix + 'space-orig_desc-skullstrip-afni_mask'] = Resource(
                ses_prefix + 'space-orig_desc-skullstrip-afni_mask')
            rp[ses_prefix + 'space-orig_desc-skullstrip-bet_mask'] = Resource(
                ses_prefix + 'space-orig_desc-skullstrip-bet_mask')

        for sub, ses, run in product(range(subs), range(sess), range(runs)):
            run_prefix = 'sub-%03d_ses-%03d_run-%03d_' % (sub, ses, run)
            rp[run_prefix + 'space-orig_desc-skullstrip-afni+nuis-gsr_bold'] = Resource(
                run_prefix + 'space-orig_desc-skullstrip-afni+nuis-gsr_bold')
            rp[run_prefix + 'space-orig_desc-skullstrip-bet+nuis-gsr_bold'] = Resource(
                run_prefix + 'space-orig_desc-skullstrip-bet+nuis-gsr_bold')
            rp[run_prefix + 'space-orig_desc-skullstrip-afni+nuis-nogsr_bold'] = Resource(
                run_prefix + 'space-orig_desc-skullstrip-afni+nuis-nogsr_bold')
            rp[run_prefix + 'space-orig_desc-skullstrip-bet+nuis-nogsr_bold'] = Resource(
                run_prefix + 'space-orig_desc-skullstrip-bet+nuis-nogsr_bold')

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

        new_key_from_string = R(key_string)
        new_key_from_dict = R(key_dict)
        new_key_from_kwargs = R(**key_dict)

        self.assertEqual(str(new_key_from_string), str(new_key_from_dict))
        self.assertEqual(str(new_key_from_string), str(new_key_from_kwargs))
        self.assertEqual(str(new_key_from_dict), str(new_key_from_kwargs))
        self.assertEqual(new_key_from_string['strategy'], new_key_from_dict['strategy'])
        self.assertEqual(new_key_from_dict['atlas'], 'aal')
        with self.assertRaises(KeyError):
            value = new_key_from_dict['space']

        temp_dict_from_string = {new_key_from_string: value}
        temp_dict_from_dict = {new_key_from_dict: value}
        temp_dict_from_kwargs = {new_key_from_kwargs: value}

        self.assertEqual(temp_dict_from_string[new_key_from_string], temp_dict_from_dict[new_key_from_dict])
        self.assertEqual(temp_dict_from_string[new_key_from_string], temp_dict_from_kwargs[new_key_from_kwargs])

        self.assertEqual(R(new_key_from_string, atlas='mni').entities['atlas'], 'mni')

        original_key = R('atlas-aal_roi-112_desc-skullstripping-afni_mask')

        self.assertTrue(R('desc-skullstripping-afni_mask') in original_key)
        self.assertTrue(R('desc-nuis-gsr_mask') in original_key)

        # Strategy matching
        self.assertTrue(original_key in R('atlas-aal_roi-112_desc-skullstripping-afni+nuis-gsr_mask'))
        self.assertTrue(R('space-MNI_desc-nuis-nogsr_mask') in R('space-MNI_desc-nuis-nogsr_mask'))
        self.assertTrue(R('space-MNI_desc-nuis-nogsr_mask') not in R('space-MNI_desc-nuis-gsr_mask'))

        self.assertTrue(
            R('sub-000_ses-000_run-000_space-orig_T1w') in
            R('space-orig_desc-skullstripping-bet+nuis-nogsr_T1w')
        )

        # Wildcard matching
        self.assertTrue(R('sub-001_mask') in R('sub-*_mask'))

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
            R(invalid_key_string)

        with self.assertRaises(KeyError):
            R(invalid_key_dict)

        with self.assertRaises(KeyError):
            R(**invalid_key_dict)

        # Case: String in invalid format
        # key_string_invalid_form1 = 'atlas-aal-112_desc-afni_mask'
        key_string_invalid_form2 = 'atlas_desc-afni_mask'
        key_string_invalid_form3 = 'mask_atlas'
        key_string_invalid_form4 = 'something'
        key_string_invalid_form5 = '_desc-afni_mask'
        key_string_invalid_form6 = ''

        # with self.assertRaises(ValueError):
        #     R(key_string_invalid_form1)

        with self.assertRaises(ValueError):
            R(key_string_invalid_form2)

        with self.assertRaises(ValueError):
            R(key_string_invalid_form3)

        with self.assertRaises(ValueError):
            R(key_string_invalid_form4)

        with self.assertRaises(ValueError):
            R(key_string_invalid_form5)

        with self.assertRaises(ValueError):
            R(key_string_invalid_form6)
