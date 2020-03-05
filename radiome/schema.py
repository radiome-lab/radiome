from typing import Tuple, Iterator

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
    's:author': {'type': 'list'},
    's:contributor': {'type': 'list'},
    's:citation': {'type': 'string'},
    's:codeRepository': {'type': 'string'},
    's:dateCreated': {'type': 'string'},
    's:license': {'type': 'string'},
    'inputs': {
        'type': 'dict',
        'dependencies': {'class': ['workflow']},
        'valuesrules': {
            'type': 'dict',
            'schema': {
                'type': {
                    'type': 'string',
                    'required': True,
                    'allowed': [
                        'boolean',
                        'binary',
                        'dict',
                        'float',
                        'integer',
                        'list',
                        'number',
                        'string',
                    ],
                },
                'doc': {'type': 'string'},
            },
        },
    },
    'outputs': {'type': 'dict', 'dependencies': {'class': ['workflow']}},
    'steps': {
        'type': 'list',
        'dependencies': {'class': ['pipeline']},
        'valuesrules': {
            'type': 'dict',
            'schema': {
                'run': {'type': 'string', 'required': True},
                'in': {'type': 'dict', 'required': True},
            },
        },
    },
}


def validate(config: dict) -> None:
    validator = Validator()
    if not validator.validate(config, schema):
        raise ValidationError(f"{','.join(validator.errors)}")


def steps(config: dict) -> Iterator[Tuple[str, str]]:
    validate(config)
    for step in config['steps']:
        for name, v in step.items():
            entry: str = v['run']
            params: dict = v['in']
            yield entry, params
