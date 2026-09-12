"""Tests verifying that _check_disallowed_items fires at the trust boundary
(name resolution) and not on every intermediate AST node.

Performance is checked by validating that the number of ``_check_disallowed_items`` calls equals the number
of distinct name lookups, not the total number of AST nodes evaluated.
"""

import unittest
from unittest.mock import patch

from simpleeval import SimpleEval


class TestCheckCalledAtBoundary(unittest.TestCase):
    """_check_disallowed_items should be called once per name lookup, not once
    per AST node."""

    def _count_checks(self, s, expr):
        count = 0
        original = s._check_disallowed_items.__func__

        def counting(self_inner, item):
            nonlocal count
            count += 1
            return original(self_inner, item)

        with patch.object(type(s), "_check_disallowed_items", counting):
            s.eval(expr)

        return count

    def test_simple_expression_calls_per_name(self):
        """A simple expression with two distinct names should cause exactly
        two checks (one per name lookup), regardless of how many AST nodes
        the expression contains."""
        s = SimpleEval(names={"a": 1, "b": 2})
        # 'a + b * (a - b)' has 4 Name nodes (a, b, a, b). The number of checks
        # should equal the number of Name node evaluations (4), NOT the total
        # number of AST nodes (7+).
        checks = self._count_checks(s, "a + b * (a - b)")
        # Each *occurrence* of a name in the expression triggers one lookup:
        self.assertEqual(checks, 4)  # Instead of 8

    def test_complex_expression_node_count_independence(self):
        """Wrap a simple lookup in deeply nested arithmetic - the check count
        must not grow with nesting depth."""
        s = SimpleEval(names={"x": 5})

        shallow_checks = self._count_checks(s, "x + 1")
        deep_checks = self._count_checks(s, "x + 1 + 1 + 1 + 1 + 1")

        # Both have exactly one Name node ('x'), so both should trigger
        # exactly one check:
        self.assertEqual(shallow_checks, 1)  # Instead of 4
        self.assertEqual(deep_checks, 1)  # Instead of 12
