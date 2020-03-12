## What Is Workflow?

In neuroimaging, a **pipeline** is a set of data processing elements connected in series, where the output of one element is the input of the next one. A **workflow** is a single data processing element, which may pull data from resource pools,  create various **jobs** (such as Python functions or Nipype interfaces) to process it, and save result back to resource pools for further use.

### How To Use Workflow?

Workflows are distributed as **namespace Python packages**. All workflows are under `radiome.workflows` namespace. Install them using `pip`, just as what you did to install other Python packages, add a new **step** in pipeline config file and provide necessary parameters. Workflows will be resolved automatically by Radiome at runtime.

### Understand Inputs Of Workflow

There are two types of inputs for a workflow.

1. Resource: anatomical and functional image files, intermediate results, masks, templates, etc. All resources are organized in the global resource pool following BIDS standard. 
2. Parameters: arguments that control the behavior of workflows, such as factors, booleans and times. Parameters can be the same for distinct resources. Radiome will read these parameters from pipeline config file and pass them into workflows.

### How Workflows Work

The entry point of a workflow is always `create_workflow(params, resource_pool, context)` function. 

1.  Validate `params` against a schema in `spec.yml` to check whether types, ranges and other constraints are correct. Radiome provides this function in `radiome.core.schema.validate_inputs`. Call this function like this `validate_inputs(__file__, params)`.

2. Select `resources ` from `resource pool` based on some conditions. 

3. Use functions, nipype interfaces or other tools to process `resources`. The outputs of current step can be connected to the inputs of next steps. For example:

   ```python
   anat_deoblique = NipypeJob(interface=afni.Refit(deoblique=True))
   anat_deoblique.in_file = anatomical_image
   anat_reorient = NipypeJob(interface=afni.Resample(orientation='RPI', outputtype='NIFTI_GZ'))
   anat_reorient.in_file = anat_deoblique.out_file
   ```

4. Save the final result back to `resource pool`, so that it can be produced in the final outputs and used by other workflows.

### Where Are Outputs

Given that results reside in `resource pool`, their produced files can be found in `$output_dir/derivatives/{workflow_name}` after the pipefine completes.