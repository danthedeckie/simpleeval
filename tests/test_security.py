import os
import sys

import simpleeval
from simpleeval import (
    FeatureNotAvailable,
    SimpleEval,
)

from .base import DRYTest


class TestTryingToBreakOut(DRYTest):
    """Test various weird methods to break the security sandbox..."""

    def test_import(self):
        """usual suspect. import"""
        # cannot import things:
        with self.assertRaises(FeatureNotAvailable):
            self.t("import sys", None)

    def test_long_running(self):
        """exponent operations can take a long time."""
        old_max = simpleeval.MAX_POWER

        self.t("9**9**5", 9**9**5)

        with self.assertRaises(simpleeval.NumberTooHigh):
            self.t("9**9**8", 0)

        # and does limiting work?

        simpleeval.MAX_POWER = 100

        with self.assertRaises(simpleeval.NumberTooHigh):
            self.t("101**2", 0)

        # good, so set it back:

        simpleeval.MAX_POWER = old_max

    def test_large_shifts(self):
        """Trying to << or >> large amounts can be too slow."""
        with self.assertRaises(simpleeval.NumberTooHigh):
            self.t("1<<25000", 0)

        with self.assertRaises(simpleeval.NumberTooHigh):
            self.t("%s<<25" % (simpleeval.MAX_SHIFT_BASE + 1), 0)

        with self.assertRaises(simpleeval.NumberTooHigh):
            self.t("1>>25000", 0)

        with self.assertRaises(simpleeval.NumberTooHigh):
            self.t("%s>>25" % (simpleeval.MAX_SHIFT_BASE + 1), 0)

        # and test we can change it:

        old_max = simpleeval.MAX_SHIFT
        simpleeval.MAX_SHIFT = 100

        with self.assertRaises(simpleeval.NumberTooHigh):
            self.t("1<<250", 0)

        with self.assertRaises(simpleeval.NumberTooHigh):
            self.t("1000>>250", 0)

        # good, so set it back.

        simpleeval.MAX_SHIFT = old_max

        self.t("1<<250", 1 << 250)

    def test_encode_bignums(self):
        # thanks gk
        with self.assertRaises(simpleeval.IterableTooLong):
            self.t('(1).from_bytes(("123123123123123123123123").encode()*999999, "big")', 0)

    def test_string_length(self):
        with self.assertRaises(simpleeval.IterableTooLong):
            self.t("50000*'text'", 0)

        with self.assertRaises(simpleeval.IterableTooLong):
            self.t("'text'*50000", 0)

        with self.assertRaises(simpleeval.IterableTooLong):
            self.t("('text'*50000)*1000", 0)

        with self.assertRaises(simpleeval.IterableTooLong):
            self.t("(50000*'text')*1000", 0)

        self.t("'stuff'*20000", 20000 * "stuff")

        self.t("20000*'stuff'", 20000 * "stuff")

        with self.assertRaises(simpleeval.IterableTooLong):
            self.t("('stuff'*20000) + ('stuff'*20000) ", 0)

        with self.assertRaises(simpleeval.IterableTooLong):
            self.t("'stuff'*100000", 100000 * "stuff")

        with self.assertRaises(simpleeval.IterableTooLong):
            self.t("'" + (10000 * "stuff") + "'*100", 0)

        with self.assertRaises(simpleeval.IterableTooLong):
            self.t("'" + (50000 * "stuff") + "'", 0)

        if sys.version_info >= (3, 6, 0):
            with self.assertRaises(simpleeval.IterableTooLong):
                self.t("f'{\"foo\"*50000}'", 0)

    def test_bytes_array_test(self):
        self.t("'20000000000000000000'.encode() * 5000", "20000000000000000000".encode() * 5000)

        with self.assertRaises(simpleeval.IterableTooLong):
            self.t("'123121323123131231223'.encode() * 5000", 20)

    def test_list_length_test(self):
        self.t("'spam spam spam'.split() * 5000", ["spam", "spam", "spam"] * 5000)

        with self.assertRaises(simpleeval.IterableTooLong):
            self.t("('spam spam spam' * 5000).split() * 5000", None)

    def test_function_globals_breakout(self):
        """by accessing function.__globals__ or func_..."""
        # thanks perkinslr.

        self.s.functions["x"] = lambda y: y + y
        self.t("x(100)", 200)

        with self.assertRaises(simpleeval.FeatureNotAvailable):
            self.t("x.__globals__", None)

        class EscapeArtist(object):
            @staticmethod
            def trapdoor():
                return 42

            @staticmethod
            def _quasi_private():
                return 84

        self.s.names["houdini"] = EscapeArtist()

        with self.assertRaises(simpleeval.FeatureNotAvailable):
            self.t("houdini.trapdoor.__globals__", 0)

        with self.assertRaises(simpleeval.FeatureNotAvailable):
            self.t("houdini.trapdoor.func_globals", 0)

        with self.assertRaises(simpleeval.FeatureNotAvailable):
            self.t("houdini._quasi_private()", 0)

        # and test for changing '_' to '__':

        dis = simpleeval.DISALLOW_PREFIXES
        simpleeval.DISALLOW_PREFIXES = ["func_"]

        self.t("houdini.trapdoor()", 42)
        self.t("houdini._quasi_private()", 84)

        # and return things to normal

        simpleeval.DISALLOW_PREFIXES = dis

    def test_mro_breakout(self):
        class Blah(object):
            x = 42

        self.s.names["b"] = Blah

        with self.assertRaises(simpleeval.FeatureNotAvailable):
            self.t("b.mro()", None)

    def test_builtins_private_access(self):
        # explicit attempt of the exploit from perkinslr
        with self.assertRaises(simpleeval.FeatureNotAvailable):
            self.t(
                "True.__class__.__class__.__base__.__subclasses__()[-1]"
                ".__init__.func_globals['sys'].exit(1)",
                42,
            )

    def test_string_format(self):
        # python has so many ways to break out!
        with self.assertRaises(simpleeval.FeatureNotAvailable):
            self.t('"{string.__class__}".format(string="things")', 0)

        with self.assertRaises(simpleeval.FeatureNotAvailable):
            self.s.names["x"] = {"a": 1}
            self.t('"{a.__class__}".format_map(x)', 0)

        if sys.version_info >= (3, 6, 0):
            self.s.names["x"] = 42

            with self.assertRaises(simpleeval.FeatureNotAvailable):
                self.t('f"{x.__class__}"', 0)

            self.s.names["x"] = lambda y: y

            with self.assertRaises(simpleeval.FeatureNotAvailable):
                self.t('f"{x.__globals__}"', 0)

            class EscapeArtist(object):
                @staticmethod
                def trapdoor():
                    return 42

                @staticmethod
                def _quasi_private():
                    return 84

            self.s.names["houdini"] = EscapeArtist()  # let's just retest this, but in a f-string

            with self.assertRaises(simpleeval.FeatureNotAvailable):
                self.t('f"{houdini.trapdoor.__globals__}"', 0)

            with self.assertRaises(simpleeval.FeatureNotAvailable):
                self.t('f"{houdini.trapdoor.func_globals}"', 0)

            with self.assertRaises(simpleeval.FeatureNotAvailable):
                self.t('f"{houdini._quasi_private()}"', 0)

            # and test for changing '_' to '__':

            dis = simpleeval.DISALLOW_PREFIXES
            simpleeval.DISALLOW_PREFIXES = ["func_"]

            self.t('f"{houdini.trapdoor()}"', "42")
            self.t('f"{houdini._quasi_private()}"', "84")

            # and return things to normal

            simpleeval.DISALLOW_PREFIXES = dis

    def test_breakout_via_module_access(self):
        import os.path

        s = SimpleEval(names={"path": os.path})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("path.os.popen('id').read()")

    def test_breakout_via_module_access_attr(self):
        import os.path

        class Foo:
            p = os.path

        s = SimpleEval(names={"thing": Foo()})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("thing.p.os.popen('id').read()")

    def test_breakout_via_disallowed_functions_as_attrs(self):
        class Foo:
            p = exec

        s = SimpleEval(names={"thing": Foo()})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("thing.p('exit')")

    def test_breakout_forbidden_function_in_list(self):
        """Disallowed functions in lists should be blocked"""
        s = SimpleEval(names={"funcs": [exec, eval]})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("funcs[0]('exit')")

        with self.assertRaises(FeatureNotAvailable):
            s.eval("funcs[1]('1+1')")

    def test_breakout_module_in_list(self):
        """Modules in lists should be blocked"""
        import os.path

        s = SimpleEval(names={"things": [os.path, os.system]})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("things[0].os.popen('id').read()")

    def test_breakout_forbidden_function_in_dict_value(self):
        """Disallowed functions as dict values should be blocked"""
        s = SimpleEval(names={"funcs": {"bad": exec, "evil": eval}})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("funcs['bad']('exit')")

        with self.assertRaises(FeatureNotAvailable):
            s.eval("funcs['evil']('1+1')")

    def test_breakout_module_in_dict_value(self):
        """Modules as dict values should be blocked"""
        import os.path

        s = SimpleEval(names={"things": {"p": os.path, "s": os.system}})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("things['p'].os.popen('id').read()")

    def test_breakout_function_returning_forbidden_function(self):
        """Functions returning disallowed functions should be blocked"""

        def get_evil():
            return exec  # pragma: no cover

        s = SimpleEval(names={}, functions={"get_evil": get_evil})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("get_evil()('exit')")

    def test_breakout_function_returning_module(self):
        """Functions returning modules should be blocked"""
        import os.path

        def get_module():
            return os.path

        s = SimpleEval(names={}, functions={"get_module": get_module})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("get_module().os.popen('id').read()")

    def test_dunder_all_in_module(self):
        """__all__ should be blocked (starts with _)"""

        s = SimpleEval(names={"os": os})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("os.__all__")

    def test_dunder_dict_in_module(self):
        """__dict__ should be blocked (starts with _)"""

        s = SimpleEval(names={"os": os})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("os.__dict__")

    def test_forbidden_method_in_tuple(self):
        """Disallowed functions in tuples should be blocked"""
        s = SimpleEval(names={"funcs": (exec, eval)})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("funcs[0]('exit')")

    def test_module_in_tuple(self):
        """Modules in tuples should be blocked"""

        s = SimpleEval(names={"mods": (os.path, os.system)})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("mods[0].os.popen('id').read()")

    def test_breakout_via_nested_container_forbidden_func(self):
        """Disallowed functions nested in containers should be blocked"""
        s = SimpleEval(names={"data": {"nested": {"funcs": [exec]}}})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("data['nested']['funcs'][0]('exit')")

    def test_breakout_via_nested_container_module(self):
        """Modules nested in containers should be blocked"""

        s = SimpleEval(names={"data": {"mods": {"p": os.path}}})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("data['mods']['p'].os.popen('id').read()")

    def test_forbidden_methods_on_allowed_attrs(self):
        """Disallowed methods listed in DISALLOW_METHODS should be
        blocked"""
        s = SimpleEval()

        # format and format_map are in DISALLOW_METHODS
        with self.assertRaises(FeatureNotAvailable):
            s.eval("'test {0}'.format")

        with self.assertRaises(FeatureNotAvailable):
            s.eval("'test'.format_map({0: 'x'})")

        # __mro__ is in DISALLOW_METHODS
        with self.assertRaises(FeatureNotAvailable):
            s.eval("'test'.mro")

    def test_function_returning_forbidden_method(self):
        """Functions returning disallowed methods should be blocked"""

        def get_exec_module():
            return os  # pragma: no cover

        s = SimpleEval(names={}, functions={"get_os": get_exec_module})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("get_os().__name__")

    def test_compound_module_submodule_access(self):
        """Accessing submodules of a passed module should be blocked"""
        import os.path

        s = SimpleEval(names={"path": os.path})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("path.os")

    def test_forbidden_func_via_class_method(self):
        """Accessing forbidden functions via class methods should be
        blocked"""

        class Container:
            @staticmethod
            def get_exec():
                return exec  # pragma: no cover

        s = SimpleEval(names={"c": Container()})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("c.get_exec()('exit')")

    def test_module_via_class_method(self):
        """Accessing modules via class methods should be blocked"""

        class Container:
            @staticmethod
            def get_os():
                return os

        s = SimpleEval(names={"c": Container()})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("c.get_os().popen('id').read()")

    def test_forbidden_func_via_property(self):
        """Accessing forbidden functions via properties should be
        blocked"""

        class Container:
            @property
            def evil(self):
                return exec

        s = SimpleEval(names={"c": Container()})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("c.evil('exit')")

    def test_module_via_property(self):
        """Accessing modules via properties should be blocked"""

        class Container:
            @property
            def mod(self):
                return os

        s = SimpleEval(names={"c": Container()})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("c.mod.popen('id').read()")

    def test_forbidden_function_direct_from_names(self):
        """Forbidden functions passed directly in names should
        be blocked when accessed"""
        s = SimpleEval(names={"evil": exec})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("evil")

    def test_module_direct_from_names(self):
        """Modules passed directly in names should be blocked
        when accessed"""

        s = SimpleEval(names={"m": os})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("m")

    def test_forbidden_function_via_callable_name_handler(self):
        """Forbidden functions from callable name handlers should
        be blocked"""

        def name_handler(node):
            if node.id == "evil":
                return exec

        s = SimpleEval(names=name_handler)

        with self.assertRaises(FeatureNotAvailable):
            s.eval("evil")

    def test_module_via_callable_name_handler(self):
        """Modules from callable name handlers should be blocked"""

        def name_handler(node):
            if node.id == "m":
                return os

        s = SimpleEval(names=name_handler)

        with self.assertRaises(FeatureNotAvailable):
            s.eval("m")

    def test_forbidden_function_passed_to_custom_function(self):
        """Passing forbidden functions to custom functions should be
        blocked - they can be executed by the custom function"""

        def evil_caller(func):
            return func("print('pwned')")  # pragma: no cover

        s = SimpleEval(names={"evil": exec}, functions={"evil_caller": evil_caller})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("evil_caller(evil)")

    def test_module_passed_to_custom_function(self):
        """Passing modules to custom functions should be blocked - they
        can be used by the custom function"""

        def os_caller(mod):
            return mod.system("id")  # pragma: no cover

        s = SimpleEval(names={"m": os}, functions={"os_caller": os_caller})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("os_caller(m)")  # pragma: no cover

    def test_forbidden_function_in_list_passed_to_custom_function(self):
        """Forbidden functions in containers passed to custom functions
        should be blocked"""

        def extract_and_call(items):
            return items[0]("print('pwned')")  # pragma: no cover

        s = SimpleEval(names={"funcs": [exec, eval]}, functions={"extract": extract_and_call})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("extract(funcs)")

    def test_module_in_list_passed_to_custom_function(self):
        """Modules in containers passed to custom functions should be
        blocked"""

        def extract_and_use(items):
            return items[0].system("id")  # pragma: no cover

        s = SimpleEval(names={"mods": [os.path, os]}, functions={"extract": extract_and_use})

        with self.assertRaises(FeatureNotAvailable):
            s.eval("extract(mods)")

    def test_forbidden_function_in_dict_passed_to_custom_function(self):
        """Forbidden functions in dicts passed to custom functions should
        be blocked"""

        def extract_and_call(d):
            return d["bad"]("print('pwned')")  # pragma: no cover

        s = SimpleEval(
            names={"funcs": {"bad": exec, "good": print}}, functions={"extract": extract_and_call}
        )

        with self.assertRaises(FeatureNotAvailable):
            s.eval("extract(funcs)")

    def test_module_in_dict_passed_to_custom_function(self):
        """Modules in dicts passed to custom functions should be blocked"""

        def extract_and_use(d):
            return d["m"].system("id")  # pragma: no cover

        s = SimpleEval(
            names={"mods": {"m": os, "p": os.path}}, functions={"extract": extract_and_use}
        )

        with self.assertRaises(FeatureNotAvailable):
            s.eval("extract(mods)")
