import ast
import operator
import sys

from simpleeval import (
    FeatureNotAvailable,
    InvalidExpression,
)

from .base import DRYTest


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
            "(out and position <=6 and -10) or (out and position > 6 and -5) or (not out and 15)",
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
