import warnings

import simpleeval
from simpleeval import (
    SimpleEval,
)

from .base import DRYTest


class TestEvaluator(DRYTest):
    """Tests for how the SimpleEval class does things"""

    def test_only_evaluate_first_statement(self):
        # it only evaluates the first statement:
        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter("always")
            self.t("11; x = 21; x + x", 11)
        self.assertIsInstance(ws[0].message, simpleeval.MultipleExpressions)

    def test_parse_and_use_previously_parsed(self):
        expr = "x + x"
        nodes = self.s.parse(expr)
        self.s.names = {"x": 21}
        self.assertEqual(self.s.eval(expr, nodes), 42)

        # This can all be done with unittest.mock.patch in python3.3+ - when we drop
        # python2 - we can drop this nonsense.
        class MockedCalled(Exception):
            pass

        def go_boom(*args, **kwargs):
            raise MockedCalled("you should never see this.")

        self.s.parse = go_boom

        # Prove the mock is installed in self.s
        with self.assertRaises(MockedCalled):
            self.s.eval("10 + 10")

        # Prove it's not installed in the actual SimpleEval
        SimpleEval().eval("10 + 10")

        # Now running .eval with a previously parsed
        self.assertEqual(self.s.eval(expr, previously_parsed=nodes), 42)

        self.s.names = {"x": 100}
        self.assertEqual(self.s.eval(expr, nodes), 200)
