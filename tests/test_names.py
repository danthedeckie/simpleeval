import warnings

import simpleeval
from simpleeval import (
    AttributeDoesNotExist,
    InvalidExpression,
    NameNotDefined,
)

from .base import DRYTest


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
