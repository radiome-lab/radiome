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
    -   workflow1: # Step name
            run: radiome.workflows.workflow1 # Full package name
            in: # Input parameters for this workflow
                param1: False 
                param2: 0.1
    -   workflow2:
            run: radiome.workflows.workflow2
            in:
                param1: 20      
```

### How Pipeline Executes

1. Radiome loads and validates the config file.
2. Steps are resolved in a top-down manner. In each step, workflow specified by `run` section is imported as a module dynamically,  then `create_workflow` function, the entry point, is extracted from the module.
3. This function is called with parameters of `in` section, `resource pool`, and `context` (run-time information). 





