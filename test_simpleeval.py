# pylint: disable=too-many-public-methods, missing-docstring, eval-used, too-many-lines, no-self-use, disallowed-name, unspecified-encoding

"""
Unit tests for simpleeval.
--------------------------

Most of this stuff is pretty basic.

"""

import ast
import gc
import operator
import os
import platform
import sys
import unittest
import warnings

import simpleeval
from simpleeval import (
    AttributeDoesNotExist,
    EvalWithCompoundTypes,
    FeatureNotAvailable,
    FunctionNotDefined,
    InvalidExpression,
    NameNotDefined,
    OperatorNotDefined,
    SimpleEval,
    simple_eval,
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


class TestBasic(DRYTest):
    """Simple expressions."""

    def test_maths_with_ints(self):
        """simple maths expressions"""

        self.t("21 + 21", 42)
        self.t("6*7", 42)
        self.t("20 + 1 + (10*2) + 1", 42)
        self.t("100/10", 10)
        self.t("12*12", 144)
        self.t("2 ** 10", 1024)
        self.t("100 % 9", 1)
        self.t("10 << 10", 10 << 10)
        self.t("10 << 10", 10240)
        self.t("1000 >> 2", 1000 >> 2)
        self.t("1000 >> 2", 250)

    def test_bools_and_or(self):
        self.t('True and ""', "")
        self.t("True and False", False)
        self.t("True or False", True)
        self.t("False or False", False)
        self.t("1 - 1 or 21", 21)
        self.t("1 - 1 and 11", 0)
        self.t("110 == 100 + 10 and True", True)
        self.t("110 != 100 + 10 and True", False)
        self.t("False or 42", 42)

        self.t("False or None", None)
        self.t("None or None", None)

        self.s.names = {"out": True, "position": 3}
        self.t(
            "(out and position <=6 and -10)"
            " or (out and position > 6 and -5)"
            " or (not out and 15)",
            -10,
        )

    def test_bit_ops(self):
        self.t("62 ^ 20", 42)
        self.t("62 ^ 100", 90)
        self.t("8 | 34", 42)
        self.t("100 & 63", 36)
        self.t("~ -43", 42)

    def test_not(self):
        self.t("not False", True)
        self.t("not True", False)
        self.t("not 0", True)
        self.t("not 1", False)

    def test_maths_with_floats(self):
        self.t("11.02 - 9.1", 1.92)
        self.t("29.1+39", 68.1)

    def test_comparisons(self):
        # GT & LT:
        self.t("1 > 0", True)
        self.t("100000 < 28", False)
        self.t("-2 < 11", True)
        self.t("+2 < 5", True)
        self.t("0 == 0", True)

        # GtE, LtE
        self.t("-2 <= -2", True)
        self.t("2 >= 2", True)
        self.t("1 >= 12", False)
        self.t("1.09 <= 1967392", True)

        self.t("1 < 2 < 3 < 4", 1 < 2 < 3 < 4)
        self.t("1 < 2 > 3 < 4", 1 < 2 > 3 < 4)

        # pylint: disable=comparison-with-itself
        self.t("1<2<1+1", 1 < 2 < 1 + 1)
        self.t("1 == 1 == 2", 1 == 1 == 2)
        self.t("1 == 1 < 2", 1 == 1 < 2)

    def test_mixed_comparisons(self):
        self.t("1 > 0.999999", True)
        self.t("1 == True", True)  # Note ==, not 'is'.
        self.t("0 == False", True)  # Note ==, not 'is'.
        self.t("False == False", True)
        self.t("False < True", True)

    def test_if_else(self):
        """x if y else z"""

        # and test if/else expressions:
        self.t("'a' if 1 == 1 else 'b'", "a")
        self.t("'a' if 1 > 2 else 'b'", "b")

        # and more complex expressions:
        self.t("'a' if 4 < 1 else 'b' if 1 == 2 else 'c'", "c")

    def test_default_conversions(self):
        """conversion between types"""

        self.t('int("20") + int(0.22*100)', 42)
        self.t('float("42")', 42.0)
        self.t('"Test Stuff!" + str(11)', "Test Stuff!11")

    def test_slicing(self):
        self.s.operators[ast.Slice] = (
            operator.getslice if hasattr(operator, "getslice") else operator.getitem
        )
        self.t("'hello'[1]", "e")
        self.t("'hello'[:]", "hello")
        self.t("'hello'[:3]", "hel")
        self.t("'hello'[3:]", "lo")
        self.t("'hello'[::2]", "hlo")
        self.t("'hello'[::-1]", "olleh")
        self.t("'hello'[3::]", "lo")
        self.t("'hello'[:3:]", "hel")
        self.t("'hello'[1:3]", "el")
        self.t("'hello'[1:3:]", "el")
        self.t("'hello'[1::2]", "el")
        self.t("'hello'[:1:2]", "h")
        self.t("'hello'[1:3:1]", "el")
        self.t("'hello'[1:3:2]", "e")

        with self.assertRaises(IndexError):
            self.t("'hello'[90]", 0)

        self.t('"spam" not in "my breakfast"', True)
        self.t('"silly" in "ministry of silly walks"', True)
        self.t('"I" not in "team"', True)
        self.t('"U" in "RUBBISH"', True)

    def test_is(self):
        self.t("1 is 1", True)
        self.t("1 is 2", False)
        self.t('1 is "a"', False)
        self.t("1 is None", False)
        self.t("None is None", True)

        self.t("1 is not 1", False)
        self.t("1 is not 2", True)
        self.t('1 is not "a"', True)
        self.t("1 is not None", True)
        self.t("None is not None", False)

    def test_fstring(self):
        if sys.version_info >= (3, 6, 0):
            self.t('f""', "")
            self.t('f"stuff"', "stuff")
            self.t('f"one is {1} and two is {2}"', "one is 1 and two is 2")
            self.t('f"1+1 is {1+1}"', "1+1 is 2")
            self.t("f\"{'dramatic':!<11}\"", "dramatic!!!")

    def test_set_not_allowed(self):
        with self.assertRaises(FeatureNotAvailable):
            self.t("{22}", False)

    def test_empty_string_not_allowed(self):
        with self.assertRaises(InvalidExpression):
            self.t("", False)


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


class TestOperators(DRYTest):
    """Test adding in new operators, removing them, make sure it works."""

    # TODO
    pass


class TestNewFeatures(DRYTest):
    """Tests which will break when new features are added..."""

    def test_lambda(self):
        with self.assertRaises(FeatureNotAvailable):
            self.t("lambda x:22", None)

    def test_lambda_application(self):
        with self.assertRaises(FeatureNotAvailable):
            self.t("(lambda x:22)(44)", None)


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


class TestCompoundTypes(DRYTest):
    """Test the compound-types edition of the library"""

    def setUp(self):
        self.s = EvalWithCompoundTypes()

    def test_dict(self):
        self.t("{}", {})
        self.t('{"foo": "bar"}', {"foo": "bar"})
        self.t('{"foo": "bar"}["foo"]', "bar")
        self.t("dict()", {})
        self.t("dict(a=1)", {"a": 1})

    def test_dict_contains(self):
        self.t('{"a":22}["a"]', 22)
        with self.assertRaises(KeyError):
            self.t('{"a":22}["b"]', 22)

        self.t('{"a": 24}.get("b", 11)', 11)
        self.t('"a" in {"a": 24}', True)

    def test_dict_star_expression(self):
        self.s.names["x"] = {"a": 1, "b": 2}
        self.t('{"a": 0, **x, "c": 3}', {"a": 1, "b": 2, "c": 3})

        # and multiple star expressions should be fine too...
        self.s.names["y"] = {"x": 1, "y": 2}
        self.t('{"a": 0, **x, **y, "c": 3}', {"a": 1, "b": 2, "c": 3, "x": 1, "y": 2})

    def test_dict_invalid_star_expression(self):
        self.s.names["x"] = {"a": 1, "b": 2}
        self.s.names["y"] = {"x": 1, "y": 2}
        self.s.names["z"] = 42

        with self.assertRaises(TypeError):
            self.t('{"a": 0, **x, **y, **z, "c": 3}', {"a": 1, "b": 2, "c": 3})

    def test_tuple(self):
        self.t("()", ())
        self.t("(1,)", (1,))
        self.t("(1, 2, 3, 4, 5, 6)", (1, 2, 3, 4, 5, 6))
        self.t("(1, 2) + (3, 4)", (1, 2, 3, 4))
        self.t("(1, 2, 3)[1]", 2)
        self.t("tuple()", ())
        self.t('tuple("foo")', ("f", "o", "o"))

    def test_tuple_contains(self):
        self.t('("a","b")[1]', "b")
        with self.assertRaises(IndexError):
            self.t('("a","b")[5]', "b")
        self.t('"a" in ("b","c","a")', True)

    def test_list(self):
        self.t("[]", [])
        self.t("[1]", [1])
        self.t("[1, 2, 3, 4, 5]", [1, 2, 3, 4, 5])
        self.t("[1, 2, 3][1]", 2)
        self.t("list()", [])
        self.t('list("foo")', ["f", "o", "o"])

    def test_list_contains(self):
        self.t('["a","b"][1]', "b")
        with self.assertRaises(IndexError):
            self.t('("a","b")[5]', "b")

        self.t('"b" in ["a","b"]', True)

    def test_list_star_expression(self):
        self.s.names["x"] = [1, 2, 3]
        self.t('["a", *x, "b"]', ["a", 1, 2, 3, "b"])

    def test_list_invalid_star_expression(self):
        self.s.names["x"] = [1, 2, 3]
        self.s.names["y"] = 42

        with self.assertRaises(TypeError):
            self.t('["a", *x, *y, "b"]', ["a", 1, 2, 3, "b"])

    def test_set(self):
        self.t("{1}", {1})
        self.t("{1, 2, 1, 2, 1, 2, 1}", {1, 2})
        self.t("set()", set())
        self.t('set("foo")', {"f", "o"})

        self.t("2 in {1,2,3,4}", True)
        self.t("22 not in {1,2,3,4}", True)

    def test_not(self):
        self.t("not []", True)
        self.t("not [0]", False)
        self.t("not {}", True)
        self.t("not {0: 1}", False)
        self.t("not {0}", False)

    def test_use_func(self):
        self.s = EvalWithCompoundTypes(functions={"map": map, "str": str})
        self.t("list(map(str, [-1, 0, 1]))", ["-1", "0", "1"])
        with self.assertRaises(NameNotDefined):
            self.s.eval("list(map(bad, [-1, 0, 1]))")

        with self.assertRaises(FunctionNotDefined):
            self.s.eval("dir(str)")
        with self.assertRaises(FeatureNotAvailable):
            self.s.eval("str.__dict__")

        self.s = EvalWithCompoundTypes(functions={"dir": dir, "str": str})
        self.t("dir(str)", dir(str))


class TestComprehensions(DRYTest):
    """Test the comprehensions support of the compound-types edition of the class."""

    def setUp(self):
        self.s = EvalWithCompoundTypes()

    def test_basic(self):
        self.t("[a + 1 for a in [1,2,3]]", [2, 3, 4])

    def test_with_self_reference(self):
        self.t("[a + a for a in [1,2,3]]", [2, 4, 6])

    def test_with_if(self):
        self.t("[a for a in [1,2,3,4,5] if a <= 3]", [1, 2, 3])

    def test_with_multiple_if(self):
        self.t("[a for a in [1,2,3,4,5] if a <= 3 and a > 1 ]", [2, 3])

    def test_attr_access_fails(self):
        with self.assertRaises(FeatureNotAvailable):
            self.t("[a.__class__ for a in [1,2,3]]", None)

    def test_unpack(self):
        self.t("[a+b for a,b in ((1,2),(3,4))]", [3, 7])

    def test_nested_unpack(self):
        self.t("[a+b+c for a, (b, c) in ((1,(1,1)),(3,(2,2)))]", [3, 7])

    def test_dictcomp_basic(self):
        self.t("{a:a + 1 for a in [1,2,3]}", {1: 2, 2: 3, 3: 4})

    def test_dictcomp_with_self_reference(self):
        self.t("{a:a + a for a in [1,2,3]}", {1: 2, 2: 4, 3: 6})

    def test_dictcomp_with_if(self):
        self.t("{a:a for a in [1,2,3,4,5] if a <= 3}", {1: 1, 2: 2, 3: 3})

    def test_dictcomp_with_multiple_if(self):
        self.t("{a:a for a in [1,2,3,4,5] if a <= 3 and a > 1 }", {2: 2, 3: 3})

    def test_dictcomp_unpack(self):
        self.t("{a:a+b for a,b in ((1,2),(3,4))}", {1: 3, 3: 7})

    def test_dictcomp_nested_unpack(self):
        self.t("{a:a+b+c for a, (b, c) in ((1,(1,1)),(3,(2,2)))}", {1: 3, 3: 7})

    def test_other_places(self):
        self.s.functions = {"sum": sum}
        self.t("sum([a+1 for a in [1,2,3,4,5]])", 20)
        self.t("sum(a+1 for a in [1,2,3,4,5])", 20)

    def test_external_names_work(self):
        self.s.names = {"x": [22, 102, 12.3]}
        self.t("[a/2 for a in x]", [11.0, 51.0, 6.15])

        self.s.names = lambda x: ord(x.id)
        self.t("[a + a for a in [b, c, d]]", [ord(x) * 2 for x in "bcd"])

    def test_multiple_generators(self):
        self.s.functions = {"range": range}
        s = "[j for i in range(100) if i > 10 for j in range(i) if j < 20]"
        self.t(s, eval(s))

    def test_triple_generators(self):
        self.s.functions = {"range": range}
        s = "[(a,b,c) for a in range(4) for b in range(a) for c in range(b)]"
        self.t(s, eval(s))

    def test_too_long_generator(self):
        self.s.functions = {"range": range}
        s = "[j for i in range(1000) if i > 10 for j in range(i) if j < 20]"
        with self.assertRaises(simpleeval.IterableTooLong):
            self.s.eval(s)

    def test_too_long_generator_2(self):
        self.s.functions = {"range": range}
        s = "[j for i in range(100) if i > 1 for j in range(i+10) if j < 100 for k in range(i*j)]"
        with self.assertRaises(simpleeval.IterableTooLong):
            self.s.eval(s)

    def test_nesting_generators_to_cheat(self):
        self.s.functions = {"range": range}
        s = "[[[c for c in range(a)] for a in range(b)] for b in range(200)]"

        with self.assertRaises(simpleeval.IterableTooLong):
            self.s.eval(s)

    def test_no_leaking_names(self):
        # see issue #52, failing list comprehensions could leak locals
        with self.assertRaises(simpleeval.NameNotDefined):
            self.s.eval('[x if x == "2" else y for x in "123"]')

        with self.assertRaises(simpleeval.NameNotDefined):
            self.s.eval("x")


class TestNames(DRYTest):
    """'names', what other languages call variables..."""

    def test_none(self):
        """what to do when names isn't defined, or is 'none'"""
        with self.assertRaises(NameNotDefined):
            self.t("a == 2", None)

        self.s.names["s"] = 21

        # or if you attempt to assign an unknown name to another
        with self.assertRaises(NameNotDefined):
            with warnings.catch_warnings(record=True) as ws:
                warnings.simplefilter("always")
                self.t("s += a", 21)
        self.assertIsInstance(ws[0].message, simpleeval.AssignmentAttempted)

        self.s.names = None

        with self.assertRaises(InvalidExpression):
            self.t("s", 21)

        self.s.names = {"a": {"b": {"c": 42}}}

        with self.assertRaises(AttributeDoesNotExist):
            self.t("a.b.d**2", 42)

    def test_dict(self):
        """using a normal dict for names lookup"""

        self.s.names = {"a": 42}
        self.t("a + a", 84)

        self.s.names["also"] = 100

        self.t("a + also - a", 100)

        # however, you can't assign to those names:
        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter("always")
            self.t("a = 200", 200)
        self.assertIsInstance(ws[0].message, simpleeval.AssignmentAttempted)

        self.assertEqual(self.s.names["a"], 42)

        # or assign to lists

        self.s.names["b"] = [0]

        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter("always")
            self.t("b[0] = 11", 11)
        self.assertIsInstance(ws[0].message, simpleeval.AssignmentAttempted)

        self.assertEqual(self.s.names["b"], [0])

        # but you can get items from a list:

        self.s.names["b"] = [6, 7]

        self.t("b[0] * b[1]", 42)

        # or from a dict

        self.s.names["c"] = {"i": 11}

        self.t("c['i']", 11)
        self.t("c.get('i')", 11)
        self.t("c.get('j', 11)", 11)
        self.t("c.get('j')", None)

        # you still can't assign though:

        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter("always")
            self.t("c['b'] = 99", 99)
        self.assertIsInstance(ws[0].message, simpleeval.AssignmentAttempted)

        self.assertFalse("b" in self.s.names["c"])

        # and going all 'inception' on it doesn't work either:

        self.s.names["c"]["c"] = {"c": 11}

        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter("always")
            self.t("c['c']['c'] = 21", 21)
        self.assertIsInstance(ws[0].message, simpleeval.AssignmentAttempted)

        self.assertEqual(self.s.names["c"]["c"]["c"], 11)

    def test_dict_attr_access(self):
        # nested dict

        self.assertEqual(self.s.ATTR_INDEX_FALLBACK, True)

        self.s.names = {"a": {"b": {"c": 42}}}

        self.t("a.b.c*2", 84)

        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter("always")
            self.t("a.b.c = 11", 11)
        self.assertIsInstance(ws[0].message, simpleeval.AssignmentAttempted)

        self.assertEqual(self.s.names["a"]["b"]["c"], 42)

        # TODO: Wat?
        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter("always")
            self.t("a.d = 11", 11)

        with self.assertRaises(KeyError):
            self.assertEqual(self.s.names["a"]["d"], 11)

    def test_dict_attr_access_disabled(self):
        # nested dict

        self.s.ATTR_INDEX_FALLBACK = False
        self.assertEqual(self.s.ATTR_INDEX_FALLBACK, False)

        self.s.names = {"a": {"b": {"c": 42}}}

        with self.assertRaises(simpleeval.AttributeDoesNotExist):
            self.t("a.b.c * 2", 84)

        self.t("a['b']['c'] * 2", 84)

        self.assertEqual(self.s.names["a"]["b"]["c"], 42)

    def test_object(self):
        """using an object for name lookup"""
        # pylint: disable=attribute-defined-outside-init

        class TestObject(object):
            @staticmethod
            def method_thing():
                return 42

        o = TestObject()
        o.a = 23
        o.b = 42
        o.c = TestObject()
        o.c.d = 9001

        self.s.names = {"o": o}

        self.t("o", o)
        self.t("o.a", 23)
        self.t("o.b + o.c.d", 9043)

        self.t("o.method_thing()", 42)

        with self.assertRaises(AttributeDoesNotExist):
            self.t("o.d", None)

    def test_func(self):
        """using a function for 'names lookup'"""

        def resolver(_):
            """all names now equal 1024!"""
            return 1024

        self.s.names = resolver

        self.t("a", 1024)
        self.t("a + b - c - d", 0)

        # the function can do stuff with the value it's sent:

        def my_name(node):
            """all names equal their textual name, twice."""
            return node.id + node.id

        self.s.names = my_name

        self.t("a", "aa")

    def test_from_doc(self):
        """the 'name first letter as value' example from the docs"""

        def name_handler(node):
            """return the alphabet number of the first letter of
            the name's textual name"""
            return ord(node.id[0].lower()) - 96

        self.s.names = name_handler
        self.t("a", 1)
        self.t("a + b", 3)

    def test_name_handler_name_not_found(self):
        def name_handler(node):
            if node.id[0] == "a":
                return 21
            raise NameNotDefined(node.id[0], "not found")

        self.s.names = name_handler
        self.s.functions = {"b": lambda: 100}
        self.t("a + a", 42)

        self.t("b()", 100)

        with self.assertRaises(NameNotDefined):
            self.t("c", None)

    def test_name_handler_raises_error(self):
        # What happens if our name-handler raises a different kind of error?
        # we want it to ripple up all the way...

        def name_handler(_node):
            return {}["test"]

        self.s.names = name_handler

        # This should never be accessed:
        self.s.functions = {"c": 42}

        with self.assertRaises(KeyError):
            self.t("c", None)


class TestWhitespace(DRYTest):
    """test that incorrect whitespace (preceding/trailing) doesn't matter."""

    def test_no_whitespace(self):
        self.t("200 + 200", 400)

    def test_trailing(self):
        self.t("200 + 200       ", 400)

    def test_preceding_whitespace(self):
        self.t("    200 + 200", 400)

    def test_preceding_tab_whitespace(self):
        self.t("\t200 + 200", 400)

    def test_preceding_mixed_whitespace(self):
        self.t("  \t 200 + 200", 400)

    def test_both_ends_whitespace(self):
        self.t("  \t 200 + 200  ", 400)


class TestSimpleEval(unittest.TestCase):
    """test the 'simple_eval' wrapper function"""

    def test_basic_run(self):
        self.assertEqual(simple_eval("6*7"), 42)

    def test_default_functions(self):
        self.assertEqual(simple_eval("rand() < 1.0 and rand() > -0.01"), True)
        self.assertEqual(simple_eval("randint(200) < 200 and rand() > 0"), True)


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


class TestExtendingClass(unittest.TestCase):
    """
    It should be pretty easy to extend / inherit from the SimpleEval class,
    to further lock things down, or unlock stuff, or whatever.
    """

    def test_methods_forbidden(self):
        # Example from README
        class EvalNoMethods(simpleeval.SimpleEval):
            def _eval_call(self, node):
                if isinstance(node.func, ast.Attribute):
                    raise simpleeval.FeatureNotAvailable("No methods please, we're British")
                return super(EvalNoMethods, self)._eval_call(node)

        e = EvalNoMethods()

        self.assertEqual(e.eval('"stuff happens"'), "stuff happens")
        self.assertEqual(e.eval("22 + 20"), 42)
        self.assertEqual(e.eval('int("42")'), 42)

        with self.assertRaises(simpleeval.FeatureNotAvailable):
            e.eval('"  blah  ".strip()')


class TestExceptions(unittest.TestCase):
    """
    confirm a few attributes exist properly and haven't been
    eaten by 2to3 or whatever... (see #41)
    """

    def test_functionnotdefined(self):
        try:
            raise FunctionNotDefined("foo", "foo in bar")
        except FunctionNotDefined as e:
            assert hasattr(e, "func_name")
            assert getattr(e, "func_name") == "foo"
            assert hasattr(e, "expression")
            assert getattr(e, "expression") == "foo in bar"

    def test_namenotdefined(self):
        try:
            raise NameNotDefined("foo", "foo in bar")
        except NameNotDefined as e:
            assert hasattr(e, "name")
            assert getattr(e, "name") == "foo"
            assert hasattr(e, "expression")
            assert getattr(e, "expression") == "foo in bar"

    def test_attributedoesnotexist(self):
        try:
            raise AttributeDoesNotExist("foo", "foo in bar")
        except AttributeDoesNotExist as e:
            assert hasattr(e, "attr")
            assert getattr(e, "attr") == "foo"
            assert hasattr(e, "expression")
            assert getattr(e, "expression") == "foo in bar"


class TestUnusualComparisons(DRYTest):
    def test_custom_comparison_returner(self):
        class Blah(object):
            def __gt__(self, other):
                return self

        b = Blah()
        self.s.names = {"b": b}
        self.t("b > 2", b)

    def test_custom_comparison_doesnt_return_boolable(self):
        """
        SqlAlchemy, bless it's cotton socks, returns BinaryExpression objects
        when asking for comparisons between things.  These BinaryExpressions
        raise a TypeError if you try and check for Truthyiness.
        """

        class BinaryExpression(object):
            def __init__(self, value):
                self.value = value

            def __eq__(self, other):
                return self.value == getattr(other, "value", other)

            def __repr__(self):  # pragma: no cover
                return "<BinaryExpression:{}>".format(self.value)

            def __bool__(self):  # pragma: no cover
                # This is the only important part, to match SqlAlchemy - the rest
                # of the methods are just to make testing a bit easier...
                raise TypeError("Boolean value of this clause is not defined")

        class Blah(object):
            def __gt__(self, other):
                return BinaryExpression("GT")

            def __lt__(self, other):
                return BinaryExpression("LT")

        b = Blah()
        # These should not crash:
        self.assertEqual(b > 2, BinaryExpression("GT"))
        self.assertEqual(b < 2, BinaryExpression("LT"))

        # And should also work in simpleeval
        self.s.names = {"b": b}
        self.t("b > 2", BinaryExpression("GT"))
        self.t("1 < 5 > b", BinaryExpression("LT"))


class TestGetItemUnhappy(DRYTest):
    # Again, SqlAlchemy doing unusual things.  Throwing it's own errors, rather than
    # expected types...

    def test_getitem_not_implemented(self):
        class Meh(object):
            def __getitem__(self, key):
                raise NotImplementedError("booya!")

            def __getattr__(self, key):
                return 42

        m = Meh()

        self.assertEqual(m.anything, 42)
        with self.assertRaises(NotImplementedError):
            m["nothing"]  # pylint: disable=pointless-statement

        self.s.names = {"m": m}
        self.t("m.anything", 42)

        with self.assertRaises(NotImplementedError):
            self.t("m['nothing']", None)

        self.s.ATTR_INDEX_FALLBACK = False

        self.t("m.anything", 42)

        with self.assertRaises(NotImplementedError):
            self.t("m['nothing']", None)


class TestShortCircuiting(DRYTest):
    def test_shortcircuit_if(self):
        x = []

        def foo(y):
            x.append(y)
            return y

        self.s.functions = {"foo": foo}
        self.t("foo(1) if foo(2) else foo(3)", 1)
        self.assertListEqual(x, [2, 1])

        x = []
        self.t("42 if True else foo(99)", 42)
        self.assertListEqual(x, [])

    def test_shortcircuit_comparison(self):
        x = []

        def foo(y):
            x.append(y)
            return y

        self.s.functions = {"foo": foo}
        self.t("foo(11) < 12", True)
        self.assertListEqual(x, [11])
        x = []

        self.t("1 > 2 < foo(22)", False)
        self.assertListEqual(x, [])


class TestDisallowedFunctions(DRYTest):
    def test_functions_are_disallowed_at_init(self):
        DISALLOWED = [type, isinstance, eval, getattr, setattr, help, repr, compile, open, exec]

        for f in simpleeval.DISALLOW_FUNCTIONS:
            assert f in DISALLOWED

        for x in DISALLOWED:
            with self.assertRaises(FeatureNotAvailable):
                SimpleEval(functions={"foo": x})

    def test_functions_are_disallowed_in_expressions(self):
        DISALLOWED = [type, isinstance, eval, getattr, setattr, help, repr, compile, open, exec]

        for f in simpleeval.DISALLOW_FUNCTIONS:
            assert f in DISALLOWED

        DF = simpleeval.DEFAULT_FUNCTIONS.copy()

        for x in DISALLOWED:
            simpleeval.DEFAULT_FUNCTIONS = DF.copy()
            with self.assertRaises(FeatureNotAvailable):
                s = SimpleEval()
                s.functions["foo"] = x
                s.eval("foo(42)")

        simpleeval.DEFAULT_FUNCTIONS = DF.copy()

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


@unittest.skipIf(platform.python_implementation() == "PyPy", "GC set_debug not available in PyPy")
class TestReferenceCleanup(DRYTest):
    """Test cleanup without cyclic references"""

    # pylint: disable=attribute-defined-outside-init

    def setUp(self):
        self._initial_gc_isenabled = gc.isenabled()

        gc.disable()
        gc.set_debug(gc.DEBUG_SAVEALL)

        gc.collect()
        self._initial_garbage_len = len(gc.garbage)

    def tearDown(self):
        gc.collect()
        self._final_garbage_len = len(gc.garbage)

        if self._initial_gc_isenabled:
            gc.enable()

        self.assertEqual(self._initial_garbage_len, self._final_garbage_len)

    def test_simpleeval_cleanup(self):
        simpleeval.SimpleEval()


class TestNoEntries(DRYTest):
    def test_no_functions(self):
        self.s.eval("int(42)")
        with self.assertRaises(FunctionNotDefined):
            s = SimpleEval(functions={})
            s.eval("int(42)")

    def test_no_names(self):
        # does not work on current Py3, True et al. are keywords now
        self.s.eval("True")
        # with self.assertRaises(NameNotDefined):
        s = SimpleEval(names={})
        if sys.version_info < (3,):
            with self.assertRaises(NameNotDefined):
                s.eval("True")
        else:
            s.eval("True")

    def test_no_operators(self):
        self.s.eval("1+2")
        self.s.eval("~2")
        s = SimpleEval(operators={})

        with self.assertRaises(OperatorNotDefined):
            s.eval("1+2")

        with self.assertRaises(OperatorNotDefined):
            s.eval("~ 2")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
