import ast

from simpleeval import CompoundEvalWithAssignments, FeatureNotAvailable


class SimpleExecutor(CompoundEvalWithAssignments):
    def __init__(self, operators=None, functions=None, names=None):
        super(SimpleExecutor, self).__init__(operators, functions, names)

    def eval(self, expr):  # allow for ast.Assign to set names
        self.expr = expr
        expression = ast.parse(expr.strip()).body[0]
        return self._eval_expression(expression)

    def exec(self, expr):
        self.expr = expr
        body = ast.parse(expr.strip()).body
        for expression in body:
            self._eval_expression(expression)

    def _eval_expression(self, expression):
        if isinstance(expression, ast.Expr):
            return self._eval(expression.value)
        elif isinstance(expression, ast.Assign):
            for target in expression.targets:  # a = b = 1
                self._assign(target, expression.value)
        elif isinstance(expression, ast.AugAssign):  # a += 1
            self._aug_assign(expression.target, expression.op, expression.value)
        # TODO py 3.8 walrus op
        else:
            raise FeatureNotAvailable("Unknown ast body type: {}".format(type(expression).__name__))
