import unittest

from simpleeval import EvalWithCompoundTypes


class TestDictionaryEvaluationOrder(unittest.TestCase):
    def test_key_before_value(self):
        calls = []
        for expression in (
            "{key(): value()}",
            "{key(): value() for item in [0]}",
        ):
            with self.subTest(expression=expression):
                calls.clear()

                def key():
                    calls.append("key")
                    return len(calls)

                def value():
                    calls.append("value")
                    return len(calls)

                evaluator = EvalWithCompoundTypes(functions={"key": key, "value": value})
                self.assertEqual(evaluator.eval(expression), {1: 2})
                self.assertEqual(calls, ["key", "value"])

    def test_key_error_does_not_evaluate_value(self):
        calls = []
        for expression in (
            "{key(): value()}",
            "{key(): value() for item in [0]}",
        ):
            with self.subTest(expression=expression):
                calls.clear()

                def key():
                    raise ValueError("key failed")

                def value():
                    calls.append("value")
                    return 1

                evaluator = EvalWithCompoundTypes(functions={"key": key, "value": value})
                with self.assertRaisesRegex(ValueError, "key failed"):
                    evaluator.eval(expression)
                self.assertEqual(calls, [])

    def test_multiple_items_keep_left_to_right_order(self):
        calls = []
        for expression in (
            "{key(1): value(1), key(2): value(2)}",
            "{key(item): value(item) for item in [1, 2]}",
        ):
            with self.subTest(expression=expression):
                calls.clear()

                def key(item):
                    calls.append(("key", item))
                    return item

                def value(item):
                    calls.append(("value", item))
                    return item * 10

                evaluator = EvalWithCompoundTypes(functions={"key": key, "value": value})
                self.assertEqual(evaluator.eval(expression), {1: 10, 2: 20})
                self.assertEqual(calls, [("key", 1), ("value", 1), ("key", 2), ("value", 2)])
