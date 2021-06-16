#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from setuptools import setup, find_namespace_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

requirements = []
if os.path.exists('requirements.txt'):
    with open('requirements.txt') as req:
        requirements = list(filter(None, req.read().splitlines()))

setup_requirements = []
if os.path.exists('requirements_setup.txt'):
    with open('requirements_setup.txt') as req:
        setup_requirements = list(filter(None, req.read().splitlines()))

test_requirements = []
if os.path.exists('requirements_test.txt'):
    with open('requirements_test.txt') as req:
        test_requirements = list(filter(None, req.read().splitlines()))

dev_requirements = []
if os.path.exists('requirements_dev.txt'):
    with open('requirements_dev.txt') as req:
        dev_requirements = list(filter(None, req.read().splitlines()))
        dev_requirements += test_requirements

setup(
    author="Cameron Craddock, Anibal Sólon, Pu Zhao",
    author_email='cameron.craddock@gmail.com, anibalsolon@gmail.com, puzhao@utexas.edu',
    python_requires='>=3, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Configurable Pipeline for the Analysis of Medical Imaging Data",
    entry_points={
        'console_scripts': [
            'radiome=radiome.core.cli:main',
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
    packages=[
        p
        for p in find_namespace_packages(
            include=['radiome.core.*'],
            exclude=['tests']
        )
        if 'tests' not in p.split('.')
    ],
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/radiome-lab/radiome',
    version='0.1.0',
    zip_safe=False,
)
