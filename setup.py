#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

requirements = [
    'nipype==1.2.3',
    'dask[delayed]==2.3',
    'networkx==2.3',
    'cloudpickle==1.2.2'
]

setup_requirements = [
]

test_requirements = [
    'pytest==5.3.0',
    'pytest-runner==5.2',
    'pytest-cov==2.8.1',
    'codecov==2.0.15',
    'flake8==3.7.9',
    'tox==3.14.1',
    'coverage==4.5.4',
    's3fs==0.4.0',
]

dev_requirements = [
    'bump2version==0.5.11',
    'wheel==0.33.6',
    'watchdog==0.9.0',
    'Sphinx==2.2.1',
    'twine==3.1.0',
] + test_requirements

setup(
    author="Cameron Craddock",
    author_email='cameron.craddock@gmail.com',
    python_requires='>=3, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Configurable Pipeline for the Analysis of Medical Imaging Data",
    entry_points={
        'console_scripts': [
            'radiome=radiome.cli:main',
        ],
    },
    extras_require={
        'dev': dev_requirements,
        'test': test_requirements,
    },
    install_requires=requirements,
    long_description=readme,
    include_package_data=True,
    keywords='radiome',
    name='radiome',
    packages=find_packages(include=['radiome', 'radiome.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/radiome-flow/radiome',
    version='0.1.0',
    zip_safe=False,
)
