import networkx as nx
from nipype.interfaces.base import Undefined
from nipype.interfaces.utility import IdentityInterface
from radiome.core import Resource
from radiome.core.jobs import PythonJob, NipypeJob, ComputedResource


def extract_nipype_graph(graph: nx.DiGraph) -> dict:
    matrix = nx.to_dict_of_dicts(graph.reverse())
    res = {}
    for node, pred_conn in matrix.items():
        if isinstance(node.interface, IdentityInterface):
            continue
        node_name = node.fullname.split('.')[1]
        res[node_name] = {}
        for name, _ in node.inputs.items():
            val = getattr(node.inputs, name)
            if val is not Undefined:
                res[node_name][name] = val
        for pred, conn in pred_conn.items():
            conn = conn['connect']
            for pair in conn:
                src, dst = pair
                if isinstance(pred.interface, IdentityInterface):
                    res[node_name][dst] = getattr(pred.inputs, src)
                else:
                    pred_name = pred.fullname.split('.')[1]
                    res[node_name][dst] = (pred_name, src)
    return res


def extract_radiome_graph(graph: nx.DiGraph) -> dict:
    mapping = {}
    matrix = nx.to_dict_of_dicts(graph.reverse())
    for data in graph.nodes.data():
        id, state = data
        job = state['job'].resource
        mapping[id] = job

    res = {}
    for node_id, pred_conn in matrix.items():
        job = mapping[node_id]
        if isinstance(job, NipypeJob):
            node_name = job._reference
            res[node_name] = {}
            for name, _ in job._interface.inputs.items():
                val = getattr(job._interface.inputs, name)
                if val is not Undefined:
                    res[node_name][name] = val
            for name, val in job.dependencies().items():
                res[node_name][name] = val
        elif isinstance(job, PythonJob):
            node_name = job._reference
            res[node_name] = {}
            for name, val in job.dependencies().items():
                res[node_name][name] = val
        else:
            continue

        for pred_id, conn in pred_conn.items():
            pred = mapping[pred_id]
            field = conn['field']
            if isinstance(pred, ComputedResource):
                res[node_name][field] = (pred.content[0]._reference, pred.content[1])
            elif isinstance(pred, Resource):
                res[node_name][field] = pred.content

    return res


def match_graph(cpac_graph: nx.DiGraph, radiome_graph: nx.DiGraph) -> bool:
    cpac_matrix = extract_nipype_graph(cpac_graph)
    radiome_matrix = extract_radiome_graph(radiome_graph)
    for k, v in cpac_matrix.items():
        if k not in radiome_matrix:
            return False
        radiome_value = radiome_matrix[k]
        if v != radiome_value:
            return False
    return True
