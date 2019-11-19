from unittest import TestCase
from radiome import resource_pool


class TestResourceKey(TestCase):

    def test_resource_key(self):

        key_dict = {'atlas': 'aal',
                    'roi': '112',
                    'desc': 'afni',
                    'suffix': 'mask'}

        key_string = 'atlas-aal_roi-112_desc-afni_mask'

        value = 'now is the time for all good men to come to the aid of their country'

        new_key_from_string = resource_pool.ResourceKey(key_string)

        new_key_from_dict = resource_pool.ResourceKey(key_dict)

        self.assertEqual(str(new_key_from_string), str(new_key_from_dict))
        self.assertEqual(new_key_from_string['desc'], new_key_from_dict['desc'])

        temp_dict_from_string = {new_key_from_string: value}
        temp_dict_from_dict = {new_key_from_dict: value}

        self.assertEqual(temp_dict_from_string[new_key_from_string], temp_dict_from_dict[new_key_from_dict])
