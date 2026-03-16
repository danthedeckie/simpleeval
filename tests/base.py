import unittest

from simpleeval import (
    SimpleEval,
)


class DRYTest(unittest.TestCase):
    """Stuff we need to do every test, let's do here instead..
    Don't Repeat Yourself."""

    def setUp(self):
        """initialize a SimpleEval"""
        self.s = SimpleEval()

    def t(self, expr, should_be):  # pylint: disable=invalid-name
        """test an evaluation of an expression against an expected answer"""
        return self.assertEqual(self.s.eval(expr), should_be)
