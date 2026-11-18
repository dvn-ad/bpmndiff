"""Deterministic synthetic mutation dataset for BPMN model comparison.

The generator starts from real diagrams in the converted-XPDL dataset and
injects a controlled number of changes (``k = 1, 2, 4``).  Every base is emitted
twice per ``k``:

* ``keep``   — element IDs are preserved;
* ``newids`` — every XML ID is regenerated, simulating a full re-export.

Each variant ships with a ``change-v1`` ground truth.  The ground truth is an
*ideal* change set: it is derived from element identity that the generator
knows, not from the alignment engine under test.

Only the standard library is used, matching the rest of the project.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .alignment import label_similarity, normalize_label
from .contract import validate_change_record
from .model import ProcessModel
from .parsers import load_model

# ---------------------------------------------------------------------------
# XML namespaces
# ---------------------------------------------------------------------------
BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
DC_NS = "http://www.omg.org/spec/DD/20100524/DC"
DI_NS = "http://www.omg.org/spec/DD/20100524/DI"
BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
XSD_NS = "http://www.w3.org/2001/XMLSchema"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
BIZAGI_NS = "http://www.bizagi.com/bpmn20"

_NAMESPACES = (
    ("", BPMN_NS),
    ("dc", DC_NS),
    ("di", DI_NS),
    ("bpmndi", BPMNDI_NS),
    ("xsd", XSD_NS),
    ("xsi", XSI_NS),
    ("bizagi", BIZAGI_NS),
)


def _register_namespaces() -> None:
    for prefix, uri in _NAMESPACES:
        ET.register_namespace(prefix, uri)


_register_namespaces()

_NODE_TAGS = {
    "task",
    "userTask",
    "serviceTask",
    "scriptTask",
    "sendTask",
    "receiveTask",
    "manualTask",
    "businessRuleTask",
    "callActivity",
    "subProcess",
    "adHocSubProcess",
    "transaction",
    "startEvent",
    "endEvent",
    "intermediateCatchEvent",
    "intermediateThrowEvent",
    "boundaryEvent",
    "exclusiveGateway",
    "parallelGateway",
    "inclusiveGateway",
    "eventBasedGateway",
    "complexGateway",
}

_IDREF_ATTRIBUTES = {
    "sourceRef",
    "targetRef",
    "bpmnElement",
    "processRef",
    "dataStoreRef",
    "attachedToRef",
    "default",
    "labelStyle",
    "calledElement",
}

_IDREF_TEXT_TAGS = {"incoming", "outgoing", "flowNodeRef", "sourceRef", "targetRef"}

_CATEGORY_NAMES = {
    1: "Steps (tasks and events)",
    2: "Actors (lanes and pools)",
    3: "Sequence, flow, and branching",
    4: "Sub-process structure",
    5: "Data and cross-pool communication",
}

_LEGACY_TYPES = {
    "INSERT_NODE": "INSERT",
    "DELETE_NODE": "DELETE",
    "RENAME_NODE": "RENAME",
    "NODE_TYPE_CHANGE": "CHANGE_TYPE",
    "MOVE_LANE": "CHANGE_SWIMLANE",
    "RENAME_LANE": "RENAME_SWIMLANE",
    "GATEWAY_TYPE_CHANGE": "CHANGE_GATEWAY_TYPE",
}

_ELEMENT_OF = {
    "INSERT_NODE": "node",
    "DELETE_NODE": "node",
    "RENAME_NODE": "node",
    "NODE_TYPE_CHANGE": "node",
    "MARKER_CHANGE": "node",
    "BOUNDARY_CHANGE": "boundary_event",
    "MOVE_LANE": "swimlane",
    "RENAME_LANE": "swimlane",
    "INSERT_LANE": "swimlane",
    "DELETE_LANE": "swimlane",
    "GATEWAY_TYPE_CHANGE": "gateway",
    "INSERT_FLOW": "flow",
    "DELETE_FLOW": "flow",
    "FLOW_CONDITION_CHANGE": "flow",
    "REORDER": "node",
    "PARALLELIZE": "node",
    "SEQUENTIALIZE": "node",
    "EXTRACT_SUBPROCESS": "subprocess",
    "INLINE_SUBPROCESS": "subprocess",
    "MESSAGE_FLOW_CHANGE": "message_flow",
    "DATA_CHANGE": "data",
}

_CATEGORY_OF = {
    "INSERT_NODE": 1,
    "DELETE_NODE": 1,
    "RENAME_NODE": 1,
    "NODE_TYPE_CHANGE": 1,
    "MARKER_CHANGE": 1,
    "BOUNDARY_CHANGE": 1,
    "MOVE_LANE": 2,
    "RENAME_LANE": 2,
    "INSERT_LANE": 2,
    "DELETE_LANE": 2,
    "GATEWAY_TYPE_CHANGE": 3,
    "INSERT_FLOW": 3,
    "DELETE_FLOW": 3,
    "FLOW_CONDITION_CHANGE": 3,
    "REORDER": 3,
    "PARALLELIZE": 3,
    "SEQUENTIALIZE": 3,
    "EXTRACT_SUBPROCESS": 4,
    "INLINE_SUBPROCESS": 4,
    "MESSAGE_FLOW_CHANGE": 5,
    "DATA_CHANGE": 5,
}

DEFAULT_BASES = ("56", "57", "58", "63", "65")
ID_POLICIES = ("keep", "newids")
K_VALUES = (1, 2, 4)


class GeneratorError(RuntimeError):
    """Raised when a base diagram cannot support the requested mutations."""


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------
def _q(tag: str) -> str:
    return f"{{{BPMN_NS}}}{tag}"


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _is_node_element(element: ET.Element) -> bool:
    return _local(element.tag) in _NODE_TAGS


def _main_process(root: ET.Element) -> ET.Element:
    processes = [child for child in list(root) if _local(child.tag) == "process"]
    if not processes:
        raise GeneratorError("base diagram contains no <process>")

    def score(process: ET.Element) -> int:
        return sum(1 for child in list(process) if _is_node_element(child))

    return max(processes, key=score)


def _sync_io(process: ET.Element) -> None:
    """Rebuild BPMN ``incoming``/``outgoing`` children from sequence flows.

    The generator changes endpoints in several mutations.  Rebuilding the
    cross-references is less error-prone than patching them in every mutation.
    The parser does not read these children, but keeping them correct preserves
    a valid, tool-openable BPMN document.
    """
    nodes = {
        element.get("id"): element
        for element in list(process)
        if _is_node_element(element) and element.get("id")
    }
    for element in nodes.values():
        for child in list(element):
            if _local(child.tag) in {"incoming", "outgoing"}:
                element.remove(child)

    for flow in list(process):
        if _local(flow.tag) != "sequenceFlow":
            continue
        source = nodes.get(flow.get("sourceRef", ""))
        target = nodes.get(flow.get("targetRef", ""))
        if source is not None:
            ET.SubElement(source, _q("outgoing")).text = flow.get("id", "")
        if target is not None:
            ET.SubElement(target, _q("incoming")).text = flow.get("id", "")


# ---------------------------------------------------------------------------
# Mutation planning
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class MutationSpec:
    kind: str
    params: dict[str, Any] = field(default_factory=dict)


_BASE_PRIORITIES = (
    # 56
    (
        "rename_node",
        "insert_node",
        "node_type_change",
        "rename_lane",
        "marker_change",
        "move_lane",
        "gateway_type_change",
        "flow_condition_change",
        "data_change",
        "insert_flow",
        "delete_node",
        "rename_node_synonym",
    ),
    # 57
    (
        "insert_node",
        "delete_node",
        "flow_condition_change",
        "data_change",
        "rename_node",
        "marker_change",
        "move_lane",
        "rename_lane",
        "insert_flow",
        "node_type_change",
        "rename_node_synonym",
        "gateway_type_change",
    ),
    # 58
    (
        "marker_change",
        "move_lane",
        "rename_node_synonym",
        "insert_flow",
        "rename_lane",
        "node_type_change",
        "delete_node",
        "insert_node",
        "data_change",
        "flow_condition_change",
        "gateway_type_change",
        "rename_node",
    ),
    # 63
    (
        "node_type_change",
        "rename_node",
        "gateway_type_change",
        "insert_node",
        "delete_node",
        "flow_condition_change",
        "marker_change",
        "move_lane",
        "rename_lane",
        "data_change",
        "insert_flow",
        "rename_node_synonym",
    ),
    # 65
    (
        "flow_condition_change",
        "gateway_type_change",
        "insert_node",
        "delete_node",
        "rename_lane",
        "insert_flow",
        "rename_node",
        "node_type_change",
        "marker_change",
        "move_lane",
        "data_change",
        "rename_node_synonym",
    ),
)


_MOVED_NOUNS = {
    "patient": "supplier",
    "room": "vehicle",
    "transaction": "subscription",
    "triage": "audit",
    "payment": "shipment",
    "medical": "financial",
    "database": "archive",
    "information": "instructions",
    "query": "report",
    "registration": "membership",
}

_SYNONYM_SWAPS = {
    "wants": "needs",
    "displays": "shows",
    "queries": "searches",
    "selects": "chooses",
    "saves": "stores",
    "enters": "inputs",
    "enter": "input",
    "reads": "views",
    "prints": "outputs",
    "creates": "makes",
}

_LANE_NEW_NAMES = {
    "FO": "Front Office",
    "ED": "Emergency Desk",
    "Cashier": "Cashier Desk",
    "System": "Back Office",
}


def _meaning_rename(name: str) -> str:
    lowered = name.lower()
    for token, replacement in _MOVED_NOUNS.items():
        if token in lowered:
            return name.replace(token, replacement).replace(token.title(), replacement.title())
    return f"{name} for suppliers"


def _synonym_rename(name: str) -> str:
    for token, replacement in _SYNONYM_SWAPS.items():
        if token in name.lower():
            return name.replace(token, replacement).replace(token.title(), replacement.title())
    return f"{name} record"


def _unique_name(candidate: str, existing: Iterable[str]) -> str:
    names = {normalize_label(name) for name in existing if name.strip()}
    if normalize_label(candidate) not in names:
        return candidate
    index = 2
    while normalize_label(f"{candidate} {index}") in names:
        index += 1
    return f"{candidate} {index}"


def _free_tasks(
    reference: ProcessModel, used: set[str], *, unique_only: bool = False
) -> list:
    names = Counter(node.name for node in reference.nodes.values())
    tasks = [
        node
        for node in reference.nodes.values()
        if node.kind == "task"
        and node.id not in used
        and node.name.strip()
        and "invisible" not in node.name.lower()
        and (not unique_only or names[node.name] == 1)
    ]
    return sorted(tasks, key=lambda node: node.id)


def _free_edges(reference: ProcessModel, used: set[str]) -> list:
    edges = [
        edge
        for edge in reference.edges
        if edge.id not in used and not edge.is_default
    ]
    return sorted(edges, key=lambda edge: edge.id)


def _make_candidate(
    kind: str,
    reference: ProcessModel,
    used_nodes: set[str],
    used_edges: set[str],
    used_lane: str | None,
    base_index: int,
) -> MutationSpec | None:
    names = [node.name for node in reference.nodes.values()]

    if kind in {"rename_node", "rename_node_synonym"}:
        tasks = _free_tasks(reference, used_nodes, unique_only=True)
        if not tasks:
            tasks = _free_tasks(reference, used_nodes)
        if not tasks:
            return None
        node = tasks[0]
        new_name = (
            _meaning_rename(node.name)
            if kind == "rename_node"
            else _synonym_rename(node.name)
        )
        new_name = _unique_name(new_name, names)
        used_nodes.add(node.id)
        return MutationSpec(kind, {"node_id": node.id, "new_name": new_name})

    if kind == "insert_node":
        edges = [
            edge
            for edge in _free_edges(reference, used_edges)
            if not _is_invisible_id(reference, edge.source)
            and not _is_invisible_id(reference, edge.target)
        ]
        if not edges:
            return None
        edge = edges[0]
        used_edges.add(edge.id)
        new_name = _unique_name(f"Adds verification step {base_index + 1}", names)
        return MutationSpec(
            kind,
            {"edge_id": edge.id, "new_name": new_name, "new_id": f"Mut_Node_{base_index + 1}"},
        )

    if kind == "delete_node":
        names_count = Counter(node.name for node in reference.nodes.values())
        eligible = [
            node
            for node in _free_tasks(reference, used_nodes, unique_only=True)
            if names_count[node.name] == 1
            and reference.in_degree(node.id) == 1
            and reference.out_degree(node.id) == 1
            and all(
                edge.id not in used_edges
                for edge in reference.in_edges(node.id) + reference.out_edges(node.id)
            )
        ]
        if not eligible:
            return None
        node = eligible[0]
        used_nodes.add(node.id)
        for edge in reference.in_edges(node.id) + reference.out_edges(node.id):
            used_edges.add(edge.id)
        return MutationSpec(
            kind,
            {
                "node_id": node.id,
                "new_flow_id": f"Mut_Flow_Delete_{base_index + 1}",
            },
        )

    if kind == "node_type_change":
        tasks = _free_tasks(reference, used_nodes, unique_only=True)
        if not tasks:
            tasks = _free_tasks(reference, used_nodes)
        if not tasks:
            return None
        node = tasks[0]
        used_nodes.add(node.id)
        return MutationSpec(kind, {"node_id": node.id, "new_tag": "userTask"})

    if kind == "marker_change":
        tasks = _free_tasks(reference, used_nodes, unique_only=True)
        if not tasks:
            tasks = _free_tasks(reference, used_nodes)
        if not tasks:
            return None
        node = tasks[0]
        used_nodes.add(node.id)
        return MutationSpec(kind, {"node_id": node.id})

    if kind == "move_lane":
        if used_lane is not None or len(reference.lanes) < 2:
            return None
        tasks = [
            node
            for node in _free_tasks(reference, used_nodes, unique_only=True)
            if node.lane in reference.lanes
        ]
        if not tasks:
            return None
        node = tasks[0]
        target = sorted(lane for lane in reference.lanes if lane != node.lane)[0]
        used_nodes.add(node.id)
        return MutationSpec(
            kind,
            {"node_id": node.id, "target_lane": target, "source_lane": node.lane},
        )

    if kind == "rename_lane":
        if used_lane is not None or not reference.lanes:
            return None
        lane = sorted(reference.lanes)[0]
        new_name = _LANE_NEW_NAMES.get(lane, f"{lane} Desk")
        while new_name in reference.lanes:
            new_name = f"{new_name} 2"
        return MutationSpec(kind, {"lane_name": lane, "new_name": new_name})

    if kind == "gateway_type_change":
        gateways = [
            node
            for node in reference.nodes.values()
            if node.kind == "xor" and node.id not in used_nodes
        ]
        signatures = Counter(
            (reference.in_degree(node.id), reference.out_degree(node.id))
            for node in reference.nodes.values()
            if node.kind == "xor"
        )
        unique = [
            node
            for node in gateways
            if signatures[(reference.in_degree(node.id), reference.out_degree(node.id))] == 1
        ]
        if not unique:
            return None
        node = sorted(unique, key=lambda item: item.id)[0]
        used_nodes.add(node.id)
        return MutationSpec(kind, {"node_id": node.id, "new_tag": "parallelGateway"})

    if kind == "flow_condition_change":
        branching = [
            edge
            for edge in _free_edges(reference, used_edges)
            if reference.out_degree(edge.source) >= 2
        ]
        edges = branching or _free_edges(reference, used_edges)
        if not edges:
            return None
        edge = edges[0]
        used_edges.add(edge.id)
        return MutationSpec(
            kind,
            {"flow_id": edge.id, "condition": f"amount > {base_index + 1}"},
        )

    if kind == "insert_flow":
        edges = [
            edge
            for edge in _free_edges(reference, used_edges)
            if edge.source != edge.target
        ]
        if not edges:
            return None
        edge = edges[0]
        used_edges.add(edge.id)
        return MutationSpec(
            kind,
            {
                "source": edge.source,
                "target": edge.target,
                "new_flow_id": f"Mut_Flow_Duplicate_{base_index + 1}",
            },
        )

    if kind == "data_change":
        existing = {element.name for element in reference.data_elements.values()}
        name = f"Audit log {base_index + 1}"
        while name in existing:
            name = f"{name} 2"
        return MutationSpec(kind, {"name": name, "new_id": f"Mut_Data_{base_index + 1}"})

    return None


def _is_invisible_id(reference: ProcessModel, node_id: str) -> bool:
    node = reference.nodes.get(node_id)
    return bool(node and "invisible" in node.name.lower())


def plan_mutations(reference: ProcessModel, base_index: int, k_max: int = 4) -> list[MutationSpec]:
    """Choose deterministic, non-conflicting mutations for one base diagram."""
    priority = _BASE_PRIORITIES[base_index % len(_BASE_PRIORITIES)]
    used_nodes: set[str] = set()
    used_edges: set[str] = set()
    used_lane: str | None = None
    selected: list[MutationSpec] = []

    for kind in priority:
        if len(selected) >= k_max:
            break
        spec = _make_candidate(kind, reference, used_nodes, used_edges, used_lane, base_index)
        if spec is None:
            continue
        if kind in {"move_lane", "rename_lane"}:
            used_lane = kind
        selected.append(spec)

    if len(selected) < k_max:
        raise GeneratorError(
            f"base can only host {len(selected)} non-conflicting mutations; "
            f"{k_max} requested"
        )
    return selected


# ---------------------------------------------------------------------------
# XML mutator
# ---------------------------------------------------------------------------
class DiagramMutator:
    """Applies mutation specs to an XML tree and tracks element identity."""

    def __init__(self, path: str | Path, base_index: int) -> None:
        self.path = Path(path)
        self.tree = ET.parse(str(path))
        self.root = self.tree.getroot()
        self.process = _main_process(self.root)
        self.reference = load_model(str(path))
        self.base_index = base_index
        self.node_origin: dict[str, str | None] = {
            node_id: node_id for node_id in self.reference.nodes
        }
        self.lane_origin: dict[str, str | None] = {
            lane: lane for lane in self.reference.lanes
        }
        self._sequence = 0

    # -- lookups ----------------------------------------------------------
    def _nodes(self) -> dict[str, ET.Element]:
        return {
            element.get("id", ""): element
            for element in list(self.process)
            if _is_node_element(element) and element.get("id")
        }

    def _flows(self) -> dict[str, ET.Element]:
        return {
            element.get("id", ""): element
            for element in list(self.process)
            if _local(element.tag) == "sequenceFlow" and element.get("id")
        }

    def _lanes(self) -> dict[str, ET.Element]:
        return {
            element.get("id", ""): element
            for element in self.process.iter()
            if _local(element.tag) == "lane" and element.get("id")
        }

    def _lane_by_name(self, name: str) -> ET.Element | None:
        for element in self._lanes().values():
            if element.get("name", "") == name:
                return element
        return None

    def _shapes(self) -> dict[str, ET.Element]:
        return {
            element.get("bpmnElement", ""): element
            for element in self.root.iter()
            if _local(element.tag) == "BPMNShape" and element.get("bpmnElement")
        }

    def _bounds(self, shape: ET.Element) -> ET.Element | None:
        for child in list(shape):
            if _local(child.tag) == "Bounds":
                return child
        return None

    def _plane(self) -> ET.Element | None:
        for element in self.root.iter():
            if _local(element.tag) == "BPMNPlane":
                return element
        return None

    def _new_id(self, prefix: str) -> str:
        self._sequence += 1
        return f"Mut_{prefix}_{self._sequence}"

    # -- diagram interchange ----------------------------------------------
    #
    # The converted BizAgi exports carry a DI plane, and the parser recovers
    # lanes from shape geometry.  Structural mutations must therefore keep the
    # plane consistent: dangling ``bpmnElement`` references make the file
    # invalid for BPMN tooling, and a moved shape without DI silently falls
    # back to its old lane.  These helpers add or drop the minimal shapes and
    # edges needed to stay consistent.
    def _remove_di(self, element_id: str) -> None:
        for parent in list(self.root.iter()):
            for child in list(parent):
                if (
                    _local(child.tag) in {"BPMNShape", "BPMNEdge"}
                    and child.get("bpmnElement") == element_id
                ):
                    parent.remove(child)

    def _center(self, element_id: str) -> tuple[float, float] | None:
        shape = self._shapes().get(element_id)
        if shape is None:
            return None
        bounds = self._bounds(shape)
        if bounds is None:
            return None
        return (
            float(bounds.get("x", 0)) + float(bounds.get("width", 0)) / 2,
            float(bounds.get("y", 0)) + float(bounds.get("height", 0)) / 2,
        )

    def _add_shape(
        self, element_id: str, x: float, y: float, width: float = 100.0, height: float = 80.0
    ) -> None:
        plane = self._plane()
        if plane is None:
            return
        shape = ET.SubElement(
            plane,
            f"{{{BPMNDI_NS}}}BPMNShape",
            {"id": self._new_id("Shape"), "bpmnElement": element_id},
        )
        ET.SubElement(
            shape,
            f"{{{DC_NS}}}Bounds",
            {
                "x": f"{x:g}",
                "y": f"{y:g}",
                "width": f"{width:g}",
                "height": f"{height:g}",
            },
        )

    def _add_edge(self, flow_id: str, source_id: str, target_id: str) -> None:
        plane = self._plane()
        if plane is None:
            return
        source = self._center(source_id)
        target = self._center(target_id)
        if source is None or target is None:
            return
        edge = ET.SubElement(
            plane,
            f"{{{BPMNDI_NS}}}BPMNEdge",
            {"id": self._new_id("Edge"), "bpmnElement": flow_id},
        )
        for x, y in (source, target):
            ET.SubElement(
                edge, f"{{{DI_NS}}}waypoint", {"x": f"{x:g}", "y": f"{y:g}"}
            )

    # -- mutations --------------------------------------------------------
    def apply(self, spec: MutationSpec) -> dict[str, Any]:
        handler = getattr(self, f"_apply_{spec.kind}")
        return handler(**spec.params)

    def _apply_rename_node(self, node_id: str, new_name: str) -> dict[str, Any]:
        element = self._nodes()[node_id]
        before = element.get("name", "")
        element.set("name", new_name)
        return {"kind": "rename_node", "node_id": node_id, "before": before, "after": new_name}

    def _apply_rename_node_synonym(self, node_id: str, new_name: str) -> dict[str, Any]:
        record = self._apply_rename_node(node_id, new_name)
        record["kind"] = "rename_node_synonym"
        return record

    def _apply_insert_node(
        self, edge_id: str, new_name: str, new_id: str
    ) -> dict[str, Any]:
        flows = self._flows()
        flow = flows[edge_id]
        source = flow.get("sourceRef", "")
        target = flow.get("targetRef", "")
        new_id = self._unique_element_id(new_id)
        node = ET.Element(_q("task"), {"id": new_id, "name": new_name})
        self.process.append(node)
        flow.set("targetRef", new_id)
        new_flow = ET.Element(
            _q("sequenceFlow"),
            {
                "id": self._unique_element_id(f"{new_id}_Flow"),
                "sourceRef": new_id,
                "targetRef": target,
            },
        )
        self.process.append(new_flow)
        self.node_origin[new_id] = None

        # Place the new shape just before its successor and keep the diagram
        # interchange consistent with the two affected sequence flows.
        target_shape = self._shapes().get(target)
        target_bounds = self._bounds(target_shape) if target_shape is not None else None
        if target_bounds is not None:
            x = float(target_bounds.get("x", 0)) - 140.0
            y = float(target_bounds.get("y", 0))
            self._add_shape(new_id, x, y)
        self._remove_di(edge_id)
        self._add_edge(edge_id, source, new_id)
        self._add_edge(new_flow.get("id", ""), new_id, target)
        return {
            "kind": "insert_node",
            "node_id": new_id,
            "name": new_name,
            "after_node": target,
            "edge_id": edge_id,
        }

    def _apply_delete_node(self, node_id: str, new_flow_id: str) -> dict[str, Any]:
        nodes = self._nodes()
        element = nodes[node_id]
        incoming = self.reference.in_edges(node_id)
        outgoing = self.reference.out_edges(node_id)
        source = incoming[0].source
        target = outgoing[0].target
        flows = self._flows()
        for edge in incoming + outgoing:
            flow = flows.get(edge.id)
            if flow is not None:
                self.process.remove(flow)
            self._remove_di(edge.id)
        # Bizagi links data stores to tasks with <association> elements; those
        # references dangle once the task disappears.
        for child in list(self.process):
            if (
                _local(child.tag) == "association"
                and node_id in {child.get("sourceRef"), child.get("targetRef")}
            ):
                self.process.remove(child)
                self._remove_di(child.get("id", ""))
        self.process.remove(element)
        self._remove_di(node_id)
        self.node_origin.pop(node_id, None)
        new_flow_id = self._unique_element_id(new_flow_id)
        self.process.append(
            ET.Element(
                _q("sequenceFlow"),
                {"id": new_flow_id, "sourceRef": source, "targetRef": target},
            )
        )
        self._add_edge(new_flow_id, source, target)
        return {
            "kind": "delete_node",
            "node_id": node_id,
            "name": element.get("name", ""),
            "reconnect": {"source": source, "target": target},
        }

    def _apply_node_type_change(self, node_id: str, new_tag: str) -> dict[str, Any]:
        element = self._nodes()[node_id]
        old_tag = _local(element.tag)
        element.tag = _q(new_tag)
        return {"kind": "node_type_change", "node_id": node_id, "before": old_tag, "after": new_tag}

    def _apply_marker_change(self, node_id: str) -> dict[str, Any]:
        element = self._nodes()[node_id]
        ET.SubElement(element, _q("standardLoopCharacteristics"))
        return {"kind": "marker_change", "node_id": node_id, "marker": "loop"}

    def _apply_gateway_type_change(self, node_id: str, new_tag: str) -> dict[str, Any]:
        element = self._nodes()[node_id]
        old_tag = _local(element.tag)
        element.tag = _q(new_tag)
        return {
            "kind": "gateway_type_change",
            "node_id": node_id,
            "before": old_tag,
            "after": new_tag,
        }

    def _apply_flow_condition_change(self, flow_id: str, condition: str) -> dict[str, Any]:
        flow = self._flows()[flow_id]
        existing = next(
            (child for child in list(flow) if _local(child.tag) == "conditionExpression"),
            None,
        )
        if existing is not None:
            flow.remove(existing)
        expression = ET.SubElement(
            flow,
            _q("conditionExpression"),
            {f"{{{XSI_NS}}}type": "tFormalExpression"},
        )
        expression.text = condition
        return {"kind": "flow_condition_change", "flow_id": flow_id, "condition": condition}

    def _apply_insert_flow(self, source: str, target: str, new_flow_id: str) -> dict[str, Any]:
        new_flow_id = self._unique_element_id(new_flow_id)
        self.process.append(
            ET.Element(
                _q("sequenceFlow"),
                {"id": new_flow_id, "sourceRef": source, "targetRef": target},
            )
        )
        self._add_edge(new_flow_id, source, target)
        return {
            "kind": "insert_flow",
            "flow_id": new_flow_id,
            "source": source,
            "target": target,
        }

    def _apply_data_change(self, name: str, new_id: str) -> dict[str, Any]:
        new_id = self._unique_element_id(new_id)
        element = ET.Element(_q("dataObject"), {"id": new_id, "name": name})
        self.process.append(element)
        return {"kind": "data_change", "data_id": new_id, "name": name}

    def _apply_rename_lane(self, lane_name: str, new_name: str) -> dict[str, Any]:
        lane = self._lane_by_name(lane_name)
        if lane is None:
            raise GeneratorError(f"lane {lane_name!r} not found")
        lane.set("name", new_name)
        origin = self.lane_origin.pop(lane_name, lane_name)
        self.lane_origin[new_name] = origin
        return {"kind": "rename_lane", "before": lane_name, "after": new_name}

    def _apply_move_lane(
        self, node_id: str, target_lane: str, source_lane: str
    ) -> dict[str, Any]:
        # Prefer explicit flowNodeRef membership when the document has it.
        target_element = self._lane_by_name(target_lane)
        source_element = self._lane_by_name(source_lane)
        moved_ref = False
        if source_element is not None and target_element is not None:
            for child in list(source_element):
                if _local(child.tag) == "flowNodeRef" and (child.text or "").strip() == node_id:
                    source_element.remove(child)
                    ET.SubElement(target_element, _q("flowNodeRef")).text = node_id
                    moved_ref = True

        # BizAgi's converted diagrams use DI geometry instead of flowNodeRef.
        shapes = self._shapes()
        lane_id = target_element.get("id", "") if target_element is not None else ""
        lane_shape = shapes.get(lane_id)
        node_shape = shapes.get(node_id)
        if lane_shape is not None and node_shape is not None:
            lane_bounds = self._bounds(lane_shape)
            node_bounds = self._bounds(node_shape)
            if lane_bounds is not None and node_bounds is not None:
                lane_y = float(lane_bounds.get("y", 0))
                lane_height = float(lane_bounds.get("height", 0))
                node_height = float(node_bounds.get("height", 0))
                node_bounds.set("y", str(lane_y + max(0.0, (lane_height - node_height) / 2)))
                moved_ref = True

        if not moved_ref:
            raise GeneratorError(f"could not move {node_id!r} into lane {target_lane!r}")
        return {
            "kind": "move_lane",
            "node_id": node_id,
            "before": source_lane,
            "after": target_lane,
        }

    # -- IDs and serialization -------------------------------------------
    def _unique_element_id(self, candidate: str) -> str:
        taken = {element.get("id") for element in self.root.iter() if element.get("id")}
        value = candidate
        index = 2
        while value in taken:
            value = f"{candidate}_{index}"
            index += 1
        return value

    def _rewrite_ids(self, salt: str) -> dict[str, str]:
        elements = [element for element in self.root.iter() if element.get("id")]
        mapping: dict[str, str] = {}
        for element in elements:
            old = element.get("id", "")
            digest = hashlib.sha1(f"{salt}:{old}".encode("utf-8")).hexdigest()[:16]
            mapping[old] = f"Id_{digest}"

        # Rewrite references first, while the old->new map is still complete.
        # Any ``*Ref``/``*Refs`` attribute or text node can carry an ID (for
        # example ``dataInputRefs``), so match by suffix rather than by an
        # exhaustive list that Bizagi extensions could outgrow.
        for element in self.root.iter():
            for attribute, value in list(element.attrib.items()):
                if (
                    attribute in _IDREF_ATTRIBUTES or attribute.endswith("Ref")
                ) and value in mapping:
                    element.set(attribute, mapping[value])
            name = _local(element.tag)
            if element.text and (
                name in _IDREF_TEXT_TAGS
                or name.endswith("Ref")
                or name.endswith("Refs")
            ):
                text = element.text.strip()
                if text in mapping:
                    element.text = mapping[text]
        for element in elements:
            old = element.get("id", "")
            element.set("id", mapping[old])

        self.node_origin = {
            mapping.get(current, current): origin
            for current, origin in self.node_origin.items()
        }
        return mapping

    def finish(self, output: str | Path, *, rewrite_ids: bool, salt: str) -> dict[str, Any]:
        _sync_io(self.process)
        id_map: dict[str, str] = {}
        if rewrite_ids:
            id_map = self._rewrite_ids(salt)
        self.tree.write(str(output), encoding="utf-8", xml_declaration=True)
        variant = load_model(str(output))
        node_map = {
            variant_id: origin
            for variant_id, origin in self.node_origin.items()
            if origin is not None
        }
        lane_map = {
            lane: origin
            for lane, origin in self.lane_origin.items()
            if origin is not None
        }
        return {
            "variant_model": variant,
            "node_map": node_map,
            "lane_map": lane_map,
            "id_map": id_map,
        }


# ---------------------------------------------------------------------------
# Ground truth
# ---------------------------------------------------------------------------
def _node_payload(model: ProcessModel, node_id: str) -> dict[str, Any]:
    node = model.nodes[node_id]
    return {
        "id": node.id,
        "name": node.display_name,
        "kind": node.kind,
        "task_type": node.task_type,
        "event_definition": node.event_definition,
        "marker": node.marker,
        "lane": node.lane,
        "pool": node.pool,
    }


def _flow_payload(model: ProcessModel, edge) -> dict[str, Any]:
    return {
        "source": model.nodes[edge.source].display_name,
        "target": model.nodes[edge.target].display_name,
        "source_id": edge.source,
        "target_id": edge.target,
        "condition": edge.condition,
        "is_default": edge.is_default,
    }


def _envelope(
    change_type: str,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
    detail: str,
    *,
    label: str | None = None,
    subtype: str | None = None,
    is_synonym: bool | None = None,
    score: float | None = None,
) -> dict[str, Any]:
    category = _CATEGORY_OF[change_type]
    change: dict[str, Any] = {
        "type": change_type,
        "legacy_type": _LEGACY_TYPES.get(change_type, change_type),
        "category": category,
        "category_name": _CATEGORY_NAMES[category],
        "element": _ELEMENT_OF[change_type],
        "before": before,
        "after": after,
        "detail": detail,
        "confidence": "high",
        "needs_review": False,
    }
    if label is not None:
        change["label"] = label
    if subtype is not None:
        change["subtype"] = subtype
    if is_synonym is not None:
        change["is_synonym"] = is_synonym
    if score is not None:
        change["score"] = round(score, 3)
    record = {
        "schema_version": "change-v1",
        "change": change,
        "evidence": {
            "alignment": [],
            "structural_context": [],
            "observations": [
                {
                    "source": "operation",
                    "description": detail,
                    "value": {"before": before, "after": after},
                }
            ],
        },
    }
    validate_change_record(record)
    return record


def _rename_subtype(reference_name: str, variant_name: str) -> tuple[str, float]:
    score, _ = label_similarity(reference_name, variant_name)
    subtype = "synonym" if score >= 0.72 else "meaning_changed"
    return subtype, score


def build_ground_truth(
    reference: ProcessModel,
    variant: ProcessModel,
    node_map: dict[str, str],
    lane_map: dict[str, str],
) -> list[dict[str, Any]]:
    """Derive the ideal change set from known element identity."""
    records: list[dict[str, Any]] = []
    matched_a = set(node_map.values())
    matched_b = set(node_map)

    # Category 1 — steps, node types, markers.
    for node_id in sorted(reference.nodes):
        if node_id not in matched_a:
            node = reference.nodes[node_id]
            records.append(
                _envelope(
                    "DELETE_NODE",
                    _node_payload(reference, node_id),
                    None,
                    f"removed {node.kind}: {node.display_name}",
                    label="unmatched",
                )
            )

    for node_id in sorted(variant.nodes):
        if node_id not in matched_b:
            node = variant.nodes[node_id]
            records.append(
                _envelope(
                    "INSERT_NODE",
                    None,
                    _node_payload(variant, node_id),
                    f"added {node.kind}: {node.display_name}",
                    label="unmatched",
                )
            )

    for variant_id, reference_id in sorted(node_map.items(), key=lambda item: item[1]):
        before = reference.nodes[reference_id]
        after = variant.nodes[variant_id]

        if normalize_label(before.name) != normalize_label(after.name) and (
            before.name.strip() or after.name.strip()
        ):
            subtype, score = _rename_subtype(before.name, after.name)
            records.append(
                _envelope(
                    "RENAME_NODE",
                    _node_payload(reference, reference_id),
                    _node_payload(variant, variant_id),
                    f'"{before.display_name}" -> "{after.display_name}" ({subtype})',
                    label=subtype,
                    subtype=subtype,
                    is_synonym=subtype == "synonym",
                    score=score,
                )
            )

        if before.is_gateway and after.is_gateway and before.kind != after.kind:
            records.append(
                _envelope(
                    "GATEWAY_TYPE_CHANGE",
                    _node_payload(reference, reference_id),
                    _node_payload(variant, variant_id),
                    f"{before.kind.upper()} -> {after.kind.upper()}",
                )
            )
        elif before.family != after.family:
            records.append(
                _envelope(
                    "NODE_TYPE_CHANGE",
                    _node_payload(reference, reference_id),
                    _node_payload(variant, variant_id),
                    f"{before.kind} -> {after.kind}",
                )
            )
        elif (
            before.family == "task"
            and after.family == "task"
            and before.task_type != after.task_type
            and (before.task_type != "abstract" or after.task_type != "abstract")
        ):
            records.append(
                _envelope(
                    "NODE_TYPE_CHANGE",
                    _node_payload(reference, reference_id),
                    _node_payload(variant, variant_id),
                    f"{before.task_type} task -> {after.task_type} task",
                )
            )
        elif (
            before.family == "event"
            and after.family == "event"
            and (
                before.event_definition != after.event_definition
                or before.kind != after.kind
            )
        ):
            records.append(
                _envelope(
                    "NODE_TYPE_CHANGE",
                    _node_payload(reference, reference_id),
                    _node_payload(variant, variant_id),
                    f"{before.event_definition} {before.kind} -> "
                    f"{after.event_definition} {after.kind}",
                )
            )

        if before.marker != after.marker:
            records.append(
                _envelope(
                    "MARKER_CHANGE",
                    _node_payload(reference, reference_id),
                    _node_payload(variant, variant_id),
                    f'marker: "{before.marker}" -> "{after.marker}"',
                )
            )

        canonical_lane = lane_map.get(after.lane, after.lane)
        if before.lane != canonical_lane:
            records.append(
                _envelope(
                    "MOVE_LANE",
                    _node_payload(reference, reference_id),
                    _node_payload(variant, variant_id),
                    f'{before.display_name}: "{before.lane or "(unassigned)"}" -> '
                    f'"{after.lane or "(unassigned)"}"',
                )
            )

    # Category 2 — lane renames and lane insert/delete.
    for variant_lane, reference_lane in sorted(lane_map.items()):
        if reference_lane != variant_lane:
            records.append(
                _envelope(
                    "RENAME_LANE",
                    {"name": reference_lane},
                    {"name": variant_lane},
                    f'"{reference_lane}" -> "{variant_lane}"',
                )
            )
    reference_lane_origins = {
        origin for origin in lane_map.values() if origin is not None
    }
    for variant_lane in sorted(set(variant.lanes) - set(lane_map)):
        records.append(
            _envelope(
                "INSERT_LANE",
                None,
                {"name": variant_lane},
                f'lane added: "{variant_lane}"',
            )
        )
    for reference_lane in sorted(set(reference.lanes) - reference_lane_origins):
        records.append(
            _envelope(
                "DELETE_LANE",
                {"name": reference_lane},
                None,
                f'lane removed: "{reference_lane}"',
            )
        )

    # Category 3 — flows between matched nodes.  The detector reports flows to
    # inserted nodes (both endpoints exist in the variant) but suppresses flows
    # incident to deleted reference nodes, because those edges have no matched
    # source/target pair.  Mirror that asymmetry here.
    reference_edges = Counter(
        (edge.source, edge.target)
        for edge in reference.edges
        if edge.source in matched_a and edge.target in matched_a
    )
    variant_edges = Counter(
        (node_map.get(edge.source, edge.source), node_map.get(edge.target, edge.target))
        for edge in variant.edges
    )
    reference_by_pair = {
        (edge.source, edge.target): edge
        for edge in reference.edges
        if edge.source in matched_a and edge.target in matched_a
    }
    variant_by_pair = {
        (node_map.get(edge.source, edge.source), node_map.get(edge.target, edge.target)): edge
        for edge in variant.edges
    }

    for (source, target), count in sorted((reference_edges - variant_edges).items()):
        edge = reference_by_pair[(source, target)]
        records.append(
            _envelope(
                "DELETE_FLOW",
                _flow_payload(reference, edge),
                None,
                f'flow removed from "{reference.nodes[source].display_name}" to '
                f'"{reference.nodes[target].display_name}" ({count}x)',
                label="unmatched",
            )
        )
    for (source, target), count in sorted((variant_edges - reference_edges).items()):
        edge = variant_by_pair[(source, target)]
        records.append(
            _envelope(
                "INSERT_FLOW",
                None,
                _flow_payload(variant, edge),
                f'flow added from "{variant.nodes[edge.source].display_name}" to '
                f'"{variant.nodes[edge.target].display_name}" ({count}x)',
                label="unmatched",
            )
        )
    for pair in sorted(set(reference_by_pair) & set(variant_by_pair)):
        reference_edge = reference_by_pair[pair]
        variant_edge = variant_by_pair[pair]
        if (
            reference_edge.condition != variant_edge.condition
            or reference_edge.is_default != variant_edge.is_default
        ):
            records.append(
                _envelope(
                    "FLOW_CONDITION_CHANGE",
                    _flow_payload(reference, reference_edge),
                    _flow_payload(variant, variant_edge),
                    f'condition: "{reference_edge.condition}" -> '
                    f'"{variant_edge.condition}"',
                )
            )

    # Category 5 — message flows and data elements.
    reference_messages = {
        (flow.source, flow.target): flow for flow in reference.message_flows
    }
    variant_messages = {
        (node_map.get(flow.source, flow.source), node_map.get(flow.target, flow.target)): flow
        for flow in variant.message_flows
    }
    for pair, flow in sorted(variant_messages.items()):
        if pair not in reference_messages:
            records.append(
                _envelope(
                    "MESSAGE_FLOW_CHANGE",
                    None,
                    {"source": pair[0], "target": pair[1], "name": flow.name},
                    f'message flow added from "{pair[0]}" to "{pair[1]}"',
                )
            )
    for pair, flow in sorted(reference_messages.items()):
        if pair not in variant_messages:
            records.append(
                _envelope(
                    "MESSAGE_FLOW_CHANGE",
                    {"source": pair[0], "target": pair[1], "name": flow.name},
                    None,
                    f'message flow removed from "{pair[0]}" to "{pair[1]}"',
                )
            )

    reference_data = {
        element.name: element
        for element in reference.data_elements.values()
        if element.name
    }
    variant_data = {
        element.name: element
        for element in variant.data_elements.values()
        if element.name
    }
    for name in sorted(set(variant_data) - set(reference_data)):
        element = variant_data[name]
        records.append(
            _envelope(
                "DATA_CHANGE",
                None,
                element.to_dict(),
                f'{element.kind.replace("_", " ")} added: "{element.name}"',
            )
        )
    for name in sorted(set(reference_data) - set(variant_data)):
        element = reference_data[name]
        records.append(
            _envelope(
                "DATA_CHANGE",
                element.to_dict(),
                None,
                f'{element.kind.replace("_", " ")} removed: "{element.name}"',
            )
        )

    records.sort(
        key=lambda record: (
            record["change"]["category"],
            record["change"]["type"],
            str(record["change"].get("before") or record["change"].get("after")),
        )
    )
    return records


# ---------------------------------------------------------------------------
# Dataset builder
# ---------------------------------------------------------------------------
def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _display_path(path: Path) -> str:
    """Prefer a repository-relative path so committed manifests stay portable."""
    resolved = path.resolve()
    repo = Path(__file__).resolve().parent.parent
    try:
        return resolved.relative_to(repo).as_posix()
    except ValueError:
        return str(resolved)


def generate_dataset(
    dataset_dir: str | Path,
    out_dir: str | Path,
    *,
    bases: Iterable[str] = DEFAULT_BASES,
    k_values: Iterable[int] = K_VALUES,
    policies: Iterable[str] = ID_POLICIES,
    seed: str = "bpmndiff",
) -> dict[str, Any]:
    dataset = Path(dataset_dir)
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "schema": "bpmndiff-synthetic-v1",
        "seed": seed,
        "base_dataset": _display_path(dataset),
        "bases": [],
    }

    for fallback_index, base_id in enumerate(bases):
        base_index = (
            DEFAULT_BASES.index(base_id) if base_id in DEFAULT_BASES else fallback_index
        )
        source = dataset / f"{base_id}.bpmn"
        if not source.is_file():
            candidates = sorted(dataset.glob(f"{base_id}*.bpmn"))
            if not candidates:
                raise GeneratorError(f"base diagram {base_id!r} not found in {dataset}")
            source = candidates[0]

        reference = load_model(str(source))
        specs = plan_mutations(reference, base_index, k_max=max(k_values))
        base_output = output / base_id
        base_output.mkdir(parents=True, exist_ok=True)
        reference_copy = base_output / "reference.bpmn"
        shutil.copyfile(source, reference_copy)

        base_entry: dict[str, Any] = {
            "base_id": base_id,
            "source": _display_path(source),
            "reference": _relative(reference_copy, output),
            "reference_model": {
                "name": reference.name,
                "nodes": len(reference.nodes),
                "edges": len(reference.edges),
                "lanes": list(reference.lanes),
            },
            "variants": [],
        }

        for k in k_values:
            selected = specs[:k]
            for policy in policies:
                mutator = DiagramMutator(source, base_index)
                mutation_records = [mutator.apply(spec) for spec in selected]
                variant_name = f"k{k}_{policy}"
                variant_path = base_output / f"{variant_name}.bpmn"
                salt = f"{seed}:{base_id}:{variant_name}"
                result = mutator.finish(
                    variant_path,
                    rewrite_ids=policy == "newids",
                    salt=salt,
                )
                variant_model = result["variant_model"]
                node_map = result["node_map"]
                lane_map = result["lane_map"]
                ground_truth = build_ground_truth(
                    reference, variant_model, node_map, lane_map
                )
                gt_path = base_output / f"{variant_name}.groundtruth.json"
                gt_path.write_text(
                    json.dumps(
                        {
                            "schema_version": "change-v1",
                            "dataset": "bpmndiff-synthetic-v1",
                            "base_id": base_id,
                            "variant": variant_name,
                            "k": k,
                            "id_policy": policy,
                            "mutations": mutation_records,
                            "operations": ground_truth,
                        },
                        indent=2,
                        ensure_ascii=False,
                    )
                    + "\n",
                    encoding="utf-8",
                )

                base_entry["variants"].append(
                    {
                        "variant": variant_name,
                        "k": k,
                        "id_policy": policy,
                        "path": _relative(variant_path, output),
                        "ground_truth": _relative(gt_path, output),
                        "mutations": [record["kind"] for record in mutation_records],
                        "node_map": node_map,
                        "lane_map": lane_map,
                        "counts": {
                            "operations": len(ground_truth),
                            "nodes": len(variant_model.nodes),
                            "edges": len(variant_model.edges),
                        },
                    }
                )

        manifest["bases"].append(base_entry)

    manifest_path = output / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def generate_default_dataset(
    *,
    dataset_dir: str | Path | None = None,
    out_dir: str | Path | None = None,
    bases: Iterable[str] = DEFAULT_BASES,
    seed: str = "bpmndiff",
) -> dict[str, Any]:
    repo = Path(__file__).resolve().parent.parent
    dataset = Path(dataset_dir) if dataset_dir else (
        repo
        / "dataset"
        / "BPMN Diagrams Dataset of Functional Requirements"
        / "Converted XPDL"
    )
    output = Path(out_dir) if out_dir else repo / "dataset" / "synthetic"
    return generate_dataset(dataset, output, bases=bases, seed=seed)
