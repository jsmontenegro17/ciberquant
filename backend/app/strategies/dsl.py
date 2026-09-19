"""Bounded, typed data-only AST. No user code is executed."""

import hashlib
import json
from decimal import Decimal
from enum import Enum
from ..features.registry import CANDLE_KEYS, feature_keys
from ..features import FEATURE_ENGINE_VERSION
from . import STRATEGY_DSL_VERSION

MAX_DEPTH, MAX_NODES, MAX_BARS_AGO = 4, 50, 50
OPS = ("GT", "GTE", "LT", "LTE", "EQ", "NE")
BASE_FIELDS = {k: "NUMBER" for k in ["open", "high", "low", "close", *CANDLE_KEYS, "gap_seconds", "contiguous_run_length"]}
BASE_FIELDS.update(direction="STRING", gap_before="BOOLEAN")


def number(value, places=18):
    if not isinstance(value, str) or len(value) > 80:
        raise ValueError("NUMBER must be a bounded decimal string")
    try:
        result = Decimal(value)
    except Exception as exc:
        raise ValueError("Invalid decimal string") from exc
    if not result.is_finite() or result.copy_abs() > Decimal("1e20") or result.as_tuple().exponent < -places:
        raise ValueError("Decimal outside precision/magnitude limits")
    return result


def decimal_string(value):
    result = format(value, "f")
    return (result.rstrip("0").rstrip(".") if "." in result else result) if value else "0"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def fields_for(specs):
    return {**BASE_FIELDS, **{key: "NUMBER" for s in specs for key in feature_keys(s)}}


def validate_tree(tree, specs):
    fields, count = fields_for(specs), 0

    def operand(raw, left=False):
        if not isinstance(raw, dict):
            raise ValueError("Operand must be an object")
        kind = raw.get("type")
        if kind == "FIELD":
            if set(raw) - {"type", "field", "bars_ago"}:
                raise ValueError("Unknown FIELD parameter")
            field, ago = raw.get("field"), raw.get("bars_ago", 0)
            if not isinstance(field, str) or field not in fields:
                raise ValueError("Unknown or undeclared feature field")
            if type(ago) is not int or not 0 <= ago <= MAX_BARS_AGO:
                raise ValueError("bars_ago must be integer0–50")
            return {"type": kind, "field": field, "bars_ago": ago}, fields[field]
        if left or set(raw) != {"type", "value"}:
            raise ValueError("Left operand must be FIELD; constants require type/value only")
        value = raw["value"]
        if kind == "NUMBER":
            value = decimal_string(number(value))
        elif kind == "STRING":
            if value not in ("C", "P", "D"):
                raise ValueError("Categorical value must be C/P/D")
        elif kind == "BOOLEAN":
            if type(value) is not bool:
                raise ValueError("BOOLEAN requires a boolean")
        else:
            raise ValueError("Unknown operand type")
        return {"type": kind, "value": value}, kind

    def visit(node, depth):
        nonlocal count
        count += 1
        if count > MAX_NODES or depth > MAX_DEPTH:
            raise ValueError("DSL depth/node limit exceeded")
        if not isinstance(node, dict):
            raise ValueError("Condition must be an object")
        op = node.get("operator")
        if op in ("AND", "OR"):
            children = node.get("conditions")
            if set(node) != {"operator", "conditions"} or not isinstance(children, list) or not 1 <= len(children) <= MAX_NODES:
                raise ValueError("Group requires1–50 conditions")
            return {"operator": op, "conditions": [visit(n, depth + 1) for n in children]}
        if op not in OPS or set(node) != {"left", "operator", "right"}:
            raise ValueError("Invalid condition operator/shape")
        left, lt = operand(node["left"], True)
        right, rt = operand(node["right"])
        if lt != rt or (op not in ("EQ", "NE") and lt != "NUMBER"):
            raise ValueError("Incompatible operand types/operator")
        return {"left": left, "operator": op, "right": right}

    return visit(tree, 1)


class Truth(str, Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"


def evaluate(tree, history, signal_time):
    context = {}

    def resolve(op):
        if op["type"] != "FIELD":
            return number(op["value"]) if op["type"] == "NUMBER" else op["value"]
        ago, field = op["bars_ago"], op["field"]
        value = None
        if ago < len(history):
            row = history[-1 - ago]
            if row["close_time"] <= signal_time:
                value = row.get(field, row["features"].get(field))
        context[f"{field}@{ago}"] = value
        return value

    def visit(node):
        op = node["operator"]
        if op in ("AND", "OR"):
            values = [visit(child) for child in node["conditions"]]
            if op == "AND":
                if Truth.FALSE in values:
                    return Truth.FALSE
                return Truth.UNKNOWN if Truth.UNKNOWN in values else Truth.TRUE
            if Truth.TRUE in values:
                return Truth.TRUE
            return Truth.UNKNOWN if Truth.UNKNOWN in values else Truth.FALSE
        a, b = resolve(node["left"]), resolve(node["right"])
        if a is None or b is None:
            return Truth.UNKNOWN
        result = {
            "GT": lambda: a > b,
            "GTE": lambda: a >= b,
            "LT": lambda: a < b,
            "LTE": lambda: a <= b,
            "EQ": lambda: a == b,
            "NE": lambda: a != b,
        }[op]()
        return Truth.TRUE if result else Truth.FALSE

    return visit(tree), context


def definitions():
    return dict(
        strategy_dsl_version=STRATEGY_DSL_VERSION,
        feature_engine_version=FEATURE_ENGINE_VERSION,
        operators=OPS,
        group_operators=["AND", "OR"],
        base_fields=BASE_FIELDS,
        max_bars_ago=MAX_BARS_AGO,
        max_depth=MAX_DEPTH,
        max_nodes=MAX_NODES,
        entry_model="NEXT_CANDLE_OPEN",
        statuses=["DRAFT", "TESTING", "DISABLED"],
    )
