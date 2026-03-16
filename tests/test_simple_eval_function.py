import unittest

from simpleeval import (
    simple_eval,
)


class TestSimpleEval(unittest.TestCase):
    """test the 'simple_eval' wrapper function"""

    def test_basic_run(self):
        self.assertEqual(simple_eval("6*7"), 42)

    def test_default_functions(self):
        self.assertEqual(simple_eval("rand() < 1.0 and rand() > -0.01"), True)
        self.assertEqual(simple_eval("randint(200) < 200 and rand() > 0"), True)
