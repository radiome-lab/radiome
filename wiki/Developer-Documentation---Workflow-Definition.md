This document defines the basic components of radiome - workflows.

A workflow is defined by its own namespace which refer to either a single python file, or serveral files contained in a folder.

Workflows should contain each of the following
1. a list of the inputs that are required for the workflow, these are things that the workflow does not know how to generate, there may be some requirements that the workflow _can_ make if they are not available, those are not included in this list, but their inputs would be.
2. a list of the resources that the workflow creates
3. a node naming scheme to ensure that node names are unique
4. a config_schema that describes the configuration information needed for the workflow
5. create_workflow method that builds the workflow, it will take a nipype workflow and resource pool objects as inputs, the method should have the following subsections:

    a. check configuration using schema
    b. check if outputs exist in resource pool, if the do then we don't need to add the workflow
    c. check if inputs exists in resource pool, if not build what you can, otherwise bail
    d. build workflow - add functionality by iterating over the following pattern

        1. new node
        2. configuration parameters
        3. connect inputs

   e. add outputs to resource pool

6. tests!
7. documentation

  