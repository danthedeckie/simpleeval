import simpleeval
from simpleeval import (
    EvalWithCompoundTypes,
    FeatureNotAvailable,
)

from .base import DRYTest


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
