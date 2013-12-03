'''
    Unit tests for simpleeval.
    --------------------------

    Most of this stuff is pretty basic.

'''

import unittest
import simpleeval
from simpleeval import SimpleEval

class DRYTest(unittest.TestCase):
    ''' Stuff we need to do every test, let's do here instead..
        Don't Repeat Yourself. '''

    def setUp(self):
        ''' initialize a SimpleEval '''
        self.s = SimpleEval()

    def t(self, expr, shouldbe):
        ''' test an evaluation of an expression against an expected answer '''
        return self.assertEqual(self.s.eval(expr), shouldbe)

class TestBasic(DRYTest):
    ''' Simple expressions. '''

    def test_maths_exprs(self):
        self.t("21 + 21", 42)
        self.t("6*7", 42)
        self.t("20 + 1 + (10*2) + 1", 42)
        self.t("100/10", 10)
        self.t("12*12", 144)
        self.t("2 ** 10", 1024)
        self.t("100 % 9", 1)

        # and test if/else expressions:
        self.t("'a' if 1 == 1 else 'b'", 'a')
        self.t("'a' if 1 > 2 else 'b'", 'b')

        # and more complex expressions:
        self.t("'a' if 4 < 1 else 'b' if 1 == 2 else 'c'", 'c')

    def test_default_conversions(self):
        self.t('int("20") + int(0.22*100)', 42)
        self.t('float("42")', 42.0)
        self.t('"Test Stuff!" + str(11)', u"Test Stuff!11")

class TestFunctions(DRYTest):

    def test_load_file(self):
        ''' add in a function which loads data from an external file. '''

        # write to the file:

        with open("file.txt",'w') as f:
            f.write("42")

        # define the function we'll send to the eval'er

        def load_file(filename):
            ''' load a file and return its contents '''
            with open(filename) as f:
                return f.read()

        # simple load:

        self.s.functions = {u"read": load_file}
        self.t("read('file.txt')", "42")

        # and we should have *replaced* the default functions. Let's check:

        with self.assertRaises(simpleeval.FunctionNotDefined):
            self.t("int(read('file.txt'))", 42)

        # OK, so we can load in the default functions as well...

        self.s.functions.update(simpleeval.DEFAULT_FUNCTIONS)

        # now it works:

        self.t("int(read('file.txt'))", 42)

class TestOperators(DRYTest):
    pass

class TestTryingToBreakOut(DRYTest):
    def test_import(self):
        pass

    def test_python_stuff(self):
        # it only evaluates the first statement:
        self.t("a = 11; x = 21; x + x", 11)

        # list comprehensions don't work:
        # this could be changed in a future release, if people want...
        with self.assertRaises(simpleeval.FeatureNotAvailable):
            self.t("[x for x in (1,2,3)]", (1,2,3))

        # cannot import things:
        with self.assertRaises(AttributeError):
            self.t("import sys", None)

class TestNames(DRYTest):
    def test_none(self):
        ''' what to do when names isn't defined, or is 'none' '''
        pass

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

    def test_func(self):
        ''' using a function for 'names lookup' '''
        def resolver(node):
            return 1024

        self.s.names = resolver

        self.t("a", 1024)
        self.t("a + b - c - d", 0)

        # the function can do stuff with the value it's sent:

        def my_name(node):
            return node.id + node.id

        self.s.names = my_name

        self.t("a", "aa")

    def test_from_doc(self):
        ''' the 'name first letter as value' example from the docs '''

        def name_handler(node):
            return ord(node.id[0].lower())-96

        self.s.names=name_handler
        self.t('a', 1)
        self.t('a + b', 3)
        

if __name__ == '__main__':
    try:
        import nose
        nose.run()
    except ImportError:
        unittest.main()
