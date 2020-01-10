import unittest

import networkx
from nipype.interfaces import base as nib

from radiome.execution import DependencySolver
from radiome.execution.nipype import NipypeJob
from radiome.resource_pool import ResourcePool, ResourceKey


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
    def test_output(self):
        rp = ResourcePool()
        mod1 = NipypeJob(EngineTestInterface(), reference="mod1")
        mod1.input1 = 1
        # TODO do we need to accept other type of inputs except Resource
        # mod1()

    def test_connect(self):
        rp = ResourcePool()
        mod2 = NipypeJob(EngineTestInterface(), reference="mod2")
        mod1 = NipypeJob(EngineTestInterface(), reference="mod1")
        mod2.input1 = mod1.output1
        rp[ResourceKey('T1w')] = mod2.output1
        g = DependencySolver(rp).graph
        self.assertIn(mod1, g.nodes)
        self.assertIn(mod2, g.nodes)
        self.assertTrue(networkx.algorithms.bidirectional_dijkstra(g, mod1, mod2))

    def test_connect_cycle(self):
        rp = ResourcePool()
        mod3 = NipypeJob(EngineTestInterface(), reference="mod3")
        mod2 = NipypeJob(EngineTestInterface(), reference="mod2")
        mod1 = NipypeJob(EngineTestInterface(), reference="mod1")
        mod3.input1 = mod2.output1
        mod2.input1 = mod1.output1
        mod1.input1 = mod3.output1
        rp[ResourceKey('T1w')] = mod1.output1
        # TODO: RecursionError: maximum recursion depth exceeded
        # g = DependencySolver(rp).graph


if __name__ == '__main__':
    unittest.main()
