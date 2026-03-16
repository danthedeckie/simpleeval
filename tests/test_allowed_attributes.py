import simpleeval
from simpleeval import BASIC_ALLOWED_ATTRS, FeatureNotAvailable, simple_eval

from .base import DRYTest


class TestAllowedAttributes(DRYTest):
    def setUp(self):
        self.saved_disallow_methods = simpleeval.DISALLOW_METHODS
        simpleeval.DISALLOW_METHODS = []
        super().setUp()

    def tearDown(self) -> None:
        simpleeval.DISALLOW_METHODS = self.saved_disallow_methods
        return super().tearDown()

    def test_allowed_attrs_(self):
        self.s.allowed_attrs = BASIC_ALLOWED_ATTRS
        self.t("5 + 5", 10)
        self.t('"   hello  ".strip()', "hello")

    def test_allowed_extra_attr(self):
        class Foo:
            def bar(self):
                return 42

        assert Foo().bar() == 42

        extended_attrs = BASIC_ALLOWED_ATTRS.copy()
        extended_attrs[Foo] = {"bar"}

        simple_eval("foo.bar()", names={"foo": Foo()}, allowed_attrs=extended_attrs)

    def test_disallowed_extra_attr(self):
        class Foo:
            bar = 42
            hidden = 100

        assert Foo().bar == 42

        extended_attrs = BASIC_ALLOWED_ATTRS.copy()
        extended_attrs[Foo] = {"bar"}

        self.assertEqual(
            simple_eval("foo.bar", names={"foo": Foo()}, allowed_attrs=extended_attrs), 42
        )
        with self.assertRaisesRegex(FeatureNotAvailable, r".*'\.hidden' access not allowed.*"):
            self.assertEqual(
                simple_eval("foo.hidden", names={"foo": Foo()}, allowed_attrs=extended_attrs), 42
            )

    def test_disallowed_types(self):
        class Foo:
            bar = 42

        assert Foo().bar == 42

        with self.assertRaises(FeatureNotAvailable):
            simple_eval("foo.bar", names={"foo": Foo()}, allowed_attrs=BASIC_ALLOWED_ATTRS)

    def test_breakout_via_generator(self):
        # Thanks decorator-factory
        class Foo:
            def bar(self):
                yield "Hello, world!"

        # Test the generator does work - also adds the `yield` to codecov...
        assert list(Foo().bar()) == ["Hello, world!"]

        evil = "foo.bar().gi_frame.f_globals['__builtins__'].exec('raise RuntimeError(\"Oh no\")')"

        extended_attrs = BASIC_ALLOWED_ATTRS.copy()
        extended_attrs[Foo] = {"bar"}

        with self.assertRaisesRegex(FeatureNotAvailable, r".*attempted to access `\.gi_frame`.*"):
            simple_eval(evil, names={"foo": Foo()}, allowed_attrs=extended_attrs)
