"""Versioned change output and runtime comparison invariants."""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

from .alignment import Alignment, Pair
from .model import ProcessModel


class ComparisonInvariantError(ValueError):
    """Raised when an alignment or change record violates its contract."""


_MIRROR_FIELDS = {
    "op": "type",
    "legacy_op": "legacy_type",
    "category": "category",
    "category_name": "category_name",
    "element": "element",
    "before": "before",
    "after": "after",
    "detail": "detail",
    "label": "label",
    "subtype": "subtype",
    "is_synonym": "is_synonym",
    "score": "score",
    "confidence": "confidence",
    "needs_review": "needs_review",
}

_NODE_PAIR_OPERATIONS = {
    "RENAME_NODE",
    "NODE_TYPE_CHANGE",
    "MARKER_CHANGE",
    "BOUNDARY_CHANGE",
    "GATEWAY_TYPE_CHANGE",
    "MOVE_LANE",
}


@lru_cache(maxsize=1)
def _load_schema() -> dict[str, Any]:
    candidates = [
        Path(__file__).resolve().parent.parent / "schema" / "change-v1.json",
        Path(sys.prefix) / "share" / "bpmndiff" / "schema" / "change-v1.json",
    ]
    for path in candidates:
        if path.is_file():
            with path.open(encoding="utf-8") as stream:
                return json.load(stream)
    raise FileNotFoundError("schema/change-v1.json is required to validate diff output")


def _resolve_ref(reference: str, root: dict[str, Any]) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise ValueError(f"unsupported JSON Schema reference: {reference}")
    value: Any = root
    for part in reference[2:].split("/"):
        value = value[part.replace("~1", "/").replace("~0", "~")]
    return value


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ValueError(f"unsupported JSON Schema type: {expected}")


def _validate_schema(
    value: Any, schema: dict[str, Any], root: dict[str, Any], path: str
) -> None:
    if "$ref" in schema:
        _validate_schema(value, _resolve_ref(schema["$ref"], root), root, path)
        return

    expected_type = schema.get("type")
    if expected_type is not None:
        choices = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(_matches_type(value, choice) for choice in choices):
            raise ComparisonInvariantError(
                f"{path}: expected {' or '.join(choices)}, got {type(value).__name__}"
            )
    if "const" in schema and value != schema["const"]:
        raise ComparisonInvariantError(f"{path}: expected {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise ComparisonInvariantError(f"{path}: unsupported value {value!r}")

    if "anyOf" in schema:
        errors: list[str] = []
        for option in schema["anyOf"]:
            try:
                _validate_schema(value, option, root, path)
                break
            except ComparisonInvariantError as exc:
                errors.append(str(exc))
        else:
            raise ComparisonInvariantError(f"{path}: does not match any allowed schema")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ComparisonInvariantError(f"{path}: value is below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            raise ComparisonInvariantError(f"{path}: value is above maximum")

    if isinstance(value, dict):
        missing = set(schema.get("required", ())) - value.keys()
        if missing:
            raise ComparisonInvariantError(f"{path}: missing required fields {sorted(missing)}")
        for key, child_schema in schema.get("properties", {}).items():
            if key in value:
                _validate_schema(value[key], child_schema, root, f"{path}.{key}")

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise ComparisonInvariantError(f"{path}: too few items")
        if "items" in schema:
            for index, item in enumerate(value):
                _validate_schema(item, schema["items"], root, f"{path}[{index}]")


def validate_change_record(record: dict[str, Any]) -> None:
    """Validate one change/evidence envelope against the checked-in JSON Schema."""
    schema = _load_schema()
    _validate_schema(record, schema, schema, "change_record")


def _payload_node_ids(
    payload: Any, model: ProcessModel, operation: dict[str, Any]
) -> list[str]:
    if not isinstance(payload, dict):
        return []
    if operation.get("element") not in {
        "node",
        "gateway",
        "boundary_event",
        "swimlane",
        "flow",
        "subprocess",
        "message_flow",
    }:
        return []

    found: list[str] = []
    for key in ("id", "first_id", "second_id", "source_id", "target_id", "subprocess_id"):
        value = payload.get(key)
        if value in model.nodes and value not in found:
            found.append(value)
    for value in payload.get("node_ids", payload.get("task_ids", [])):
        if value in model.nodes and value not in found:
            found.append(value)

    name_keys = ("first", "second")
    for key in name_keys:
        name = payload.get(key)
        if not isinstance(name, str):
            continue
        matches = [node.id for node in model.nodes.values() if node.display_name == name]
        if len(matches) == 1 and matches[0] not in found:
            found.append(matches[0])

    if operation.get("element") == "message_flow":
        for key in ("source", "target"):
            value = payload.get(key)
            if isinstance(value, str) and value in model.nodes and value not in found:
                found.append(value)
    return found


def _pair_evidence(pair: Pair) -> dict[str, Any]:
    return {
        "reference_node_id": pair.a,
        "variant_node_id": pair.b,
        "label": pair.label,
        "score": round(pair.score, 3),
        "reason": pair.reason,
        "confidence": pair.confidence,
        "needs_review": pair.needs_review,
    }


def _node_context(model: ProcessModel, node_id: str | None) -> dict[str, Any] | None:
    if node_id is None or node_id not in model.nodes:
        return None
    return {
        "node_id": node_id,
        "predecessor_ids": model.predecessors(node_id),
        "successor_ids": model.successors(node_id),
        "in_degree": model.in_degree(node_id),
        "out_degree": model.out_degree(node_id),
    }


def _structural_evidence(
    reference: ProcessModel,
    variant: ProcessModel,
    alignment: Alignment,
    pair: Pair,
) -> dict[str, Any]:
    neighbors: list[dict[str, str]] = []
    if pair.a in reference.nodes and pair.b in variant.nodes:
        for direction, related_a, related_b in (
            ("predecessor", reference.predecessors(pair.a), variant.predecessors(pair.b)),
            ("successor", reference.successors(pair.a), variant.successors(pair.b)),
        ):
            for node_id in related_a:
                mapped_id = alignment.a_to_b.get(node_id)
                if mapped_id is not None and mapped_id in related_b:
                    neighbors.append(
                        {
                            "direction": direction,
                            "reference_node_id": node_id,
                            "variant_node_id": mapped_id,
                        }
                    )
    return {
        "reference": _node_context(reference, pair.a),
        "variant": _node_context(variant, pair.b),
        "matched_neighbors": neighbors,
    }


def _related_pairs(
    reference: ProcessModel,
    variant: ProcessModel,
    alignment: Alignment,
    operation: dict[str, Any],
) -> list[Pair]:
    reference_ids = _payload_node_ids(operation.get("before"), reference, operation)
    variant_ids = _payload_node_ids(operation.get("after"), variant, operation)
    pairs: list[Pair] = []
    for node_id in reference_ids:
        pair = alignment.pair_of_a.get(node_id)
        if pair is not None and pair not in pairs:
            pairs.append(pair)
    for node_id in variant_ids:
        pair = alignment.pair_of_b.get(node_id)
        if pair is not None and pair not in pairs:
            pairs.append(pair)

    if operation.get("op") == "RENAME_LANE":
        before_lane = (operation.get("before") or {}).get("name")
        after_lane = (operation.get("after") or {}).get("name")
        for pair in alignment.matched_pairs:
            if (
                reference.nodes[pair.a].lane == before_lane
                and variant.nodes[pair.b].lane == after_lane
                and pair not in pairs
            ):
                pairs.append(pair)
    return pairs


def _evidence_for_operation(
    reference: ProcessModel,
    variant: ProcessModel,
    alignment: Alignment,
    operation: dict[str, Any],
) -> dict[str, Any]:
    pairs = _related_pairs(reference, variant, alignment, operation)
    structural = [
        _structural_evidence(reference, variant, alignment, pair)
        for pair in pairs
    ]
    observations = [
        {"source": "alignment", "description": pair.reason or f"Alignment label: {pair.label}."}
        for pair in pairs
    ]
    if structural:
        observations.append(
            {
                "source": "graph",
                "description": "Direct predecessor and successor context for aligned nodes.",
            }
        )

    op_type = operation["op"]
    if operation.get("element") == "data":
        source = "data"
    elif operation.get("element") == "swimlane":
        source = "lane"
    elif operation.get("element") == "flow" or op_type in {
        "REORDER",
        "PARALLELIZE",
        "SEQUENTIALIZE",
    }:
        source = "graph"
    elif op_type in {"RENAME_NODE", "NODE_TYPE_CHANGE", "MARKER_CHANGE", "BOUNDARY_CHANGE"}:
        source = "attribute"
    else:
        source = "operation"
    observations.append(
        {
            "source": source,
            "description": operation.get("detail") or f"{op_type} detected.",
            "value": {
                "before": operation.get("before"),
                "after": operation.get("after"),
            },
        }
    )
    return {
        "alignment": [_pair_evidence(pair) for pair in pairs],
        "structural_context": structural,
        "observations": observations,
    }


def _change_layer(operation: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "category",
        "category_name",
        "element",
        "before",
        "after",
        "detail",
        "label",
        "subtype",
        "is_synonym",
        "score",
        "confidence",
        "needs_review",
    )
    change = {
        "type": operation["op"],
        "legacy_type": operation.get("legacy_op", operation["op"]),
    }
    change.update({key: operation[key] for key in keys if key in operation})
    return change


def standardize_operations(
    reference: ProcessModel,
    variant: ProcessModel,
    alignment: Alignment,
    operations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Add the v1 change/evidence layers while retaining legacy flat fields."""
    standardized = []
    for operation in operations:
        record = dict(operation)
        record.update(
            {
                "schema_version": "change-v1",
                "change": _change_layer(operation),
                "evidence": _evidence_for_operation(
                    reference, variant, alignment, operation
                ),
            }
        )
        standardized.append(record)
    return standardized


def assert_diff_invariants(
    reference: ProcessModel,
    variant: ProcessModel,
    alignment: Alignment,
    operations: list[dict[str, Any]],
) -> None:
    """Fail loudly if the alignment or emitted changes violate the v1 contract."""
    seen_a = [pair.a for pair in alignment.pairs if pair.a is not None]
    seen_b = [pair.b for pair in alignment.pairs if pair.b is not None]
    if len(seen_a) != len(set(seen_a)) or set(seen_a) != set(reference.nodes):
        raise ComparisonInvariantError("alignment must cover each reference node exactly once")
    if len(seen_b) != len(set(seen_b)) or set(seen_b) != set(variant.nodes):
        raise ComparisonInvariantError("alignment must cover each variant node exactly once")

    expected_a_to_b = {
        pair.a: pair.b for pair in alignment.matched_pairs if pair.a and pair.b
    }
    expected_b_to_a = {value: key for key, value in expected_a_to_b.items()}
    if alignment.a_to_b != expected_a_to_b or alignment.b_to_a != expected_b_to_a:
        raise ComparisonInvariantError("alignment maps must be one-to-one and agree with matched pairs")
    if set(alignment.pair_of_a) != set(reference.nodes) or set(alignment.pair_of_b) != set(variant.nodes):
        raise ComparisonInvariantError("alignment pair indexes must cover both models")

    deleted: list[str] = []
    inserted: list[str] = []
    for index, operation in enumerate(operations):
        validate_change_record(operation)
        change = operation["change"]
        for legacy_key, change_key in _MIRROR_FIELDS.items():
            if legacy_key in operation and operation[legacy_key] != change.get(change_key):
                raise ComparisonInvariantError(
                    f"operations[{index}]: legacy field {legacy_key!r} disagrees with change layer"
                )

        if operation["op"] == "DELETE_NODE":
            before = operation.get("before") or {}
            deleted.append(before.get("id"))
            pair = alignment.pair_of_a.get(before.get("id"))
            if pair is None or pair.matched:
                raise ComparisonInvariantError("DELETE_NODE must refer to an unmatched reference node")
        elif operation["op"] == "INSERT_NODE":
            after = operation.get("after") or {}
            inserted.append(after.get("id"))
            pair = alignment.pair_of_b.get(after.get("id"))
            if pair is None or pair.matched:
                raise ComparisonInvariantError("INSERT_NODE must refer to an unmatched variant node")
        elif operation["op"] in _NODE_PAIR_OPERATIONS:
            before, after = operation.get("before") or {}, operation.get("after") or {}
            pair = alignment.pair_of_a.get(before.get("id"))
            if pair is None or not pair.matched or pair.b != after.get("id"):
                raise ComparisonInvariantError(
                    f"{operation['op']} must refer to its matched alignment pair"
                )

    expected_deleted = {pair.a for pair in alignment.unmatched_a}
    expected_inserted = {pair.b for pair in alignment.unmatched_b}
    if len(deleted) != len(set(deleted)) or set(deleted) != expected_deleted:
        raise ComparisonInvariantError("unmatched reference nodes must have exactly one DELETE_NODE")
    if len(inserted) != len(set(inserted)) or set(inserted) != expected_inserted:
        raise ComparisonInvariantError("unmatched variant nodes must have exactly one INSERT_NODE")
