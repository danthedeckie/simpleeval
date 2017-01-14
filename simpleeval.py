'''
SimpleEval - (C) 2013-2016 Daniel Fairhead
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
Contributors:
- corro (Robin Baumgartner) (py3k)
- dratchkov (David R) (nested dicts)
- marky1991 (Mark Young) (slicing)
- T045T (Nils Berg) (!=, py3kstr, obj.attributes)
- perkinslr (Logan Perkins) (.__globals__ or .func_ breakouts)

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

    s.functions["get_file"] = get_file
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
import sys
import operator as op
from random import random

########################################
# Module wide 'globals'

MAX_STRING_LENGTH = 100000
MAX_POWER = 4000000  # highest exponent
DISALLOW_PREFIXES = ['_', 'func_']

PYTHON3 = sys.version_info[0] == 3

########################################
# Exceptions:


class InvalidExpression(Exception):
    ''' Generic Exception '''
    pass


class FunctionNotDefined(InvalidExpression):
    ''' sorry! That function isn't defined! '''
    def __init__(self, func_name, expression):
        self.message = "Function '{0}' not defined," \
                       " for expression '{1}'.".format(func_name, expression)
        self.func_name = func_name
        self.expression = expression

        # pylint: disable=bad-super-call
        super(InvalidExpression, self).__init__(self.message)


class NameNotDefined(InvalidExpression):
    ''' a name isn't defined. '''
    def __init__(self, name, expression):
        self.message = "'{0}' is not defined for expression '{1}'".format(
            name, expression)
        self.name = name
        self.expression = expression

        # pylint: disable=bad-super-call
        super(InvalidExpression, self).__init__(self.message)


class AttributeDoesNotExist(InvalidExpression):
    '''attribute does not exist'''
    def __init__(self, attr, expression):
        self.message = \
            "Attribute '{0}' does not exist in expression '{1}'".format(
                attr, expression)
        self.attr = attr
        self.expression = expression


class FeatureNotAvailable(InvalidExpression):
    ''' What you're trying to do is not allowed. '''
    pass


class NumberTooHigh(InvalidExpression):
    ''' Sorry! That number is too high. I don't want to spend the
        next 10 years evaluating this expression! '''
    pass


class StringTooLong(InvalidExpression):
    ''' That string is **way** too long, baby. '''
    pass


########################################
# Default simple functions to include:


def random_int(top):
    ''' return a random int below <top> '''
    return int(random() * top)


def safe_power(a, b):  # pylint: disable=invalid-name
    ''' a limited exponent/to-the-power-of function, for safety reasons '''
    if abs(a) > MAX_POWER or abs(b) > MAX_POWER:
        raise NumberTooHigh("Sorry! I don't want to evaluate {0} ** {1}"
                            .format(a, b))
    return a ** b


def safe_mult(a, b):  # pylint: disable=invalid-name
    ''' limit the number of times a string can be repeated... '''
    if isinstance(a, str) or isinstance(b, str):
        if isinstance(a, int) and a*len(b) > MAX_STRING_LENGTH:
            raise StringTooLong("Sorry, a string that long is not allowed")
        elif isinstance(b, int) and b*len(a) > MAX_STRING_LENGTH:
            raise StringTooLong("Sorry, a string that long is not allowed")

    return a * b


def safe_add(a, b):  # pylint: disable=invalid-name
    ''' string length limit again '''
    if isinstance(a, str) and isinstance(b, str):
        if len(a) + len(b) > MAX_STRING_LENGTH:
            raise StringTooLong("Sorry, adding those two strings would"
                                " make a too long string.")
    return a + b


########################################
# Defaults for the evaluator:

DEFAULT_OPERATORS = {ast.Add: safe_add, ast.Sub: op.sub, ast.Mult: safe_mult,
                     ast.Div: op.truediv, ast.Pow: safe_power, ast.Mod: op.mod,
                     ast.Eq: op.eq, ast.NotEq: op.ne,
                     ast.Gt: op.gt, ast.Lt: op.lt,
                     ast.GtE: op.ge, ast.LtE: op.le, ast.USub: op.neg,
                     ast.UAdd: op.pos}

DEFAULT_FUNCTIONS = {"rand": random, "randint": random_int,
                     "int": int, "float": float,
                     "str": str if PYTHON3 else unicode}

DEFAULT_NAMES = {"True": True, "False": False}

########################################
# And the actual evaluator:


class SimpleEval(object):  # pylint: disable=too-few-public-methods
    ''' A very simple expression parser.
        >>> s = SimpleEval()
        >>> s.eval("20 + 30 - ( 10 * 5)")
        0
        '''
    expr = ""

    def __init__(self, operators=None, functions=None, names=None):
        '''
            Create the evaluator instance.  Set up valid operators (+,-, etc)
            functions (add, random, get_val, whatever) and names. '''

        if not operators:
            operators = DEFAULT_OPERATORS
        if not functions:
            functions = DEFAULT_FUNCTIONS
        if not names:
            names = DEFAULT_NAMES

        self.operators = operators
        self.functions = functions
        self.names = names

    def eval(self, expr):
        ''' evaluate an expresssion, using the operators, functions and
            names previously set up. '''

        # set a copy of the expression aside, so we can give nice errors...

        self.expr = expr

        # and evaluate:
        return self._eval(ast.parse(expr.strip()).body[0].value)

    # pylint: disable=too-many-return-statements, too-many-branches
    def _eval(self, node):
        ''' The internal evaluator used on each node in the parsed tree. '''

        # literals:

        if isinstance(node, ast.Num):  # <number>
            return node.n
        elif isinstance(node, ast.Str):  # <string>
            if len(node.s) > MAX_STRING_LENGTH:
                raise StringTooLong("String Literal in statement is too long!"
                                    " ({0}, when {1} is max)".format(
                                        len(node.s), MAX_STRING_LENGTH))
            return node.s

        # python 3 compatibility:

        elif (hasattr(ast, 'NameConstant') and
              isinstance(node, ast.NameConstant)):  # <bool>
            return node.value

        # operators, functions, etc:

        elif isinstance(node, ast.UnaryOp):  # - and + etc.
            return self.operators[type(node.op)](self._eval(node.operand))
        elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
            return self.operators[type(node.op)](self._eval(node.left),
                                                 self._eval(node.right))
        elif isinstance(node, ast.BoolOp):  # and & or...
            if isinstance(node.op, ast.And):
                for value in node.values:
                    vout = self._eval(value)
                    if not vout:
                        return False
                return vout
            elif isinstance(node.op, ast.Or):
                for value in node.values:
                    vout = self._eval(value)
                    if vout:
                        return vout
                return False

        elif isinstance(node, ast.Compare):  # 1 < 2, a == b...
            left = self._eval(node.left)
            for operation, comp in zip(node.ops, node.comparators):
                right = self._eval(comp)
                if self.operators[type(operation)](left, right):
                    left = right  # Hi Dr. Seuss...
                else:
                    return False
            return True

        elif isinstance(node, ast.IfExp):  # x if y else z
            return self._eval(node.body) if self._eval(node.test) \
                                         else self._eval(node.orelse)
        elif isinstance(node, ast.Call):  # function...
            try:
                if isinstance(node.func, ast.Name):
                    return self.functions[node.func.id](
                        *(self._eval(a) for a in node.args),
                        **{k.arg: self._eval(k.value) for k in node.keywords}
                    )
                elif isinstance(node.func, ast.Attribute):
                    return self._eval(node.func)(*(self._eval(a)
                                                   for a in node.args))
            except KeyError:
                raise FunctionNotDefined(node.func.id, self.expr)

        # variables/names:

        elif isinstance(node, ast.Name):  # a, b, c...
            try:
                # This happens at least for slicing
                # This is a safe thing to do because it is impossible
                # that there is a true exression assigning to none
                # (the compiler rejects it, so you can't even pass that
                # to ast.parse)
                if node.id == "None":
                    return None
                elif isinstance(self.names, dict):
                    return self.names[node.id]
                elif callable(self.names):
                    return self.names(node)
                else:
                    raise InvalidExpression(
                        'Trying to use name (variable) "{0}"'
                        ' when no "names" defined for'
                        ' evaluator'.format(node.id))

            except KeyError:
                raise NameNotDefined(node.id, self.expr)

        elif isinstance(node, ast.Subscript):  # b[1]
            return self._eval(node.value)[self._eval(node.slice)]

        elif isinstance(node, ast.Attribute):  # a.b.c
            for prefix in DISALLOW_PREFIXES:
                if node.attr.startswith(prefix):
                    raise FeatureNotAvailable(
                        "Sorry, access to __attributes "
                        " or func_ attributes is not available. "
                        "({0})".format(node.attr))

            try:
                return self._eval(node.value)[node.attr]
            except (KeyError, TypeError):
                pass

            # Maybe the base object is an actual object, not just a dict
            try:
                return getattr(self._eval(node.value), node.attr)
            except (AttributeError, TypeError):
                pass

            # If it is neither, raise an exception
            raise AttributeDoesNotExist(node.attr, self.expr)

        elif isinstance(node, ast.Index):
            return self._eval(node.value)
        elif isinstance(node, ast.Slice):
            lower = upper = step = None
            if node.lower is not None:
                lower = self._eval(node.lower)
            if node.upper is not None:
                upper = self._eval(node.upper)
            if node.step is not None:
                step = self._eval(node.step)
            return slice(lower, upper, step)
        else:
            raise FeatureNotAvailable("Sorry, {0} is not available in this "
                                      "evaluator".format(type(node).__name__))


def simple_eval(expr, operators=None, functions=None, names=None):
    ''' Simply evaluate an expresssion '''
    s = SimpleEval(operators=operators,
                   functions=functions,
                   names=names)
    return s.eval(expr)
