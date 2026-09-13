import unittest

from simpleeval import (
    AttributeDoesNotExist,
    FunctionNotDefined,
    NameNotDefined,
)


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
            assert e.func_name == "foo"
            assert hasattr(e, "expression")
            assert e.expression == "foo in bar"

    def test_namenotdefined(self):
        try:
            raise NameNotDefined("foo", "foo in bar")
        except NameNotDefined as e:
            assert hasattr(e, "name")
            assert e.name == "foo"
            assert hasattr(e, "expression")
            assert e.expression == "foo in bar"

    def test_attributedoesnotexist(self):
        try:
            raise AttributeDoesNotExist("foo", "foo in bar")
        except AttributeDoesNotExist as e:
            assert hasattr(e, "attr")
            assert e.attr == "foo"
            assert hasattr(e, "expression")
            assert e.expression == "foo in bar"
