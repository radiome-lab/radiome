import os

from setuptools import setup, find_namespace_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

requirements = []
if os.path.exists('requirements.txt'):
    with open('requirements.txt') as req:
        requirements = list(filter(None, req.read().splitlines()))

setup(
    name="{package_name}",
    version="0.0.1",
    author="{author}",
    author_email="{email}",
    description="{package_description}",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=find_namespace_packages(include=['radiome.*']),
    package_data={{
        'radiome.workflows.{package_name}': ['spec.yml']
    }},
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    include_package_data=True,
    zip_safe=False,
)
