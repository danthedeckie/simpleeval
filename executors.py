import ast

from simpleeval import CompoundEvalWithAssignments, EvalWithAssignments


class SimpleExecutor(EvalWithAssignments):
    def __init__(self, operators=None, functions=None, names=None):
        super(SimpleExecutor, self).__init__(operators, functions, names)

    def exec(self, expr):
        self.expr = expr
        body = ast.parse(expr.strip()).body
        return self._exec(body)

    def _exec(self, body):
        for expression in body:
            try:
                self._eval(expression)
            except Return as r:
                return r.value


class ExecutorWithControl(SimpleExecutor, CompoundEvalWithAssignments):
    def __init__(self, operators=None, functions=None, names=None):
        super(ExecutorWithControl, self).__init__(operators, functions, names)

        self.nodes.update({
            ast.If: self._exec_if,
            ast.For: self._exec_for,
            ast.While: self._exec_while,
            Value: lambda val: val.value,
            ast.Break: self._exec_break,
            ast.Continue: self._exec_continue,
            ast.Return: self._exec_return
        })

    def _exec_if(self, node):
        test = self._eval(node.test)
        if test:
            self._exec(node.body)
        else:
            self._exec(node.orelse)

    def _exec_for(self, node):
        for item in self._eval(node.iter):
            self._assign(node.target, Value(item))
            try:
                self._exec(node.body)
            except Break:
                break
            except Continue:
                continue
        else:
            self._exec(node.orelse)

    def _exec_while(self, node):
        while self._eval(node.test):
            try:
                self._exec(node.body)
            except Break:
                break
            except Continue:
                continue
        else:
            self._exec(node.orelse)

    def _exec_break(self, node):
        raise Break

    def _exec_continue(self, node):
        raise Continue

    def _exec_return(self, node):
        raise Return(self._eval(node.value))


class Value:  # used to pass already-evaluated values to assignments
    def __init__(self, value):
        self.value = value


# exceptions used to propogate loop-breaking signals
class Return(BaseException):
    def __init__(self, retval):
        self.value = retval


class Break(BaseException):
    pass


class Continue(BaseException):
    pass
