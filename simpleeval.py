'''
SimpleEval - (C) 2013 Daniel Fairhead
-------------------------------------

An short, easy to use, safe and reasonably extensible expression evaluator.
Designed for things like in a website where you want to allow the user to
generate a string, or a number from some other input, without allowing full
eval() or other unsafe or needlessly complex linguistics.

-------------------------------------

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

-------------------------------------

Initial idea copied from J.F. Sebastian on Stack Overflow
( http://stackoverflow.com/a/9558001/1973500 ) with
modifications and many improvments.

-------------------------------------
Usage:

>>> s = SimpleEval()
>>> s.eval("20 + 30")
50

You can add your own functions easily too:

if file.txt contents is "11"

>>> def get_file():
        with open("file.txt",'r') as f:
            return f.read()
    s.functions.append("get_file", get_file)
    s.eval("int(get_file()) + 31")
42

For more information, see the full package documentation on pypi, or the github
repo.

-----------

If you don't need to re-use the evaluator (with it's names, functions, etc),
then you can use the simple_eval() function:

>>> simple_eval("21 + 19")
40

You can pass names, operators and functions to the simple_eval function as
well:

>>> simple_eval("40 + two", names={"two": 2})
42

'''

import ast
import operator as op
import math
from random import random

########################################
# Exceptions:

class InvalidExpression(Exception):
    ''' Generic Exception '''
    pass

class FunctionNotDefined(InvalidExpression):
    ''' sorry! That function isn't defined! '''
    def __init__(self, func_name, expression):
        self.message = "Function '{0}' not defined," \
                       " for expression '{1}'.".format( func_name, expression)
        self.func_name = func_name
        self.expression = expression

        super(Exception, self).__init__(self.message)

class NameNotDefined(InvalidExpression):
    ''' a name isn't defined. '''
    def __init__(self, name, expression):
        self.message = "'{0}' is not defined for expression '{1}'".format(
                            name, expression)
        self.name = name
        self.expression = expression

        super(Exception, self).__init__(self.message)

class FeatureNotAvailable(Exception):
    ''' What you're trying to do is not allowed. '''
    pass

########################################
# Default simple functions to include:

def random_int(top):
    ''' return a random int below <top> '''
    return int(random() * top)

########################################
# Defaults for the evaluator:

DEFAULT_OPERATORS = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
                     ast.Div: op.truediv, ast.Pow: op.pow, ast.Mod: op.mod,
                     ast.Eq: op.eq, ast.Gt: op.gt, ast.Lt: op.lt}

DEFAULT_CONSTANTS = {"pi": math.pi}

DEFAULT_FUNCTIONS = {"rand": random, "randint": random_int,
                     "int": int, "float": float, "str": unicode}

########################################
# And the actual evaluator:

class SimpleEval(object): # pylint: disable=too-few-public-methods
    ''' A very simple expression parser.
        >>> s = SimpleEval()
        >>> s.eval("20 + 30 - ( 10 * 5)")
        0
        '''

    def __init__(self, operators=None, functions=None, names=None):
        '''
            Create the evaluator instance.  Set up valid operators (+,-, etc)
            functions (add, random, get_val, whatever) and names. '''

        if not operators:
            operators = DEFAULT_OPERATORS
        if not functions:
            functions = DEFAULT_FUNCTIONS

        self.operators = operators
        self.functions = functions
        self.names = names

    def eval(self, expr):
        ''' evaluate an expresssion, using the operators, functions and
            names previously set up. '''

        # set a copy of the expression aside, so we can give nice errors...

        self.expr = expr

        # and evaluate:
        return self._eval(ast.parse(expr).body[0].value)

    def _eval(self, node):
        ''' The internal eval function used on each node in the parsed tree. '''
        if isinstance(node, ast.Num): # <number>
            return node.n
        elif isinstance(node, ast.Str): # <string>
            return node.s

        elif isinstance(node, ast.BinOp): # <left> <operator> <right>
            return self.operators[type(node.op)](self._eval(node.left),
                                       self._eval(node.right))

        elif isinstance(node, ast.BoolOp): # and & or...
            if isinstance(node.op, ast.And):
                return all((self._eval(v) for v in node.values))
            elif isinstance(node.op, ast.Or):
                return any((self._eval(v) for v in node.values))

        elif isinstance(node, ast.Compare): # 1 < 2, a == b...
            return self.operators[type(node.ops[0])](self._eval(node.left),
                                                     self._eval(node.comparators[0]))
        elif isinstance(node, ast.IfExp): # x if y else z
            return self._eval(node.body) if self._eval(node.test) \
                                         else self._eval(node.orelse)

        elif isinstance(node, ast.Call): # function...
            try:
                return self.functions[node.func.id](*(self._eval(a)
                                                      for a in node.args))
            except KeyError:
                raise FunctionNotDefined(node.func.id, self.expr)

        ##########################
        # variables/names:

        elif isinstance(node, ast.Name): # a, b, c...
            try:
                if isinstance(self.names, dict):
                    return self.names[node.id]
                elif callable(self.names):
                    return self.names(node)
                else:
                    raise KeyError('undefined name')
            except KeyError:
                raise NameNotDefined(node.id, self.expr)

        elif isinstance(node, ast.Subscript): # b[1]
            return self._eval(node.value)[self._eval(node.slice.value)]

        else:
            raise FeatureNotAvailable("Sorry, {0} is not available in this "
                                      "evaluator".format(type(node).__name__ ))

def simple_eval(expr, operators=None, functions=None, names=None):
    ''' Simply evaluate an expresssion '''
    s = SimpleEval(operators=operators,
                   functions=functions,
                   names=names)
    return s.eval(expr)

if __name__ == '__main__':
    s = SimpleEval()
    while True:
        expr = raw_input(">")
        try:
            print(s.eval(expr))
        except Exception as e:
            print "oh"
            print dir(e)
            print(e)

