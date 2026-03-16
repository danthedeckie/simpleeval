import unittest

from simpleeval import (
    simple_eval,
)


class TestMethodChaining(unittest.TestCase):
    def test_chaining_correct(self):
        """
        Contributed by Khalid Grandi (xaled).
        """

        class A(object):
            def __init__(self):
                self.a = "0"

            def add(self, b):
                self.a += "-add" + str(b)
                return self

            def sub(self, b):
                self.a += "-sub" + str(b)
                return self

            def tostring(self):
                return str(self.a)

        x = A()
        self.assertEqual(
            simple_eval("x.add(1).sub(2).sub(3).tostring()", names={"x": x}), "0-add1-sub2-sub3"
        )
