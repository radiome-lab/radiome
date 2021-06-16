## Create a workflow

This tutorial will walk you through how to develop a new workflow for Radiome. In this tutorial, we will create a workflow that can refit, denoise and reorient anatomical images.

Workflows are namespace Python packages running on Python 3.6+. All workflows are under `radiome.workflows` namespace. Its boilerplate looks like:

```
- radiome
    - workflows
        - example
                __init__.py
                workflow.py
                spec.yml
requirements.txt
setup.py
```

Note that all modules must be under `radiome/workflows`. `__init__.py` must not present in `radiome` or `radiome/workflows` folder. Otherwise, this namespace package would be invalid. Besides, to make `setuptools` discover the namespace package, `find_namespace_packages` is used instead of `find_packages` in `setup.py`.  If you want to learn more about namespace packages, please refer to [namespace package](https://packaging.python.org/guides/packaging-namespace-packages/).

Radiome has two requirements over a workflow:

1. a `create_workflow` callable is the entry point to execute the workflow. It must exist in the module.
2. a `spec.yml` file must present at the same level as the python file that includes `create_workflow`. It stores description and input schema.

There can be multiple `create_workflow` and `spec.yml` if the module has more than one workflow.

In our example, the procedures of this workflow are

```
afni.Refit  -->  ants.DenoiseImage --> afni.Resample
```

As `ants.DenoiseImage` is time-consuming, we hope users can decide whether to enable this feature. Therefore, a boolean flag `denoise` is introduced. Our `spec.yml` looks like:

```yaml
radiomeSchemaVersion: 1.0

class: workflow

name: example

doc: an example workflow that supports refit, reorient and denoise.

inputs:
  denoise:
    type: boolean
    doc: Apply ants.DenoiseImage to images.
```

 `workflow.py`:

```python
from nipype.interfaces import afni
from nipype.interfaces import ants
from radiome.core import workflow, AttrDict, Context, ResourceKey as R, ResourcePool
from radiome.core.jobs import NipypeJob


@workflow()
def create_workflow(config: AttrDict, resource_pool: ResourcePool, context: Context):
  pass

```

Export this function to `__init__.py`.

```python
from .workflow import create_workflow
```

Let's explain it more:

1. Nipype interfaces are used to invoke native tools, such as AFNI, ANTs or FSL.
2. `create_workflow` always receives three arguments. `config` has the value of parameters or flags for this workflow.  It should conform to the schema in `spec.yml`. For instance, the config can be `{'denoise': True}` in our example.  `resource_pool` is for all image resources, such as T1w, masks, brain, etc. These resources can be retrieved through specified rules. More information on `resource_pool` is [here](https://github.com/radiome-lab/radiome/wiki/ResourcePool). `Context` is the immutable object for runtime information, which we don't use in this project.
3. `radiome.core.workflow` is a decorator on `create_workflow` function, it will register the decorated function as an entry point and add additional features.

The full form is `@radiome.core.workflow(validate_inputs=True, use_attr=True)`. `validate_inputs` enables validating your inputs against the schema in `spec.yml` file to guarantee inputs have proper types, like `{'denoise': True}` rather than `{'denoise': 1}`. Radiome use [Cerberus](https://docs.python-cerberus.org/en/stable/) and its [rules](https://docs.python-cerberus.org/en/stable/validation-rules.html) for validation because it can be fully serialized and deserialized. If you prefer a different library, you can leave `inputs` section in `spec.yml` empty and disable this feature in the decorator.

 `use_attr` is to retrieve values in `config` by attributes, that is, `config.denoise` instead of `config['denoise']`.  It is a plus to dict.

Then let's move to the implementation of the `create_workflow` function. The first step is to select resources from the `resource pool`. In our example, the input images are raw T1W (anatomical) images. `ResourcePool` is based on a `dict[ResourceKey, Resource]`. `ResourceKey` is a name that comes from  [BIDS Extension Proposals](https://github.com/bids-standard/bids-specification/blob/master/src/06-extensions.md). For example, `ResourceKey(sub-0050682_T1w)` represents the T1w data from subject ID 0050682. Resources in a resource pool are represented by class `Resource`. The instance of `Resource` is a callable. It would lazily evaluate and return its content when called. There are various types of `Resource`.

Use `list` rather than a single string key in `resource pool` is to `extract` all resources that have a suffix `T1w` no matter subjects, sessions or runs. It returns a generator of `tuple[strategy_key, StrategyResourcePool]`.

```python
for _, rp in resource_pool[['T1w']]:
    anat_image = rp[R('T1w')]
    # process the files
```

 `StrategyResourcePool` is a proxy pool that allows iteration and modification simultaneously. All operations, such as look up or save resources on `StrategyResourcePool `, are mapped to the underlying `ResourcePool`. Therefore, `anat_image` represents all `T1w` resource we need to process,

Now it's time to create jobs to process such images. Currently Radiome supports two kinds of jobs: `NipypeJob` and `PythonJob`.  `NipypeJob` is the wrapper for all niype interfaces.

Initialize the actual interface in kwarg `interface=` while giving the job a name in `reference`.

```python
anat_deoblique = NipypeJob(
            interface=afni.Refit(deoblique=True),
            reference='deoblique'
        )
```

If a Python function is expected, you can create it by

```python
func_job = PythonJob(function=func, reference='func_job')
```

Inputs for a job are supplied in a `setattr` fashion. Assume we have a Python function and a corresponding `PythonJob`:

```python
def reversed_string(path):
  # Must return a dict, outputs would be retrieved by job.reversed.
    return {
        'reversed': str(path[::-1]),
    }
```

```python
func_job = PythonJob(function=reversed_string, reference='func_job')
func_job.path = '/usr/bin' # set value
res = func_job.reversed # retrieve result
```


For nipype jobs, there are simpler rules.

For nipype:

```python
anat_deoblique.inputs.deoblique = True
```

For Radiome NipypeJob way:

```python
anat_deoblique.deoblique = True
```

For nipype:

```python
preproc.connect(anat_deoblique, 'out_file', outputnode, 'refit')
```

For Radiome NipypeJob:

```python
outputnode.refit = anat_deoblique.out_file
```

It is pretty straightforward, isn't it?

However, one important point is when you access an attribute in righthand expression, you are manipulating a `ComputedResource`. They will not compute and return a result immediately. `ComputedResource` can become inputs of other jobs. In this way, connections among the jobs are established. Computation happens after all workflows finish execution. Each `ComputedResource` is a node in the execution graph and, if not saved to `resource pool`, will be discarded after completion. Therefore, if you want the `ComputedResource` to be produced in your output directory, you should keep them in the `resource pool`.

```python
rp[R('T1w', label='reorient')] = anat_reorient.out_file
```

With all such knowledge in mind, we have

```python
from nipype.interfaces import afni
from nipype.interfaces import ants
from radiome.core import workflow, AttrDict, Context, ResourceKey as R, ResourcePool
from radiome.core.jobs import NipypeJob


@workflow()
def create_workflow(config: AttrDict, resource_pool: ResourcePool, context: Context):
    for _, rp in resource_pool[['T1w']]:
        anat_image = rp[R('T1w')]
        anat_deoblique = NipypeJob(
            interface=afni.Refit(deoblique=True),
            reference='deoblique'
        )
        anat_deoblique.in_file = anat_image
        output_node = anat_deoblique.out_file

        if config.denoise:
            denoise = NipypeJob(interface=ants.DenoiseImage(), reference='denoise')
            denoise.input_image = output_node
            output_node = denoise.output_image

        anat_reorient = NipypeJob(
            interface=afni.Resample(orientation='RPI', outputtype='NIFTI_GZ'),
            reference='reorient'
        )
        anat_reorient.in_file = output_node
        rp[R('T1w', label='reorient')] = anat_reorient.out_file
```

Some additional information in `setup.py`. Note that `spec.yml` must be included in package data.

```python
import os

from setuptools import setup, find_namespace_packages

requirements = []
if os.path.exists('requirements.txt'):
    with open('requirements.txt') as req:
        requirements = list(filter(None, req.read().splitlines()))

setup(
    name="example",
    version="0.0.1",
    author="Radiome developer",
    packages=find_namespace_packages(include=['radiome.workflows.*']),
    package_data={
        'radiome.workflows.example': ['spec.yml'],
    },
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    include_package_data=True,
    zip_safe=False,
)

```

Append nipype to `requirements.txt`

```
nipype
```

Finally let's do some tests to make sure everything is sweet! Radiome provides `WorkflowDriver` to run a single workflow and return a `resource pool` containing all results. The usage is

```python
wf = WorkflowDriver(entry_dir, test_data_dir)
res_rp = wf.run(config={'denoise': True})
```

Add some unit tests to this project.

```
- radiome
    - workflows
        - example
            __init__.py
            workflow.py
            spec.yml
    - tests
        - data
            sub-0050682_T1w.nii.gz (Come from http://fcon_1000.projects.nitrc.org/)
        test_example.py
requirements.txt
setup.py
```

`test_example.py`

```python
import os
import unittest

import nibabel as nib
from radiome.core.resource_pool import R
from radiome.core.utils.mocks import WorkflowDriver


# Locate the test data.
def test_data_dir(destination):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), destination)


# Locate the entry point of workflow.
def entry_dir(destination):
    return os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, 'radiome', 'workflows', destination))


class TestCase(unittest.TestCase):
    def setUp(self):
        self._wf = WorkflowDriver(entry_dir('example'),
                                  test_data_dir('data'))

    def test_result(self):
        res_rp = self._wf.run(config={'denoise': False})
        for _, rp in res_rp[['label-reorient_T1w']]:
            anat_image = rp[R('T1w', label='reorient')]
            self.assertIsNotNone(anat_image.content)


if __name__ == '__main__':
    unittest.main()
```

Start a virtual environment and install packages:

```bash
$ virtualenv venv
$ source venv/bin/activate
$ pip install radiome
$ pip install -e .
$ python tests/test_example.py
```

Currently radiome is not available on pypi, but you should be able to install it from the github repo.

The content is the location for the outputs. It is a path such as `some_dir/derivatives/example/sub-0050682/anat/sub-0050682_label-reorient_T1w.nii.gz`. `example` is from the `name` in your `spec.yml` file. All output files are organized following the BIDS outputs standard.

Now you should have a good knowledge of Radiome workflows. You are welcome to contribute workflows to the whole community!

