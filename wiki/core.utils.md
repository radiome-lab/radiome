# core.utils package

## Submodules

## core.utils.bids module


### core.utils.bids.derivative_location(pipeline_name: str, key: radiome.core.resource_pool.ResourceKey)
## core.utils.mocks module


### class core.utils.mocks.NipypeJob(interface, reference=None)
Bases: `radiome.core.execution.job.Job`

Nipype job mock for testing.

Mock that emulates the behavior and APIs of NipypeJob, but do not execute the commandline of nipype jobs.
It will create fake outputs based on the outputs traits.


### class core.utils.mocks.mock_nipype()
Bases: `object`

Context manager which replaces Nipype job with mock at runtime.

Patch the nipype job with mocks at runtime, then recover it when exiting.


#### name( = 'radiome.core.execution.nipype')
## core.utils.s3 module


### class core.utils.s3.S3Resource(content: str, working_dir: str, aws_cred_path: str = None, aws_cred_profile: str = None)
Bases: `radiome.core.resource_pool.Resource`, `os.PathLike`

Amazon AWS S3 Resource.

An representation of S3 resource. It is bind to a specific s3 bucket url and credentials.
Once the resource is initialized, files can be downloaded, cached and uoloaded to this
bucket.


#### upload(path)
Upload path to the S3 bucket.

Args:

    path: The source directory.


#### walk()
Iterate the S3 bucket, the behavior is the same as os.walk.


### core.utils.s3.get_profile_credentials(path: str, profile_name='default')
## Module contents


### class core.utils.Hashable()
Bases: `object`


### core.utils.deterministic_hash(obj)
