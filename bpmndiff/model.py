"""Normalised, layout-free process model shared by all parsers.

The whole pipeline works on :class:`ProcessModel`.  Visual information
(coordinates, colours, ...) is deliberately discarded at parse time so that
downstream stages only reason about control flow and semantics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


TASK_KINDS = {"task", "subprocess", "call_activity"}
EVENT_KINDS = {"start", "end", "event", "boundary_event"}
GATEWAY_KINDS = {"xor", "and", "or", "complex", "event_based"}

#: A human readable name for every structural node kind.
KIND_LABELS = {
    "task": "task",
    "subprocess": "subprocess",
    "call_activity": "call activity",
    "start": "start event",
    "end": "end event",
    "event": "intermediate event",
    "boundary_event": "boundary event",
    "xor": "exclusive gateway (XOR)",
    "and": "parallel gateway (AND)",
    "or": "inclusive gateway (OR)",
    "complex": "complex gateway",
    "event_based": "event-based gateway",
}


def kind_family(kind: str) -> str:
    """Return the coarse alignment family of a node kind."""
    if kind in TASK_KINDS:
        return "task"
    if kind in EVENT_KINDS:
        return "event"
    if kind in GATEWAY_KINDS:
        return "gateway"
    return "other"


@dataclass
class Node:
    """A flow node (activity, event or gateway)."""

    id: str
    name: str = ""
    kind: str = "task"
    lane: str = ""
    pool: str = ""

    # Extended attributes (future.md)
    task_type: str = "abstract"  # user, service, manual, script, send, receive, business_rule, abstract
    event_definition: str = "none"  # none, message, timer, error, signal, conditional, escalation, compensation, link, terminate
    attached_to: str | None = None  # activity ID for boundary event
    cancel_activity: bool = True    # interrupting (True) vs non-interrupting (False)
    marker: str = "none"            # none, loop, multi_instance_parallel, multi_instance_sequential
    gateway_direction: str = "unspecified"  # split, join, unspecified
    default_flow: str = ""          # ID of default outgoing flow
    submodel_node_ids: list[str] = field(default_factory=list)
    called_element: str = ""

    @property
    def family(self) -> str:
        return kind_family(self.kind)

    @property
    def is_gateway(self) -> bool:
        return self.kind in GATEWAY_KINDS

    @property
    def is_event(self) -> bool:
        return self.kind in EVENT_KINDS

    @property
    def is_boundary(self) -> bool:
        return self.kind == "boundary_event" or self.attached_to is not None

    @property
    def is_subprocess(self) -> bool:
        return self.kind in {"subprocess", "call_activity"}

    @property
    def display_name(self) -> str:
        name = " ".join(self.name.split())
        return name if name else f"<{KIND_LABELS.get(self.kind, self.kind)}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.display_name,
            "kind": self.kind,
            "family": self.family,
            "lane": self.lane,
            "pool": self.pool,
            "task_type": self.task_type,
            "event_definition": self.event_definition,
            "attached_to": self.attached_to,
            "cancel_activity": self.cancel_activity,
            "marker": self.marker,
            "gateway_direction": self.gateway_direction,
            "default_flow": self.default_flow,
            "submodel_node_ids": list(self.submodel_node_ids),
            "called_element": self.called_element,
        }


@dataclass
class Edge:
    """A sequence flow."""

    id: str
    source: str
    target: str
    name: str = ""
    condition: str = ""
    is_default: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "name": self.name,
            "condition": self.condition,
            "is_default": self.is_default,
        }


@dataclass
class MessageFlow:
    """A message flow across pools."""

    id: str
    source: str
    target: str
    name: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "name": self.name,
        }


@dataclass
class DataElement:
    """A data object or data store."""

    id: str
    name: str = ""
    kind: str = "data_object"  # data_object, data_store, data_input, data_output
    connected_nodes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "connected_nodes": list(self.connected_nodes),
        }


@dataclass
class ProcessModel:
    """A single workflow process in canonical form."""

    id: str
    name: str
    source: str = ""
    fmt: str = ""
    pool: str = ""
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    lanes: list[str] = field(default_factory=list)
    message_flows: list[MessageFlow] = field(default_factory=list)
    data_elements: dict[str, DataElement] = field(default_factory=dict)

    # -- construction -----------------------------------------------------
    def add_node(self, node: Node) -> Node:
        self.nodes[node.id] = node
        if node.lane and node.lane not in self.lanes:
            self.lanes.append(node.lane)
        return node

    def add_edge(self, edge: Edge) -> Edge:
        self.edges.append(edge)
        return edge

    def add_message_flow(self, flow: MessageFlow) -> MessageFlow:
        self.message_flows.append(flow)
        return flow

    def add_data_element(self, element: DataElement) -> DataElement:
        self.data_elements[element.id] = element
        return element

    # -- graph helpers ----------------------------------------------------
    def out_edges(self, node_id: str) -> list[Edge]:
        return [e for e in self.edges if e.source == node_id]

    def in_edges(self, node_id: str) -> list[Edge]:
        return [e for e in self.edges if e.target == node_id]

    def successors(self, node_id: str) -> list[str]:
        return [e.target for e in self.out_edges(node_id)]

    def predecessors(self, node_id: str) -> list[str]:
        return [e.source for e in self.in_edges(node_id)]

    def in_degree(self, node_id: str) -> int:
        return len(self.in_edges(node_id))

    def out_degree(self, node_id: str) -> int:
        return len(self.out_edges(node_id))

    def start_nodes(self) -> list[str]:
        starts = [n.id for n in self.nodes.values() if n.kind == "start"]
        if starts:
            return sorted(starts)
        return sorted(n.id for n in self.nodes.values() if self.in_degree(n.id) == 0)

    def end_nodes(self) -> list[str]:
        ends = [n.id for n in self.nodes.values() if n.kind == "end"]
        if ends:
            return sorted(ends)
        return sorted(n.id for n in self.nodes.values() if self.out_degree(n.id) == 0)

    def terminal_nodes(self) -> list[str]:
        """Nodes that cannot continue: explicit ends plus sinks."""
        return sorted(
            {n.id for n in self.nodes.values() if n.kind == "end"}
            | {n.id for n in self.nodes.values() if self.out_degree(n.id) == 0}
        )

    def submodel(self, node_ids: Iterable[str], name: str | None = None) -> "ProcessModel":
        """Induced subgraph used for fragment-level behavioural checks."""
        keep = set(node_ids)
        sub = ProcessModel(
            id=f"{self.id}::fragment",
            name=name or f"{self.name} (fragment)",
            source=self.source,
            fmt=self.fmt,
            pool=self.pool,
        )
        for nid in keep:
            if nid in self.nodes:
                sub.nodes[nid] = self.nodes[nid]
        for e in self.edges:
            if e.source in keep and e.target in keep:
                sub.add_edge(e)
        sub.lanes = [lane for lane in self.lanes if any(n.lane == lane for n in sub.nodes.values())]
        for mf in self.message_flows:
            if mf.source in keep or mf.target in keep:
                sub.add_message_flow(mf)
        for de in self.data_elements.values():
            overlap = [nid for nid in de.connected_nodes if nid in keep]
            if overlap:
                sub.add_data_element(
                    DataElement(
                        id=de.id,
                        name=de.name,
                        kind=de.kind,
                        connected_nodes=overlap,
                    )
                )
        return sub

    def stats(self) -> dict:
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "tasks": sum(1 for n in self.nodes.values() if n.kind in TASK_KINDS),
            "gateways": sum(1 for n in self.nodes.values() if n.is_gateway),
            "events": sum(1 for n in self.nodes.values() if n.is_event),
            "lanes": len(self.lanes),
            "message_flows": len(self.message_flows),
            "data_elements": len(self.data_elements),
        }

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "source": self.source,
            "format": self.fmt,
            "pool": self.pool,
            "lanes": self.lanes,
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
            "message_flows": [mf.to_dict() for mf in self.message_flows],
            "data_elements": [de.to_dict() for de in self.data_elements.values()],
            "stats": self.stats(),
        }
