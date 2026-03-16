from simpleeval import (
    FunctionNotDefined,
    NameNotDefined,
    OperatorNotDefined,
    SimpleEval,
)

from .base import DRYTest


class TestNoEntries(DRYTest):
    def test_no_functions(self):
        self.s.eval("int(42)")
        with self.assertRaises(FunctionNotDefined):
            s = SimpleEval(functions={})
            s.eval("int(42)")

    def test_no_names(self):
        s = SimpleEval(names={})
        with self.assertRaises(NameNotDefined):
            s.eval("hello")

    def test_no_operators(self):
        self.s.eval("1+2")
        self.s.eval("~2")
        s = SimpleEval(operators={})

        with self.assertRaises(OperatorNotDefined):
            s.eval("1+2")

        with self.assertRaises(OperatorNotDefined):
            s.eval("~ 2")
