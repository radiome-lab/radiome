import os

from radiome.core.resource_pool import ResourceKey


def derivative_location(pipeline_name: str, key: ResourceKey) -> str:
    path = os.path.join('derivatives', pipeline_name)
    if 'sub' in key.entities:
        path = os.path.join(path, f'sub-{key.entities["sub"]}')
    if 'ses' in key.entities:
        path = os.path.join(path, f'ses-{key.entities["ses"]}')
    category = 'anat' if key.suffix == 'T1w' else 'func'
    path = os.path.join(path, category)
    return path
