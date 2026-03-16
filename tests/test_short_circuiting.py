from .base import DRYTest


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
