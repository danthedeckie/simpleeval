'''
    Unit tests for simpleeval.
    --------------------------

    Most of this stuff is pretty basic.

'''
# pylint: disable=too-many-public-methods, missing-docstring

import unittest, operator, ast
import simpleeval
from simpleeval import (
    SimpleEval, EvalWithCompoundTypes, NameNotDefined,
    InvalidExpression, AttributeDoesNotExist, simple_eval
)


class DRYTest(unittest.TestCase):
    ''' Stuff we need to do every test, let's do here instead..
        Don't Repeat Yourself. '''

    def setUp(self):
        ''' initialize a SimpleEval '''
        self.s = SimpleEval()

    def t(self, expr, shouldbe): #pylint: disable=invalid-name
        ''' test an evaluation of an expression against an expected answer '''
        return self.assertEqual(self.s.eval(expr), shouldbe)

class TestBasic(DRYTest):
    ''' Simple expressions. '''

    def test_maths_with_ints(self):
        ''' simple maths expressions '''

        self.t("21 + 21", 42)
        self.t("6*7", 42)
        self.t("20 + 1 + (10*2) + 1", 42)
        self.t("100/10", 10)
        self.t("12*12", 144)
        self.t("2 ** 10", 1024)
        self.t("100 % 9", 1)

    def test_bools_and_or(self):
        self.t('True and False', False)
        self.t('True or False', True)
        self.t('1 - 1 or 21', 21)
        self.t('1 - 1 and 11', 0)
        self.t('110 == 100 + 10 and True', True)
        self.t('110 != 100 + 10 and True', False)
        self.t('False or 42', 42)

        self.s.names = {'out': True, 'position': 3}
        self.t('(out and position <=6 and -10)'
                ' or (out and position > 6 and -5)'
                ' or (not out and 15)', -10)

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

        self.t('1 < 2 < 3 < 4', 1 < 2 < 3 < 4)
        self.t('1 < 2 > 3 < 4', 1 < 2  > 3 < 4)

        self.t('1<2<1+1', 1<2<1+1)
        self.t('1 == 1 == 2', 1 == 1 == 2)
        self.t('1 == 1 < 2', 1 == 1 < 2)

    def test_mixed_comparisons(self):
        self.t("1 > 0.999999", True)
        self.t("1 == True", True)  # Note ==, not 'is'.
        self.t("0 == False", True)  # Note ==, not 'is'.
        self.t("False == False", True)
        self.t("False < True", True)

    def test_if_else(self):
        ''' x if y else z '''

        # and test if/else expressions:
        self.t("'a' if 1 == 1 else 'b'", 'a')
        self.t("'a' if 1 > 2 else 'b'", 'b')

        # and more complex expressions:
        self.t("'a' if 4 < 1 else 'b' if 1 == 2 else 'c'", 'c')

    def test_default_conversions(self):
        ''' conversion between types '''

        self.t('int("20") + int(0.22*100)', 42)
        self.t('float("42")', 42.0)
        self.t('"Test Stuff!" + str(11)', "Test Stuff!11")

    def test_slicing(self):
        self.s.operators[ast.Slice] = operator.getslice if hasattr(operator, "getslice") else operator.getitem
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


class TestFunctions(DRYTest):
    ''' Functions for expressions to play with '''

    def test_load_file(self):
        ''' add in a function which loads data from an external file. '''

        # write to the file:

        with open("file.txt", 'w') as f:
            f.write("42")

        # define the function we'll send to the eval'er

        def load_file(filename):
            ''' load a file and return its contents '''
            with open(filename) as f:
                return f.read()

        # simple load:

        self.s.functions = {"read": load_file}
        self.t("read('file.txt')", "42")

        # and we should have *replaced* the default functions. Let's check:

        with self.assertRaises(simpleeval.FunctionNotDefined):
            self.t("int(read('file.txt'))", 42)

        # OK, so we can load in the default functions as well...

        self.s.functions.update(simpleeval.DEFAULT_FUNCTIONS)

        # now it works:

        self.t("int(read('file.txt'))", 42)

    def test_randoms(self):
        ''' test the rand() and randint() functions '''

        self.s.functions['type'] = type

        self.t('type(randint(1000))', int)
        self.t('type(rand())', float)

        self.t("randint(20)<20", True)
        self.t("rand()<1.0", True)

        # I don't know how to further test these functions.  Ideas?

    def test_methods(self):
        self.t('"WORD".lower()', 'word')
        self.t('"{}:{}".format(1, 2)', '1:2')

    def test_function_args_none(self):
        def foo():
            return 42

        self.s.functions['foo'] = foo
        self.t('foo()', 42)

    def test_function_args_required(self):
        def foo(toret):
            return toret

        self.s.functions['foo'] = foo
        with self.assertRaises(TypeError):
            self.t('foo()', 42)

        self.t('foo(12)', 12)
        self.t('foo(toret=100)', 100)

    def test_function_args_defaults(self):
        def foo(toret=9999):
            return toret

        self.s.functions['foo'] = foo
        self.t('foo()', 9999)

        self.t('foo(12)', 12)
        self.t('foo(toret=100)', 100)

    def test_function_args_bothtypes(self):
        def foo(mult, toret=100):
            return toret * mult

        self.s.functions['foo'] = foo
        with self.assertRaises(TypeError):
            self.t('foo()', 9999)

        self.t('foo(2)', 200)

        with self.assertRaises(TypeError):
            self.t('foo(toret=100)', 100)

        self.t('foo(4, toret=4)', 16)
        self.t('foo(mult=2, toret=4)', 8)
        self.t('foo(2, 10)', 20)


class TestOperators(DRYTest):
    ''' Test adding in new operators, removing them, make sure it works. '''
    pass


class TestTryingToBreakOut(DRYTest):
    ''' Test various weird methods to break the security sandbox... '''

    def test_import(self):
        ''' usual suspect. import '''
        # cannot import things:
        with self.assertRaises(AttributeError):
            self.t("import sys", None)

    def test_long_running(self):
        ''' exponent operations can take a long time. '''
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

    def test_string_length(self):

        with self.assertRaises(simpleeval.StringTooLong):
            self.t("50000*'text'", 0)

        with self.assertRaises(simpleeval.StringTooLong):
            self.t("'text'*50000", 0)

        with self.assertRaises(simpleeval.StringTooLong):
            self.t("('text'*50000)*1000", 0)

        with self.assertRaises(simpleeval.StringTooLong):
            self.t("(50000*'text')*1000", 0)

        self.t("'stuff'*20000", 20000*'stuff')

        self.t("20000*'stuff'", 20000*'stuff')

        with self.assertRaises(simpleeval.StringTooLong):
            self.t("('stuff'*20000) + ('stuff'*20000) ", 0)

        with self.assertRaises(simpleeval.StringTooLong):
            self.t("'stuff'*100000", 100000*'stuff')

        with self.assertRaises(simpleeval.StringTooLong):
            self.t("'" + (10000*"stuff") +"'*100", 0)

        with self.assertRaises(simpleeval.StringTooLong):
            self.t("'" + (50000 * "stuff") + "'", 0)

    def test_python_stuff(self):
        ''' other various pythony things. '''
        # it only evaluates the first statement:
        self.t("a = 11; x = 21; x + x", 11)

        # list comprehensions don't work:
        # this could be changed in a future release, if people want...
        with self.assertRaises(simpleeval.FeatureNotAvailable):
            self.t("[x for x in (1, 2, 3)]", (1, 2, 3))


    def test_function_globals_breakout(self):
        ''' by accessing function.__globals__ or func_... '''
        # thanks perkinslr.

        self.s.functions['x'] = lambda y:y+y
        self.t('x(100)', 200)

        with self.assertRaises(simpleeval.FeatureNotAvailable):
            self.t('x.__globals__', None)

        class EscapeArtist(object):
            def trapdoor(self):
                return 42

            def _quasi_private(self):
                return 84

        self.s.names['houdini'] = EscapeArtist()

        with self.assertRaises(simpleeval.FeatureNotAvailable):
            self.t('houdini.trapdoor.__globals__', 0)

        with self.assertRaises(simpleeval.FeatureNotAvailable):
            self.t('houdini.trapdoor.func_globals', 0)

        with self.assertRaises(simpleeval.FeatureNotAvailable):
            self.t('houdini._quasi_private()', 0)

        # and test for changing '_' to '__':

        dis = simpleeval.DISALLOW_PREFIXES
        simpleeval.DISALLOW_PREFIXES = ['func_']

        self.t('houdini._quasi_private()', 84)

        # and return things to normal

        simpleeval.DISALLOW_PREFIXES = dis

    def test_builtins_private_access(self):
        # explicit attempt of the exploit from perkinslr
        with self.assertRaises(simpleeval.FeatureNotAvailable):
            self.t("True.__class__.__class__.__base__.__subclasses__()[-1].__init__.func_globals['sys'].exit(1)", 42)


class TestCompoundTypes(DRYTest):
    ''' Test the compound-types edition of the library '''

    def setUp(self):
        self.s = EvalWithCompoundTypes()

    def test_dict(self):
        self.t('{}', {})
        self.t('{"foo": "bar"}', {'foo': 'bar'})
        self.t('{"foo": "bar"}["foo"]', 'bar')
        self.t('dict()', {})
        self.t('dict(a=1)', {'a': 1})


    def test_dict_contains(self):
        self.t('{"a":22}["a"]', 22)
        with self.assertRaises(KeyError):
            self.t('{"a":22}["b"]', 22)

        self.t('{"a": 24}.get("b", 11)', 11)
        self.t('"a" in {"a": 24}', True)

    def test_tuple(self):
        self.t('()', ())
        self.t('(1,)', (1,))
        self.t('(1, 2, 3, 4, 5, 6)', (1, 2, 3, 4, 5, 6))
        self.t('(1, 2) + (3, 4)', (1, 2, 3, 4))
        self.t('(1, 2, 3)[1]', 2)
        self.t('tuple()', ())
        self.t('tuple("foo")', ('f', 'o', 'o'))


    def test_tuple_contains(self):
        self.t('("a","b")[1]', 'b')
        with self.assertRaises(IndexError):
            self.t('("a","b")[5]', 'b')
        self.t('"a" in ("b","c","a")', True)

    def test_list(self):
        self.t('[]', [])
        self.t('[1]', [1])
        self.t('[1, 2, 3, 4, 5]', [1, 2, 3, 4, 5])
        self.t('[1, 2, 3][1]', 2)
        self.t('list()', [])
        self.t('list("foo")', ['f', 'o', 'o'])

    def test_list_contains(self):
        self.t('["a","b"][1]', 'b')
        with self.assertRaises(IndexError):
            self.t('("a","b")[5]', 'b')

        self.t('"b" in ["a","b"]', True)


    def test_set(self):
        self.t('{1}', {1})
        self.t('{1, 2, 1, 2, 1, 2, 1}', {1, 2})
        self.t('set()', set())
        self.t('set("foo")', {'f', 'o'})

        self.t('2 in {1,2,3,4}', True)
        self.t('22 not in {1,2,3,4}', True)


class TestNames(DRYTest):
    ''' 'names', what other languages call variables... '''

    def test_none(self):
        ''' what to do when names isn't defined, or is 'none' '''
        with self.assertRaises(NameNotDefined):
            self.t("a == 2", None)

        self.s.names["s"] = 21

        with self.assertRaises(NameNotDefined):
            self.t("s += a", 21)

        self.s.names = None

        with self.assertRaises(InvalidExpression):
            self.t('s', 21)

        self.s.names = {'a' : {'b': {'c': 42}}}

        with self.assertRaises(AttributeDoesNotExist):
            self.t('a.b.d**2', 42)


    def test_dict(self):
        ''' using a normal dict for names lookup '''

        self.s.names = {'a': 42}
        self.t("a + a", 84)

        self.s.names['also'] = 100

        self.t("a + also - a", 100)

        # however, you can't assign to those names:

        self.t("a = 200", 200)

        self.assertEqual(self.s.names['a'], 42)

        # or assign to lists

        self.s.names['b'] = [0]

        self.t("b[0] = 11", 11)

        self.assertEqual(self.s.names['b'], [0])

        # but you can get items from a list:

        self.s.names['b'] = [6, 7]

        self.t("b[0] * b[1]", 42)

        # or from a dict

        self.s.names['c'] = {'i': 11}

        self.t("c['i']", 11)

        # you still can't assign though:

        self.t("c['b'] = 99", 99)

        self.assertFalse('b' in self.s.names['c'])

        # and going all 'inception' on it doesn't work either:

        self.s.names['c']['c'] = {'c': 11}

        self.t("c['c']['c'] = 21", 21)

        self.assertEqual(self.s.names['c']['c']['c'], 11)

        # nested dict

        self.s.names = {'a' : {'b': {'c': 42}}}

        self.t("a.b.c*2", 84)

        self.t("a.b.c = 11", 11)

        self.assertEqual(self.s.names['a']['b']['c'], 42)

        self.t("a.d = 11", 11)

        with self.assertRaises(KeyError):
            self.assertEqual(self.s.names['a']['d'], 11)

    def test_object(self):
        ''' using an object for name lookup '''
        class TestObject(object):
           def method_thing(self):
                return 42

        o = TestObject()
        o.a = 23
        o.b = 42
        o.c = TestObject()
        o.c.d = 9001

        self.s.names = {'o' : o}

        self.t('o', o)
        self.t('o.a', 23)
        self.t('o.b + o.c.d', 9043)

        self.t('o.method_thing()', 42)

        with self.assertRaises(AttributeDoesNotExist):
            self.t('o.d', None)

    def test_func(self):
        ''' using a function for 'names lookup' '''

        def resolver(node): # pylint: disable=unused-argument
            ''' all names now equal 1024! '''
            return 1024

        self.s.names = resolver

        self.t("a", 1024)
        self.t("a + b - c - d", 0)

        # the function can do stuff with the value it's sent:

        def my_name(node):
            ''' all names equal their textual name, twice. '''
            return node.id + node.id

        self.s.names = my_name

        self.t("a", "aa")

    def test_from_doc(self):
        ''' the 'name first letter as value' example from the docs '''

        def name_handler(node):
            ''' return the alphabet number of the first letter of
                the name's textual name '''
            return ord(node.id[0].lower())-96

        self.s.names = name_handler
        self.t('a', 1)
        self.t('a + b', 3)


class Test_whitespace(DRYTest):
    ''' test that incorrect whitespace (preceding/trailing) doesn't matter. '''
    def test_no_whitespace(self):
        self.t('200 + 200', 400)

    def test_trailing(self):
        self.t('200 + 200       ', 400)

    def test_preciding_whitespace(self):
        self.t('    200 + 200', 400)

    def test_preceding_tab_whitespace(self):
        self.t("\t200 + 200", 400)

    def test_preceding_mixed_whitespace(self):
        self.t("  \t 200 + 200", 400)

    def test_both_ends_whitespace(self):
        self.t("  \t 200 + 200  ", 400)



class Test_simple_eval(unittest.TestCase):
    ''' test the 'simple_eval' wrapper function '''
    def test_basic_run(self):
        self.assertEqual(simple_eval('6*7'), 42)

    def test_default_functions(self):
        self.assertEqual(simple_eval('rand() < 1.0 and rand() > -0.01'), True)
        self.assertEqual(simple_eval('randint(200) < 200 and rand() > 0'), True)

if __name__ == '__main__':
    unittest.main()
