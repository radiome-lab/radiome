import os
from types import ModuleType
from typing import Tuple, Iterator

import yaml
from cerberus import Validator

supporting_templates = ['1.0']


def _version_check(field, value, error):
    parts = value.split('.')
    if len(parts) != 2:
        error(field, 'Too many parts in the version.')
    major, minor = parts
    if not major.isdigit() or not minor.isdigit():
        error(field, 'Version must be numeric.')
    if value not in supporting_templates:
        error(field, 'This version is not supported in current Radiome version.')


class ValidationError(Exception):
    pass


schema = {
    'radiomeSchemaVersion': {
        'check_with': _version_check,
        'required': True,
        'type': 'string',
        'allow_unknown': True,
        'coerce': str,
    },
    'class': {'allowed': ['workflow', 'pipeline'], 'required': True},
    'name': {'type': 'string', 'required': True},
    'doc': {'type': 'string'},
    'inputs': {'type': 'dict',
               'dependencies': {'class': ['workflow']},
               'valuesrules': {
                   'type': 'dict',
                   'schema': {
                       'type': {'type': 'string', 'required': True},
                   }
               }},
    'steps': {'type': 'list',
              'dependencies': {'class': ['pipeline']},
              'valuesrules': {
                  'type': 'dict',
                  'schema': {'run': {'type': 'string', 'required': True},
                             'in': {'type': 'dict', 'required': False, 'nullable': True}}
              }}
}


def validate(config: dict) -> None:
    validator = Validator()
    if not validator.validate(config, schema):
        raise ValidationError(f"{','.join(validator.errors)}")


def validate_inputs(current_file, config: dict):
    spec_path = os.path.join(os.path.dirname(current_file), 'spec.yml')
    if not os.path.isfile(spec_path):
        raise FileNotFoundError(f"Can't find spec.yml file for {current_file}.")
    with open(spec_path, 'r') as f:
        spec_schema = yaml.safe_load(f)
    validator = Validator()
    if not validator.validate(config, spec_schema['inputs']):
        raise ValidationError(f"{','.join(validator.errors)}")


def validate_spec(module: ModuleType) -> None:
    """
    Check that a module has spec.yml file and the spec.yaml is valid.

    Args:
        module: The module that has been imported.

    Raises:
        FileNotFoundError: The spec.yml is not found.
        ValidationError: Errors in validating spec.yml file.
    """
    spec_path = os.path.join(os.path.dirname(module.__file__), 'spec.yml')
    if not os.path.isfile(spec_path):
        raise FileNotFoundError(f"Can't find spec.yml file for {module.__name__}.")
    with open(spec_path, 'r') as f:
        config = yaml.safe_load(f)
        validate(config)


def steps(config: dict) -> Iterator[Tuple[str, str]]:
    validate(config)
    for step in config['steps']:
        for name, v in step.items():
            entry: str = v['run']
            params: dict = v['in']
            yield entry, params
