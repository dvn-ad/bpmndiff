"""Unit tests for the extended BPMN scope and 5-category change taxonomy."""

from __future__ import annotations

import unittest

from bpmndiff.diff import DiffOptions, diff_models
from bpmndiff.model import DataElement, Edge, MessageFlow, Node, ProcessModel


def _build_simple_process(model_id: str, tasks: list[tuple[str, str, str]]) -> ProcessModel:
    """Helper to build a sequence: start -> task1 -> task2 ... -> end.
    
    Each task is (id, name, lane).
    """
    model = ProcessModel(id=model_id, name=model_id, source=f"{model_id}.bpmn", fmt="bpmn")
    start = Node(f"{model_id}-start", "Start", "start")
    model.add_node(start)
    prev = start.id

    for tid, name, lane in tasks:
        node = Node(tid, name, "task", lane=lane)
        model.add_node(node)
        model.add_edge(Edge(f"e-{prev}-{tid}", prev, tid))
        prev = tid

    end = Node(f"{model_id}-end", "End", "end")
    model.add_node(end)
    model.add_edge(Edge(f"e-{prev}-{end.id}", prev, end.id))
    return model


class ModelScopeTests(unittest.TestCase):
    def test_node_extended_attributes(self):
        node = Node(
            id="t1",
            name="Verify identity",
            kind="task",
            task_type="user",
            marker="multi_instance_parallel",
            lane="Security",
            pool="Hospital",
        )
        self.assertEqual(node.task_type, "user")
        self.assertEqual(node.marker, "multi_instance_parallel")
        self.assertEqual(node.family, "task")

        d = node.to_dict()
        self.assertEqual(d["task_type"], "user")
        self.assertEqual(d["marker"], "multi_instance_parallel")

    def test_boundary_event_attributes(self):
        boundary = Node(
            id="ev1",
            name="Timeout",
            kind="boundary_event",
            event_definition="timer",
            attached_to="t1",
            cancel_activity=False,
        )
        self.assertTrue(boundary.is_boundary)
        self.assertEqual(boundary.event_definition, "timer")
        self.assertEqual(boundary.attached_to, "t1")
        self.assertFalse(boundary.cancel_activity)

    def test_message_flow_and_data_element(self):
        model = ProcessModel(id="p1", name="Patient Intake")
        model.add_node(Node(id="t1", name="Register", kind="task"))

        mf = MessageFlow(id="mf1", source="t1", target="external_sys", name="Patient Record")
        model.add_message_flow(mf)
        self.assertEqual(len(model.message_flows), 1)

        de = DataElement(id="ds1", name="PatientDB", kind="data_store", connected_nodes=["t1"])
        model.add_data_element(de)
        self.assertEqual(len(model.data_elements), 1)

        model_dict = model.to_dict()
        self.assertIn("message_flows", model_dict)
        self.assertIn("data_elements", model_dict)


class TaxonomyDetectionTests(unittest.TestCase):
    def test_category1_insert_and_delete_node(self):
        # A has tasks t1, t2; B has t1, t3
        m1 = _build_simple_process("m1", [("t1", "Check in", "FO"), ("t2", "Take Photo", "FO")])
        m2 = _build_simple_process("m2", [("t1", "Check in", "FO"), ("t3", "Verify Insurance", "FO")])
        comp = diff_models(m1, m2, DiffOptions(bisimulation=False))
        ops = comp.operations
        self.assertTrue(any(op["op"] == "DELETE_NODE" for op in ops))
        self.assertTrue(any(op["op"] == "INSERT_NODE" for op in ops))

    def test_category1_rename_node_synonym_vs_meaning(self):
        # Synonym: "Save form" -> "Store form"
        m1 = _build_simple_process("m1", [("t1", "Save form", "FO")])
        m2 = _build_simple_process("m2", [("t1", "Store form", "FO")])
        comp1 = diff_models(m1, m2, DiffOptions(bisimulation=False))
        rename_syn = [op for op in comp1.operations if op["op"] == "RENAME_NODE"]
        self.assertEqual(len(rename_syn), 1)
        self.assertTrue(rename_syn[0].get("is_synonym"))

        # Meaning changed: "General patient" -> "Corporate patient"
        m3 = _build_simple_process("m3", [("t1", "General patient", "FO")])
        m4 = _build_simple_process("m4", [("t1", "Corporate patient", "FO")])
        comp2 = diff_models(m3, m4, DiffOptions(bisimulation=False))
        rename_mean = [op for op in comp2.operations if op["op"] == "RENAME_NODE"]
        self.assertEqual(len(rename_mean), 1)
        self.assertFalse(rename_mean[0].get("is_synonym"))

    def test_category1_node_type_change(self):
        # Task type: user -> service
        m1 = _build_simple_process("m1", [("t1", "Process claim", "FO")])
        m1.nodes["t1"].task_type = "user"
        m2 = _build_simple_process("m2", [("t1", "Process claim", "FO")])
        m2.nodes["t1"].task_type = "service"

        comp = diff_models(m1, m2, DiffOptions(bisimulation=False))
        type_changes = [op for op in comp.operations if op["op"] == "NODE_TYPE_CHANGE"]
        self.assertEqual(len(type_changes), 1)

    def test_category1_marker_change(self):
        # marker: none -> loop
        m1 = _build_simple_process("m1", [("t1", "Collect signatures", "FO")])
        m2 = _build_simple_process("m2", [("t1", "Collect signatures", "FO")])
        m2.nodes["t1"].marker = "loop"

        comp = diff_models(m1, m2, DiffOptions(bisimulation=False))
        marker_changes = [op for op in comp.operations if op["op"] == "MARKER_CHANGE"]
        self.assertEqual(len(marker_changes), 1)

    def test_category1_boundary_change(self):
        m1 = _build_simple_process("m1", [("t1", "Task 1", "FO"), ("t2", "Task 2", "FO")])
        b1 = Node("b1", "Timeout", "boundary_event", event_definition="timer", attached_to="t1", cancel_activity=True)
        m1.add_node(b1)

        m2 = _build_simple_process("m2", [("t1", "Task 1", "FO"), ("t2", "Task 2", "FO")])
        b2 = Node("b1", "Timeout", "boundary_event", event_definition="timer", attached_to="t2", cancel_activity=False)
        m2.add_node(b2)

        comp = diff_models(m1, m2, DiffOptions(bisimulation=False))
        b_changes = [op for op in comp.operations if op["op"] == "BOUNDARY_CHANGE"]
        self.assertEqual(len(b_changes), 1)

    def test_category2_actors_lanes(self):
        # MOVE_LANE & RENAME_LANE & INSERT_LANE & DELETE_LANE
        m1 = _build_simple_process("m1", [("t1", "Verify", "Reviewer"), ("t2", "Archive", "OldLane")])
        m2 = _build_simple_process("m2", [("t1", "Verify", "Senior Reviewer"), ("t2", "Archive", "NewLane")])
        m2.lanes.append("Auditor")  # newly added empty lane

        comp = diff_models(m1, m2, DiffOptions(bisimulation=False))
        ops = comp.operations
        # Both RENAME_LANE and MOVE_LANE are actor operations
        actor_ops = [op for op in ops if op.get("category") == 2 or op["op"] in {"RENAME_LANE", "MOVE_LANE", "INSERT_LANE", "DELETE_LANE"}]
        self.assertTrue(len(actor_ops) >= 1)

    def test_category3_reorder(self):
        # A -> B in m1 vs B -> A in m2
        m1 = _build_simple_process("m1", [("t1", "Step One", "FO"), ("t2", "Step Two", "FO")])
        m2 = _build_simple_process("m2", [("t2", "Step Two", "FO"), ("t1", "Step One", "FO")])

        comp = diff_models(m1, m2, DiffOptions(bisimulation=False))
        reorders = [op for op in comp.operations if op["op"] == "REORDER"]
        self.assertEqual(len(reorders), 1)

    def test_category3_gateway_and_flow_changes(self):
        # Gateway type XOR -> AND
        m1 = ProcessModel("m1", "m1")
        m1.add_node(Node("gw1", "Split", "xor"))
        m2 = ProcessModel("m2", "m2")
        m2.add_node(Node("gw1", "Split", "and"))

        comp = diff_models(m1, m2, DiffOptions(bisimulation=False))
        gw_changes = [op for op in comp.operations if op["op"] == "GATEWAY_TYPE_CHANGE"]
        self.assertEqual(len(gw_changes), 1)

    def test_category3_flow_condition_change(self):
        m1 = _build_simple_process("m1", [("t1", "Task 1", "FO"), ("t2", "Task 2", "FO")])
        m1.edges[1].condition = "amount > 100"
        m2 = _build_simple_process("m2", [("t1", "Task 1", "FO"), ("t2", "Task 2", "FO")])
        m2.edges[1].condition = "amount > 500"

        comp = diff_models(m1, m2, DiffOptions(bisimulation=False))
        cond_changes = [op for op in comp.operations if op["op"] == "FLOW_CONDITION_CHANGE"]
        self.assertEqual(len(cond_changes), 1)

    def test_category3_parallelize_and_sequentialize(self):
        # Sequential: start -> A -> B -> end
        m_seq = _build_simple_process("seq", [("ta", "Task A", "FO"), ("tb", "Task B", "FO")])

        # Parallel: start -> split_and -> branches A & B -> join_and -> end
        m_par = ProcessModel("par", "par")
        m_par.add_node(Node("s", "Start", "start"))
        m_par.add_node(Node("split", "", "and"))
        m_par.add_node(Node("ta", "Task A", "task", lane="FO"))
        m_par.add_node(Node("tb", "Task B", "task", lane="FO"))
        m_par.add_node(Node("join", "", "and"))
        m_par.add_node(Node("e", "End", "end"))

        m_par.add_edge(Edge("e1", "s", "split"))
        m_par.add_edge(Edge("e2", "split", "ta"))
        m_par.add_edge(Edge("e3", "split", "tb"))
        m_par.add_edge(Edge("e4", "ta", "join"))
        m_par.add_edge(Edge("e5", "tb", "join"))
        m_par.add_edge(Edge("e6", "join", "e"))

        comp_par = diff_models(m_seq, m_par, DiffOptions(bisimulation=False))
        par_ops = [op for op in comp_par.operations if op["op"] == "PARALLELIZE"]
        self.assertGreaterEqual(len(par_ops), 1)

        comp_seq = diff_models(m_par, m_seq, DiffOptions(bisimulation=False))
        seq_ops = [op for op in comp_seq.operations if op["op"] == "SEQUENTIALIZE"]
        self.assertGreaterEqual(len(seq_ops), 1)

    def test_category4_subprocess_extract_and_inline(self):
        m_root = _build_simple_process("root", [("t1", "Alpha", "FO"), ("t2", "Beta", "FO")])

        m_sub = ProcessModel("sub", "sub")
        m_sub.add_node(Node("s", "Start", "start"))
        m_sub.add_node(Node("sp", "Subprocess 1", "subprocess", submodel_node_ids=["t1", "t2"]))
        m_sub.add_node(Node("t1", "Alpha", "task", lane="FO"))
        m_sub.add_node(Node("t2", "Beta", "task", lane="FO"))
        m_sub.add_node(Node("e", "End", "end"))
        m_sub.add_edge(Edge("e1", "s", "sp"))
        m_sub.add_edge(Edge("e2", "sp", "e"))

        comp_ext = diff_models(m_root, m_sub, DiffOptions(bisimulation=False))
        self.assertTrue(any(op["op"] == "EXTRACT_SUBPROCESS" for op in comp_ext.operations))

        comp_inl = diff_models(m_sub, m_root, DiffOptions(bisimulation=False))
        self.assertTrue(any(op["op"] == "INLINE_SUBPROCESS" for op in comp_inl.operations))

    def test_category5_data_and_message_flow_change(self):
        m1 = _build_simple_process("m1", [("t1", "Task 1", "FO")])
        m2 = _build_simple_process("m2", [("t1", "Task 1", "FO")])

        # Message flow added in m2
        m2.add_message_flow(MessageFlow("mf1", "t1", "ext_pool", "Inquiry"))

        # Data store added in m2 connected to t1
        m2.add_data_element(DataElement("ds1", "PatientsDB", "data_store", connected_nodes=["t1"]))

        comp = diff_models(m1, m2, DiffOptions(bisimulation=False))
        ops = comp.operations
        self.assertTrue(any(op["op"] == "MESSAGE_FLOW_CHANGE" for op in ops))
        self.assertTrue(any(op["op"] == "DATA_CHANGE" for op in ops))


if __name__ == "__main__":
    unittest.main()
