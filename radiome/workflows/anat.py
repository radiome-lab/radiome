from ..resource_pool import ResourcePool, ResourceKey

# TODO input validation by resouce metadata (variant, flags, type)
# TODO output validation by resouce metadata (variant, flags, type)
# TODO config schema validator

inputs = [
    ResourceKey()
]


def create_workflow(workflow, configuration, resource_pool: ResourcePool):

    inputs = []
    outputs = []
