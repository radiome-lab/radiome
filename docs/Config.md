### Why Config File

To build a neuroimaging pipeline, we must know what workflows we need and the order of execution. Besides, arguments for each workflow are necessary. Config file is used to provide such information for a pipeline.

### Config File Template

In Radiome, pipeline config file is a YAML file with required sections and keys.

```yaml
radiomeSchemaVersion: 1.0

# Type of schema, required.
class: pipeline

# Pipeline name. required.
name: anat-preproc

# Pipeline description, optional.
doc: Some description text

# Pipeline steps, required.
steps:
  - workflow1: # Step name
    run: radiome.workflows.workflow1 # Full package name
    in: # Input parameters for this workflow
      param1: False
      param2: 0.1
  - workflow2:
    run: radiome.workflows.workflow2
    in:
      param1: 20
  - sameworkflow2:
    run: radiome.workflows.workflow2
    in:
      param1: 10
```

### How Pipeline Executes

1. Radiome loads and validates the config file.
2. Steps are resolved in a top-down manner. In each step, workflow specified by `run` section is imported as a module,  then `create_workflow` function, the entry point, is extracted from the module.
3. `create_workflow` is called with parameters from `in` section, a global `resource pool`, and `context` (run-time information).
4. Once all workflows finish, information of the pipeline is established. Radiome execution engine will do the computation and produce the outputs.
