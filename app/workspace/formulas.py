"""Safe spreadsheet-style formula evaluator; never executes Python code."""

from __future__ import annotations

import ast
import operator
from typing import Any


_BINARY = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
}
_COMPARE = {
    ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt,
    ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge,
}
_FUNCTIONS = {
    "SUM": lambda *v: sum(_flatten(v)),
    "AVERAGE": lambda *v: (sum(_flatten(v)) / len(_flatten(v))) if _flatten(v) else None,
    "MIN": lambda *v: min(_flatten(v)) if _flatten(v) else None,
    "MAX": lambda *v: max(_flatten(v)) if _flatten(v) else None,
    "COUNT": lambda *v: len([x for x in _flatten(v) if isinstance(x, (int, float)) and not isinstance(x, bool)]),
    "ABS": abs,
    "ROUND": round,
    "IF": lambda condition, yes, no: yes if condition else no,
    "AND": lambda *v: all(v),
    "OR": lambda *v: any(v),
    "NOT": lambda v: not v,
}


def _flatten(values):
    for value in values:
        if isinstance(value, (list, tuple)):
            yield from _flatten(value)
        elif value is not None:
            yield value


class FormulaError(ValueError):
    pass


class FormulaEngine:
    """Evaluate a deliberately small, auditable formula language."""

    MAX_EXPRESSION_LENGTH = 2048
    MAX_POWER = 12

    def evaluate(self, expression: str, context: dict[str, Any] | None = None):
        if not isinstance(expression, str):
            raise TypeError("A fórmula deve ser texto.")
        source = expression.strip()
        if source.startswith("="):
            source = source[1:].strip()
        if not source or len(source) > self.MAX_EXPRESSION_LENGTH:
            raise FormulaError("Fórmula vazia ou acima do limite permitido.")
        try:
            tree = ast.parse(source, mode="eval")
            return self._node(tree.body, context or {})
        except FormulaError:
            raise
        except Exception as exc:
            raise FormulaError(f"Não foi possível avaliar a fórmula: {exc}") from exc

    def _node(self, node, context):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, str, bool, type(None))):
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in context:
                raise FormulaError(f"Referência desconhecida: {node.id}")
            return context[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
            left, right = self._node(node.left, context), self._node(node.right, context)
            if isinstance(node.op, ast.Pow) and abs(right) > self.MAX_POWER:
                raise FormulaError("Expoente acima do limite permitido.")
            return _BINARY[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub, ast.Not)):
            value = self._node(node.operand, context)
            return {ast.UAdd: operator.pos, ast.USub: operator.neg, ast.Not: operator.not_}[type(node.op)](value)
        if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
            values = [self._node(item, context) for item in node.values]
            return all(values) if isinstance(node.op, ast.And) else any(values)
        if isinstance(node, ast.Compare):
            left = self._node(node.left, context)
            for op, comparator in zip(node.ops, node.comparators):
                if type(op) not in _COMPARE:
                    raise FormulaError("Comparador não permitido.")
                right = self._node(comparator, context)
                if not _COMPARE[type(op)](left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.IfExp):
            return self._node(node.body if self._node(node.test, context) else node.orelse, context)
        if isinstance(node, (ast.List, ast.Tuple)):
            values = [self._node(item, context) for item in node.elts]
            return values if isinstance(node, ast.List) else tuple(values)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
            name = node.func.id.upper()
            if name not in _FUNCTIONS:
                raise FormulaError(f"Função não permitida: {name}")
            args = [self._node(item, context) for item in node.args]
            return _FUNCTIONS[name](*args)
        raise FormulaError(f"Operação não permitida: {type(node).__name__}")
