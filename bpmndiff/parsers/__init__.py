"""Multi-format process parsers (XPDL 2.x and BPMN 2.0).

Only the standard library is used.  The parsers intentionally ignore layout
information and return a :class:`~bpmndiff.model.ProcessModel`.
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from typing import Iterable

from ..model import DataElement, Edge, MessageFlow, Node, ProcessModel


class ParseError(ValueError):
    """Raised when a file is not a supported process model."""


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------
def local_name(tag: str) -> str:
    """Return the local part of an XML tag (namespace independent)."""
    return tag.rsplit("}", 1)[-1]


def children(element: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in list(element) if local_name(c.tag) == name]


def descendants(element: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in element.iter() if local_name(c.tag) == name]


def first_child(element: ET.Element, name: str) -> ET.Element | None:
    for child in list(element):
        if local_name(child.tag) == name:
            return child
    return None


def text_of(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return (element.text or "").strip()


def _bpmn_bounds(element: ET.Element) -> tuple[float, float, float, float] | None:
    bounds = first_child(element, "Bounds")
    if bounds is None:
        return None
    try:
        return (
            float(bounds.attrib["x"]),
            float(bounds.attrib["y"]),
            float(bounds.attrib["width"]),
            float(bounds.attrib["height"]),
        )
    except (KeyError, ValueError):
        return None


def _graphics_box(element: ET.Element) -> tuple[float, float, float, float] | None:
    """Extract (x, y, width, height) from a BizAgi-style graphic block."""
    node_infos = first_child(element, "NodeGraphicsInfos")
    if node_infos is None:
        return None
    for info in children(node_infos, "NodeGraphicsInfo"):
        coords = first_child(info, "Coordinates")
        if coords is None:
            continue
        try:
            x = float(coords.attrib.get("XCoordinate", 0))
            y = float(coords.attrib.get("YCoordinate", 0))
            w = float(info.attrib.get("Width", 0))
            h = float(info.attrib.get("Height", 0))
        except ValueError:
            continue
        return x, y, w, h
    return None


def _assign_lanes_by_geometry(
    model: ProcessModel, lane_boxes: list[tuple[str, float, float]], node_boxes: dict[str, tuple[float, float]]
) -> None:
    """Best-effort lane assignment for XPDL files without flowNodeRef."""
    for node_id, (_, cy) in node_boxes.items():
        for lane_name, y0, height in lane_boxes:
            if y0 <= cy <= y0 + height:
                node = model.nodes.get(node_id)
                if node is not None and not node.lane:
                    node.lane = lane_name
                    if lane_name not in model.lanes:
                        model.lanes.append(lane_name)
                break


# ---------------------------------------------------------------------------
# XPDL 2.x
# ---------------------------------------------------------------------------
_GATEWAY_TYPES = {
    "parallel": "and",
    "and": "and",
    "exclusive": "xor",
    "xor": "xor",
    "inclusive": "or",
    "or": "or",
    "complex": "complex",
    "eventbased": "event_based",
}


def _xpdl_gateway_kind(activity: ET.Element) -> str:
    explicit = activity.attrib.get("GatewayType", "")
    if not explicit:
        child = first_child(activity, "GatewayType")
        explicit = text_of(child)
    mapped = _GATEWAY_TYPES.get(explicit.replace(" ", "").lower())
    return mapped or "xor"


def _xpdl_event_definition(event: ET.Element) -> tuple[str, str, str | None, bool]:
    """Return (kind, event_def, attached_to, cancel_activity)."""
    start_el = first_child(event, "StartEvent")
    end_el = first_child(event, "EndEvent")
    inter_el = first_child(event, "IntermediateEvent")
    el = event
    for candidate in (start_el, end_el, inter_el):
        if candidate is not None:
            el = candidate
            break
    tag = local_name(el.tag) if el is not None else ""

    trigger = el.attrib.get("Trigger", "") or el.attrib.get("Result", "")
    if not trigger and el is not None:
        for c in list(el):
            c_tag = local_name(c.tag)
            if "Timer" in c_tag:
                trigger = "Timer"
            elif "Message" in c_tag:
                trigger = "Message"
            elif "Error" in c_tag:
                trigger = "Error"
            elif "Signal" in c_tag:
                trigger = "Signal"
            elif "Conditional" in c_tag:
                trigger = "Conditional"
            elif "Terminate" in c_tag:
                trigger = "Terminate"
            elif "Cancel" in c_tag or "Compensation" in c_tag:
                trigger = "Compensation"

    trigger_lower = trigger.lower()
    event_def = "none"
    if "timer" in trigger_lower:
        event_def = "timer"
    elif "message" in trigger_lower:
        event_def = "message"
    elif "error" in trigger_lower:
        event_def = "error"
    elif "signal" in trigger_lower:
        event_def = "signal"
    elif "conditional" in trigger_lower or "rule" in trigger_lower:
        event_def = "conditional"
    elif "terminate" in trigger_lower:
        event_def = "terminate"
    elif "compensation" in trigger_lower:
        event_def = "compensation"
    elif "escalation" in trigger_lower:
        event_def = "escalation"
    elif "link" in trigger_lower:
        event_def = "link"

    attached_to = el.attrib.get("Target") if el is not None else None
    if not attached_to and inter_el is not None:
        attached_to = inter_el.attrib.get("Target")
    cancel_activity = True
    if inter_el is not None:
        cancel_activity = inter_el.attrib.get("IsInterrupting", "true").lower() != "false"

    if start_el is not None:
        kind = "start"
    elif end_el is not None:
        kind = "end"
    elif attached_to:
        kind = "boundary_event"
    else:
        kind = "event"

    return kind, event_def, attached_to, cancel_activity


def _xpdl_marker(activity: ET.Element) -> str:
    loop = first_child(activity, "Loop")
    if loop is None:
        return "none"
    loop_type = loop.attrib.get("LoopType", "")
    if loop_type == "Standard":
        return "loop"
    if loop_type == "MultiInstance":
        mi = first_child(loop, "MultiInstance")
        ordering = (mi.attrib.get("MI_Ordering", "") if mi is not None else "").lower()
        if ordering == "sequential":
            return "multi_instance_sequential"
        return "multi_instance_parallel"
    return "none"


def _xpdl_task_type(activity: ET.Element) -> str:
    impl = first_child(activity, "Implementation")
    if impl is None:
        return "abstract"
    task = first_child(impl, "Task")
    if task is None:
        if first_child(impl, "SubFlow") is not None:
            return "subprocess"
        return "abstract"
    for c in list(task):
        tag = local_name(c.tag).lower()
        if "user" in tag:
            return "user"
        if "service" in tag:
            return "service"
        if "script" in tag:
            return "script"
        if "send" in tag:
            return "send"
        if "receive" in tag:
            return "receive"
        if "manual" in tag:
            return "manual"
        if "businessrule" in tag:
            return "business_rule"
    return "abstract"


def _xpdl_node(activity: ET.Element) -> Node:
    node_id = activity.attrib.get("Id", "")
    name = activity.attrib.get("Name", "")
    event = first_child(activity, "Event")
    if event is not None:
        kind, event_def, attached_to, cancel_activity = _xpdl_event_definition(event)
        return Node(
            id=node_id,
            name=name,
            kind=kind,
            event_definition=event_def,
            attached_to=attached_to,
            cancel_activity=cancel_activity,
        )
    if first_child(activity, "Route") is not None:
        route = first_child(activity, "Route")
        gateway_direction = "unspecified"
        if route is not None:
            d = route.attrib.get("GatewayDirection", "").lower()
            if d == "split":
                gateway_direction = "split"
            elif d == "join":
                gateway_direction = "join"
        return Node(
            id=node_id,
            name=name,
            kind=_xpdl_gateway_kind(activity),
            gateway_direction=gateway_direction,
        )

    impl = first_child(activity, "Implementation")
    subflow = first_child(impl, "SubFlow") if impl is not None else None
    if subflow is not None:
        return Node(
            id=node_id,
            name=name,
            kind="subprocess",
            called_element=subflow.attrib.get("Id", ""),
            marker=_xpdl_marker(activity),
        )

    task_type = _xpdl_task_type(activity)
    return Node(
        id=node_id,
        name=name,
        kind="task",
        task_type=task_type,
        marker=_xpdl_marker(activity),
    )


def _choose_process(processes: list[ET.Element], requested: str | None) -> ET.Element:
    if not processes:
        raise ParseError("XPDL package contains no WorkflowProcess")

    def score(proc: ET.Element) -> int:
        activities = first_child(proc, "Activities")
        return len(list(activities)) if activities is not None else 0

    if requested:
        for proc in processes:
            if requested in (proc.attrib.get("Id"), proc.attrib.get("Name")):
                return proc
        raise ParseError(f"process {requested!r} not found in XPDL package")
    return max(processes, key=score)


def parse_xpdl(path: str, process: str | None = None) -> ProcessModel:
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        raise ParseError(f"invalid XML in {path}: {exc}") from exc
    root = tree.getroot()

    processes = descendants(root, "WorkflowProcess")
    proc = _choose_process(processes, process)
    proc_id = proc.attrib.get("Id", "")
    proc_name = proc.attrib.get("Name", os.path.basename(path))
    model = ProcessModel(id=proc_id, name=proc_name, source=path, fmt="xpdl")

    # Pool name (the visible pool, not the "Main Process" container).
    pool_name = ""
    for pool in descendants(root, "Pool"):
        if pool.attrib.get("Process") == proc_id:
            pool_name = pool.attrib.get("Name", "")
            break
    model.pool = pool_name

    lane_boxes: list[tuple[str, float, float]] = []
    for pool in descendants(root, "Pool"):
        if pool.attrib.get("Process") != proc_id:
            continue
        for lane in descendants(pool, "Lane"):
            lane_name = lane.attrib.get("Name", "")
            if lane_name and lane_name not in model.lanes:
                model.lanes.append(lane_name)
            box = _graphics_box(lane)
            if box is not None:
                lane_boxes.append((lane_name, box[1], box[3]))

    node_boxes: dict[str, tuple[float, float]] = {}
    activities = first_child(proc, "Activities")
    if activities is not None:
        for activity in children(activities, "Activity"):
            node = _xpdl_node(activity)
            if not node.id:
                continue
            node.pool = pool_name
            model.add_node(node)
            box = _graphics_box(activity)
            if box is not None:
                node_boxes[node.id] = (box[0], box[1] + box[3] / 2.0)

    if lane_boxes:
        _assign_lanes_by_geometry(model, lane_boxes, node_boxes)

    # Data Stores & Objects in XPDL
    for ds in descendants(root, "DataStore"):
        ds_id = ds.attrib.get("Id", "")
        if ds_id:
            model.add_data_element(
                DataElement(id=ds_id, name=ds.attrib.get("Name", ""), kind="data_store")
            )
    for do in descendants(root, "DataObject"):
        do_id = do.attrib.get("Id", "")
        if do_id and do_id not in model.data_elements:
            model.add_data_element(
                DataElement(id=do_id, name=do.attrib.get("Name", ""), kind="data_object")
            )

    # Associations
    for assoc in descendants(root, "Association"):
        src = assoc.attrib.get("Source", "")
        tgt = assoc.attrib.get("Target", "")
        for item_id, node_id in [(src, tgt), (tgt, src)]:
            if item_id in model.data_elements and node_id in model.nodes:
                if node_id not in model.data_elements[item_id].connected_nodes:
                    model.data_elements[item_id].connected_nodes.append(node_id)

    # Message flows in XPDL
    for mf in descendants(root, "MessageFlow"):
        mf_id = mf.attrib.get("Id", "")
        src = mf.attrib.get("Source", "")
        tgt = mf.attrib.get("Target", "")
        name = mf.attrib.get("Name", "")
        if mf_id and src and tgt:
            model.add_message_flow(MessageFlow(id=mf_id, source=src, target=tgt, name=name))

    transitions = first_child(proc, "Transitions")
    if transitions is not None:
        for index, transition in enumerate(children(transitions, "Transition")):
            source = transition.attrib.get("From", "")
            target = transition.attrib.get("To", "")
            if source not in model.nodes or target not in model.nodes:
                continue
            condition_el = first_child(transition, "Condition")
            condition = ""
            is_default = False
            if condition_el is not None:
                cond_type = condition_el.attrib.get("Type", "").upper()
                if cond_type == "DEFAULTEXCEPTION":
                    is_default = True
                expression = first_child(condition_el, "Expression")
                condition = text_of(expression) or text_of(condition_el)
            model.add_edge(
                Edge(
                    id=transition.attrib.get("Id", f"flow-{index}"),
                    source=source,
                    target=target,
                    name=transition.attrib.get("Name", ""),
                    condition=condition,
                    is_default=is_default,
                )
            )

    if not model.nodes:
        raise ParseError(f"no activities found in process {proc_name!r}")
    return model


# ---------------------------------------------------------------------------
# BPMN 2.0
# ---------------------------------------------------------------------------
_BPMN_TASK_TYPES = {
    "task": "abstract",
    "userTask": "user",
    "serviceTask": "service",
    "scriptTask": "script",
    "sendTask": "send",
    "receiveTask": "receive",
    "manualTask": "manual",
    "businessRuleTask": "business_rule",
}

_BPMN_NODE_KINDS = {
    "startEvent": "start",
    "endEvent": "end",
    "intermediateCatchEvent": "event",
    "intermediateThrowEvent": "event",
    "boundaryEvent": "boundary_event",
    "task": "task",
    "userTask": "task",
    "serviceTask": "task",
    "scriptTask": "task",
    "sendTask": "task",
    "receiveTask": "task",
    "manualTask": "task",
    "businessRuleTask": "task",
    "callActivity": "call_activity",
    "subProcess": "subprocess",
    "adHocSubProcess": "subprocess",
    "transaction": "subprocess",
    "exclusiveGateway": "xor",
    "parallelGateway": "and",
    "inclusiveGateway": "or",
    "eventBasedGateway": "event_based",
    "complexGateway": "complex",
}


def _bpmn_event_definition(element: ET.Element) -> str:
    definitions = [
        ("messageEventDefinition", "message"),
        ("timerEventDefinition", "timer"),
        ("errorEventDefinition", "error"),
        ("signalEventDefinition", "signal"),
        ("conditionalEventDefinition", "conditional"),
        ("escalationEventDefinition", "escalation"),
        ("compensateEventDefinition", "compensation"),
        ("linkEventDefinition", "link"),
        ("terminateEventDefinition", "terminate"),
    ]
    for tag_name, def_type in definitions:
        if first_child(element, tag_name) is not None:
            return def_type
    return "none"


def _bpmn_marker(element: ET.Element) -> str:
    if first_child(element, "standardLoopCharacteristics") is not None:
        return "loop"
    mi = first_child(element, "multiInstanceLoopCharacteristics")
    if mi is not None:
        if mi.attrib.get("isSequential", "false").lower() == "true":
            return "multi_instance_sequential"
        return "multi_instance_parallel"
    return "none"


def _bpmn_gateway_direction(element: ET.Element) -> str:
    d = element.attrib.get("gatewayDirection", "").strip().lower()
    if d in {"diverging", "split"}:
        return "split"
    if d in {"converging", "join"}:
        return "join"
    return "unspecified"


def parse_bpmn(path: str, process: str | None = None) -> ProcessModel:
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        raise ParseError(f"invalid XML in {path}: {exc}") from exc
    root = tree.getroot()
    processes = descendants(root, "process")

    def score(proc: ET.Element) -> int:
        return sum(1 for child in list(proc) if local_name(child.tag) in _BPMN_NODE_KINDS)

    if not processes:
        raise ParseError("BPMN file contains no <process>")
    if process:
        selected = [
            p for p in processes if process in (p.attrib.get("id"), p.attrib.get("name"))
        ]
        if not selected:
            raise ParseError(f"process {process!r} not found in BPMN file")
        proc = selected[0]
    else:
        proc = max(processes, key=score)

    proc_id = proc.attrib.get("id", "")
    proc_name = proc.attrib.get("name", os.path.basename(path))
    model = ProcessModel(id=proc_id, name=proc_name, source=path, fmt="bpmn")

    # Pool name from collaboration/participant.
    pool_name = ""
    for participant in descendants(root, "participant"):
        if participant.attrib.get("processRef") == proc_id:
            pool_name = participant.attrib.get("name", "")
            break
    model.pool = pool_name

    # Lane membership.
    lane_of: dict[str, str] = {}
    lane_names_by_id: dict[str, str] = {}
    for lane in descendants(proc, "lane"):
        lane_name = lane.attrib.get("name", "")
        if lane_name and lane_name not in model.lanes:
            model.lanes.append(lane_name)
        lane_id = lane.attrib.get("id", "")
        if lane_id:
            lane_names_by_id[lane_id] = lane_name
        for ref in children(lane, "flowNodeRef"):
            if text_of(ref):
                lane_of[text_of(ref)] = lane_name

    def _parse_flow_nodes(container: ET.Element) -> None:
        for child in list(container):
            tag = local_name(child.tag)
            kind = _BPMN_NODE_KINDS.get(tag)
            if not kind:
                continue
            node_id = child.attrib.get("id", "")
            if not node_id:
                continue

            task_type = _BPMN_TASK_TYPES.get(tag, "abstract")
            event_def = _bpmn_event_definition(child)
            marker = _bpmn_marker(child)
            gateway_dir = _bpmn_gateway_direction(child)
            default_flow = child.attrib.get("default", "")
            attached_to = child.attrib.get("attachedToRef", None)
            cancel_act = child.attrib.get("cancelActivity", "true").lower() != "false"
            called_elem = child.attrib.get("calledElement", "")

            # If it's a subprocess, collect inner node IDs and recursively parse them
            submodel_ids: list[str] = []
            if kind == "subprocess":
                submodel_ids = [
                    c.attrib.get("id", "")
                    for c in list(child)
                    if local_name(c.tag) in _BPMN_NODE_KINDS and c.attrib.get("id")
                ]
                _parse_flow_nodes(child)

            node = Node(
                id=node_id,
                name=child.attrib.get("name", ""),
                kind=kind,
                lane=lane_of.get(node_id, ""),
                pool=pool_name,
                task_type=task_type,
                event_definition=event_def,
                attached_to=attached_to,
                cancel_activity=cancel_act,
                marker=marker,
                gateway_direction=gateway_dir,
                default_flow=default_flow,
                submodel_node_ids=submodel_ids,
                called_element=called_elem,
            )
            model.add_node(node)

    _parse_flow_nodes(proc)

    # Some BPMN exporters omit flowNodeRef; recover lane assignment from DI shapes
    lane_shapes: dict[str, tuple[tuple[float, float, float, float], bool]] = {}
    node_shapes: dict[str, tuple[float, float, float, float]] = {}
    for shape in descendants(root, "BPMNShape"):
        element_id = shape.attrib.get("bpmnElement", "")
        bounds = _bpmn_bounds(shape)
        if bounds is None:
            continue
        if element_id in lane_names_by_id:
            horizontal = shape.attrib.get("isHorizontal", "true").lower() != "false"
            lane_shapes[element_id] = (bounds, horizontal)
        elif element_id in model.nodes:
            node_shapes[element_id] = bounds

    for node_id, (x, y, width, height) in node_shapes.items():
        node = model.nodes[node_id]
        if node.lane:
            continue
        center_x = x + width / 2
        center_y = y + height / 2
        containing_lanes = []
        for lane_id, (lane_bounds, horizontal) in lane_shapes.items():
            lane_x, lane_y, lane_width, lane_height = lane_bounds
            in_lane = (
                lane_y <= center_y <= lane_y + lane_height
                if horizontal
                else lane_x <= center_x <= lane_x + lane_width
            )
            if in_lane:
                span = lane_height if horizontal else lane_width
                containing_lanes.append((span, lane_names_by_id[lane_id]))
        if containing_lanes:
            node.lane = min(containing_lanes)[1]

    # Data Elements in BPMN (dataObject, dataStore, dataStoreReference, dataInput, dataOutput)
    for item in descendants(root, "dataObject") + descendants(root, "dataObjectReference"):
        item_id = item.attrib.get("id", "")
        if item_id and item_id not in model.data_elements:
            model.add_data_element(
                DataElement(id=item_id, name=item.attrib.get("name", ""), kind="data_object")
            )
    for item in descendants(root, "dataStore") + descendants(root, "dataStoreReference"):
        item_id = item.attrib.get("id", "")
        if item_id and item_id not in model.data_elements:
            model.add_data_element(
                DataElement(id=item_id, name=item.attrib.get("name", ""), kind="data_store")
            )
    for item in descendants(proc, "dataInput") + descendants(proc, "dataOutput"):
        item_id = item.attrib.get("id", "")
        if item_id and item_id not in model.data_elements:
            kind = "data_input" if local_name(item.tag) == "dataInput" else "data_output"
            model.add_data_element(
                DataElement(id=item_id, name=item.attrib.get("name", ""), kind=kind)
            )

    # Data associations (dataInputAssociation, dataOutputAssociation)
    for flow_node in list(proc):
        node_id = flow_node.attrib.get("id", "")
        if node_id not in model.nodes:
            continue
        for assoc in children(flow_node, "dataInputAssociation") + children(flow_node, "dataOutputAssociation"):
            src_refs = [text_of(sr) for sr in children(assoc, "sourceRef")]
            tgt_ref = text_of(first_child(assoc, "targetRef"))
            for ref in src_refs + ([tgt_ref] if tgt_ref else []):
                if ref in model.data_elements:
                    if node_id not in model.data_elements[ref].connected_nodes:
                        model.data_elements[ref].connected_nodes.append(node_id)

    # Message flows across pools
    for mf in descendants(root, "messageFlow"):
        mf_id = mf.attrib.get("id", "")
        src = mf.attrib.get("sourceRef", "")
        tgt = mf.attrib.get("targetRef", "")
        name = mf.attrib.get("name", "")
        if mf_id and src and tgt:
            model.add_message_flow(MessageFlow(id=mf_id, source=src, target=tgt, name=name))

    # Sequence flows
    for index, flow in enumerate(descendants(proc, "sequenceFlow")):
        source = flow.attrib.get("sourceRef", "")
        target = flow.attrib.get("targetRef", "")
        if source not in model.nodes or target not in model.nodes:
            continue
        condition = ""
        condition_el = first_child(flow, "conditionExpression")
        if condition_el is not None:
            condition = text_of(condition_el)

        flow_id = flow.attrib.get("id", f"flow-{index}")
        source_node = model.nodes.get(source)
        is_default = False
        if source_node and source_node.default_flow == flow_id:
            is_default = True

        model.add_edge(
            Edge(
                id=flow_id,
                source=source,
                target=target,
                name=flow.attrib.get("name", ""),
                condition=condition,
                is_default=is_default,
            )
        )

    if not model.nodes:
        raise ParseError(f"no flow nodes found in process {proc_name!r}")
    return model


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def load_model(path: str, process: str | None = None) -> ProcessModel:
    """Load a `.xpdl`, `.bpmn` or `.xml` process file.

    The format is detected from the XML root element, not from the extension,
    because many datasets ship BPMN content in `.xml` files.
    """
    if not os.path.isfile(path):
        raise ParseError(f"file not found: {path}")
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise ParseError(f"not a well-formed XML file: {path}: {exc}") from exc
    root_tag = local_name(root.tag)
    if root_tag == "Package":
        return parse_xpdl(path, process)
    if root_tag == "definitions":
        return parse_bpmn(path, process)
    raise ParseError(
        f"unsupported root element <{root_tag}> in {path}; expected an XPDL "
        "<Package> or a BPMN <definitions> document"
    )


def load_models(paths: Iterable[str], process: str | None = None) -> list[ProcessModel]:
    return [load_model(p, process) for p in paths]
