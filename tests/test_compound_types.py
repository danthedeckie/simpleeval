from simpleeval import (
    EvalWithCompoundTypes,
    FeatureNotAvailable,
    FunctionNotDefined,
    NameNotDefined,
)

from .base import DRYTest


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
