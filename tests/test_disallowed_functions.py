import os

import simpleeval
from simpleeval import (
    FeatureNotAvailable,
    SimpleEval,
    simple_eval,
)

from .base import DRYTest


class TestDisallowedFunctions(DRYTest):
    def test_functions_in_disallowed_functions_list(self):
        # a bit of double-entry testing. probably pointless.
        assert simpleeval.DISALLOW_FUNCTIONS.issuperset(
            {
                type,
                isinstance,
                eval,
                getattr,
                setattr,
                help,
                repr,
                compile,
                open,
                exec,
                os.popen,
                os.system,
            }
        )

    def test_functions_are_disallowed_at_init(self):
        for dangerous_function in simpleeval.DISALLOW_FUNCTIONS:
            with self.assertRaises(FeatureNotAvailable):
                SimpleEval(functions={"foo": dangerous_function})

    def test_functions_are_disallowed_in_expressions(self):
        for dangerous_function in simpleeval.DISALLOW_FUNCTIONS:
            with self.assertRaises(FeatureNotAvailable):
                s = SimpleEval()
                s.functions["foo"] = dangerous_function
                s.eval("foo(42)")

    def test_breakout_via_generator(self):
        # Thanks decorator-factory
        class Foo:
            def bar(self):
                yield "Hello, world!"

        # Test the generator does work - also adds the `yield` to codecov...
        assert list(Foo().bar()) == ["Hello, world!"]

        evil = "foo.bar().gi_frame.f_globals['__builtins__'].exec('raise RuntimeError(\"Oh no\")')"

        with self.assertRaises(FeatureNotAvailable):
            simple_eval(evil, names={"foo": Foo()})
