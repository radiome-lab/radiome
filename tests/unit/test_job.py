import unittest

import networkx
from nipype.interfaces import base as nib

from radiome.core.execution import DependencySolver
from radiome.core.jobs import NipypeJob
from radiome.core.resource_pool import ResourceKey, ResourcePool


class InputSpec(nib.TraitedSpec):
    input1 = nib.traits.Int(desc="a random int")
    input2 = nib.traits.Int(desc="a random int")
    input_file = nib.File(desc="Random File")


class OutputSpec(nib.TraitedSpec):
    output1 = nib.traits.List(nib.traits.Int, desc="outputs")


class EngineTestInterface(nib.SimpleInterface):
    input_spec = InputSpec
    output_spec = OutputSpec

    def _run_interface(self, runtime):
        runtime.returncode = 0
        self._results["output1"] = [1, self.inputs.input1]
        return runtime


class TestNipypeJob(unittest.TestCase):

    def test_connect(self):
        rp = ResourcePool()

        mod2 = NipypeJob(EngineTestInterface(), reference="mod2")
        mod1 = NipypeJob(EngineTestInterface(), reference="mod1")
        mod2.input1 = mod1.output1

        rp[ResourceKey('T1w')] = mod2.output1

        g = DependencySolver(rp).graph

        self.assertIn(id(mod1), g.nodes)
        self.assertIn(id(mod2), g.nodes)
        self.assertTrue(networkx.algorithms.bidirectional_dijkstra(g, id(mod1), id(mod2)))
