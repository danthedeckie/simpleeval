import ast
import unittest

import simpleeval


class TestExtendingClass(unittest.TestCase):
    """
    It should be pretty easy to extend / inherit from the SimpleEval class,
    to further lock things down, or unlock stuff, or whatever.
    """

    def test_methods_forbidden(self):
        # Example from README
        class EvalNoMethods(simpleeval.SimpleEval):
            def _eval_call(self, node):
                if isinstance(node.func, ast.Attribute):
                    raise simpleeval.FeatureNotAvailable("No methods please, we're British")
                return super(EvalNoMethods, self)._eval_call(node)

        e = EvalNoMethods()

        self.assertEqual(e.eval('"stuff happens"'), "stuff happens")
        self.assertEqual(e.eval("22 + 20"), 42)
        self.assertEqual(e.eval('int("42")'), 42)

        with self.assertRaises(simpleeval.FeatureNotAvailable):
            e.eval('"  blah  ".strip()')
