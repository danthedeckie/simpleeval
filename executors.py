import ast

from simpleeval import CompoundEvalWithAssignments, EvalWithAssignments, MAX_COMPREHENSION_LENGTH, IterableTooLong, \
    InvalidExpression

MAX_NUM_STATEMENTS = 100000


class TooManyStatements(InvalidExpression):
    """I've only got so much time to spare!"""
    pass


class SimpleExecutor(EvalWithAssignments):
    def __init__(self, operators=None, functions=None, names=None):
        super(SimpleExecutor, self).__init__(operators, functions, names)
        self._num_stmts = 0

    def eval(self, expr):
        self._num_stmts = 0
        return super(SimpleExecutor, self).eval(expr)

    def exec(self, expr):
        self._num_stmts = 0
        self.expr = expr
        body = ast.parse(expr.strip()).body
        return self._exec(body)

    def _eval(self, node):
        self._num_stmts += 1
        if self._num_stmts > MAX_NUM_STATEMENTS:
            raise TooManyStatements("You are trying to execute too many statements.")

        return super(SimpleExecutor, self)._eval(node)

    def _exec(self, body):
        for expression in body:
            try:
                self._eval(expression)
            except _Return as r:
                return r.value


class ExecutorWithControl(SimpleExecutor, CompoundEvalWithAssignments):
    def __init__(self, operators=None, functions=None, names=None):
        super(ExecutorWithControl, self).__init__(operators, functions, names)

        self.nodes.update({
            ast.If: self._exec_if,
            ast.For: self._exec_for,
            ast.While: self._exec_while,
            ast.Break: self._exec_break,
            ast.Continue: self._exec_continue,
            ast.Return: self._exec_return
        })

    def exec(self, expr):
        self._max_count = 0
        return super(ExecutorWithControl, self).exec(expr)

    def _exec_if(self, node):
        test = self._eval(node.test)
        if test:
            self._exec(node.body)
        else:
            self._exec(node.orelse)

    def _exec_for(self, node):
        for item in self._eval(node.iter):
            self._max_count += 1
            if self._max_count > MAX_COMPREHENSION_LENGTH:
                raise IterableTooLong('Too many loops (in for block)')

            self._assign(node.target, self._FinalValue(value=item))
            try:
                self._exec(node.body)
            except _Break:
                break
            except _Continue:
                continue
        else:
            self._exec(node.orelse)

    def _exec_while(self, node):
        while self._eval(node.test):
            self._max_count += 1
            if self._max_count > MAX_COMPREHENSION_LENGTH:
                raise IterableTooLong('Too many loops (in while block)')

            try:
                self._exec(node.body)
            except _Break:
                break
            except _Continue:
                continue
        else:
            self._exec(node.orelse)

    def _exec_break(self, node):
        raise _Break

    def _exec_continue(self, node):
        raise _Continue

    def _exec_return(self, node):
        raise _Return(self._eval(node.value))


# exceptions used to propogate loop-breaking signals
class _Return(BaseException):
    def __init__(self, retval):
        self.value = retval


class _Break(BaseException):
    pass


class _Continue(BaseException):
    pass
