from .base import DRYTest


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
