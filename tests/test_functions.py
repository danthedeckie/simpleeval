import os

import simpleeval
from simpleeval import (
    simple_eval,
)

from .base import DRYTest


class TestFunctions(DRYTest):
    """Functions for expressions to play with"""

    def test_load_file(self):
        """add in a function which loads data from an external file."""

        # write to the file:

        with open("testfile.txt", "w") as f:
            f.write("42")

        # define the function we'll send to the eval'er

        def load_file(filename):
            """load a file and return its contents"""
            with open(filename) as f2:
                return f2.read()

        # simple load:

        self.s.functions = {"read": load_file}
        self.t("read('testfile.txt')", "42")

        # and we should have *replaced* the default functions. Let's check:

        with self.assertRaises(simpleeval.FunctionNotDefined):
            self.t("int(read('testfile.txt'))", 42)

        # OK, so we can load in the default functions as well...

        self.s.functions.update(simpleeval.DEFAULT_FUNCTIONS)

        # now it works:

        self.t("int(read('testfile.txt'))", 42)

        os.remove("testfile.txt")

    def test_randoms(self):
        """test the rand() and randint() functions"""

        i = self.s.eval("randint(1000)")
        self.assertEqual(type(i), int)
        self.assertLessEqual(i, 1000)

        f = self.s.eval("rand()")
        self.assertEqual(type(f), float)

        self.t("randint(20)<20", True)
        self.t("rand()<1.0", True)

        # I don't know how to further test these functions.  Ideas?

    def test_methods(self):
        self.t('"WORD".lower()', "word")
        x = simpleeval.DISALLOW_METHODS
        simpleeval.DISALLOW_METHODS = []
        self.t('"{}:{}".format(1, 2)', "1:2")
        simpleeval.DISALLOW_METHODS = x

    def test_function_args_none(self):
        def foo():
            return 42

        self.s.functions["foo"] = foo
        self.t("foo()", 42)

    def test_function_args_required(self):
        def foo(to_return):
            return to_return

        self.s.functions["foo"] = foo
        with self.assertRaises(TypeError):
            self.t("foo()", 42)

        self.t("foo(12)", 12)
        self.t("foo(to_return=100)", 100)

    def test_function_args_defaults(self):
        def foo(to_return=9999):
            return to_return

        self.s.functions["foo"] = foo
        self.t("foo()", 9999)

        self.t("foo(12)", 12)
        self.t("foo(to_return=100)", 100)

    def test_function_args_bothtypes(self):
        def foo(mult, to_return=100):
            return to_return * mult

        self.s.functions["foo"] = foo
        with self.assertRaises(TypeError):
            self.t("foo()", 9999)

        self.t("foo(2)", 200)

        with self.assertRaises(TypeError):
            self.t("foo(to_return=100)", 100)

        self.t("foo(4, to_return=4)", 16)
        self.t("foo(mult=2, to_return=4)", 8)
        self.t("foo(2, 10)", 20)

    def test_function_with_list_args(self):
        # Regression test, makes sure we can pass lists (non-hashable) items as
        # kwargs to functions.

        def func(*args, **kwargs):
            return 42

        simple_eval("test(boo=x)", functions={"test": func}, names={"x": [1, 2]})
