simpleeval (Simple Eval)
========================

.. image:: https://travis-ci.org/danthedeckie/simpleeval.svg?branch=master
   :target: https://travis-ci.org/danthedeckie/simpleeval
   :alt: Build Status

.. image:: https://coveralls.io/repos/github/danthedeckie/simpleeval/badge.svg?branch=master
   :target: https://coveralls.io/r/danthedeckie/simpleeval?branch=master
   :alt: Coverage Status

.. image:: https://badge.fury.io/py/simpleeval.svg
   :target: https://badge.fury.io/py/simpleeval
   :alt: PyPI Version

A quick single file library for easily adding evaluatable expressions into
python projects.  Say you want to allow a user to set an alarm volume, which
could depend on the time of day, alarm level, how many previous alarms had gone
off, and if there is music playing at the time.

Or if you want to allow simple formulae in a web application, but don't want to
give full eval() access, or don't want to run in javascript on the client side.

It's deliberately very simple, pull it in from PyPI (pip or easy_install), or
even just a single file you can dump into a project.

Internally, it's using the amazing python ``ast`` module to parse the
expression, which allows very fine control of what is and isn't allowed.  It
should be completely safe in terms of what operations can be performed by the
expression.

The only issue I know to be aware of is that you can create an expression which
takes a long time to evaluate, or which evaluating requires an awful lot of
memory, which leaves the potential for DOS attacks.  There is basic protection
against this, and you can lock it down further if you desire. (see the
Operators_ section below)

You should be aware of this when deploying in a public setting.

The defaults are pretty locked down and basic, and it's very easy to add
whatever extra specific functionality you need (your own functions,
variable/name lookup, etc).

Basic Usage
-----------

To get very simple evaluating:

.. code-block:: python

    from simpleeval import simple_eval

    simple_eval("21 + 21")

returns ``42``.

Expressions can be as complex and convoluted as you want:

.. code-block:: python

    simple_eval("21 + 19 / 7 + (8 % 3) ** 9")

returns ``535.714285714``.

You can add your own functions in as well.

.. code-block:: python

    simple_eval("square(11)", functions={"square": lambda x: x*x})

returns ``121``.

For more details of working with functions, read further down.

Note:
~~~~~
all further examples use ``>>>`` to designate python code, as if you are using
the python interactive prompt.

.. _Operators:

Operators
---------
You can add operators yourself, using the ``operators`` argument, but these are
the defaults:

+--------+------------------------------------+
|  ``+`` | add two things. ``x + y``          |
|        | ``1 + 1`` -> ``2``                 |
+--------+------------------------------------+
|  ``-`` | subtract two things ``x - y``      |
|        | ``100 - 1`` -> ``99``              |
+--------+------------------------------------+
|  ``/`` | divide one thing by another        |
|        | ``x / y``                          |
|        | ``100/10`` -> ``10``               |
+--------+------------------------------------+
|  ``*`` | multiple one thing by another      |
|        | ``x * y``                          |
|        | ``10 * 10`` -> ``100``             |
+--------+------------------------------------+
| ``**`` | 'to the power of' ``x**y``         |
|        | ``2 ** 10`` -> ``1024``            |
+--------+------------------------------------+
| ``%``  | modulus. (remainder)  ``x % y``    |
|        | ``15 % 4`` -> ``3``                |
+--------+------------------------------------+
| ``==`` | equals  ``x == y``                 |
|        | ``15 == 4`` -> ``False``           |
+--------+------------------------------------+
| ``<``  | Less than. ``x < y``               |
|        | ``1 < 4`` -> ``True``              |
+--------+------------------------------------+
| ``>``  | Greater than. ``x > y``            |
|        | ``1 > 4`` -> ``False``             |
+--------+------------------------------------+
| ``<=`` | Less than or Equal to. ``x <= y``  |
|        | ``1 < 4`` -> ``True``              |
+--------+------------------------------------+
| ``>=`` | Greater or Equal to ``x >= 21``    |
|        | ``1 >= 4`` -> ``False``            |
+--------+------------------------------------+
| ``in`` | is something contained within      |
|        | something else.                    |
|        | ``"spam" in "my breakfast"``       |
|        | -> ``False``                       |
+--------+------------------------------------+


The ``^`` operator is notably missing - not because it's hard, but because it
is often mistaken for a exponent operator, not the bitwise operation that it is
in python.  It's trivial to add back in again if you wish (using the class
based evaluator explained below):

.. code-block:: python

    >>> import ast
    >>> import operator

    >>> s = SimpleEval()
    >>> s.operators[ast.BitXor] = operator.xor

    >>> s.eval("2 ^ 10")
    8

Limited Power
~~~~~~~~~~~~~

Also note, the ``**`` operator has been locked down by default to have a
maximum input value of ``4000000``, which makes it somewhat harder to make
expressions which go on for ever.  You can change this limit by changing the
``simpleeval.POWER_MAX`` module level value to whatever is an appropriate value
for you (and the hardware that you're running on) or if you want to completely
remove all limitations, you can set the ``s.operators[ast.Pow] = operator.pow``
or make your own function.

On my computer, ``9**9**5`` evaluates almost instantly, but ``9**9**6`` takes
over 30 seconds.  Since ``9**7`` is ``4782969``, and so over the ``POWER_MAX``
limit, it throws a ``NumberTooHigh`` exception for you. (Otherwise it would go
on for hours, or until the computer runs out of memory)

Strings (and other Iterables) Safety
~~~~~~~~~~~~~

There are also limits on string length (100000 characters,
``MAX_STRING_LENGTH``).  This can be changed if you wish.

Related to this, if you try to create a silly long string/bytes/list, by doing
``'i want to break free'.split() * 9999999999`` for instance, it will block you.

If Expressions
--------------

You can use python style ``if x then y else z`` type expressions:

.. code-block:: python

    >>> simple_eval("'equal' if x == y else 'not equal'",
                    names={"x": 1, "y": 2})
    'not equal'

which, of course, can be nested:

.. code-block:: python

    >>> simple_eval("'a' if 1 == 2 else 'b' if 2 == 3 else 'c'")
    'c'


Functions
---------

You can define functions which you'd like the expresssions to have access to:

.. code-block:: python

    >>> simple_eval("double(21)", functions={"double": lambda x:x*2})
    42

You can define "real" functions to pass in rather than lambdas, of course too,
and even re-name them so that expressions can be shorter

.. code-block:: python

    >>> def double(x):
            return x * 2
    >>> simple_eval("d(100) + double(1)", functions={"d": double, "double":double})
    202

If you don't provide your own ``functions`` dict, then the the following defaults
are provided in the ``DEFAULT_FUNCTIONS`` dict:

+----------------+--------------------------------------------------+
| ``randint(x)`` | Return a random ``int`` below ``x``              |
+----------------+--------------------------------------------------+
| ``rand()``     | Return a random ``float`` between 0 and 1        |
+----------------+--------------------------------------------------+
| ``int(x)``     | Convert ``x`` to an ``int``.                     |
+----------------+--------------------------------------------------+
| ``float(x)``   | Convert ``x`` to a ``float``.                    |
+----------------+--------------------------------------------------+
| ``str(x)``     | Convert ``x`` to a ``str`` (``unicode`` in py2)  |
+----------------+--------------------------------------------------+

If you want to provide a list of functions, but want to keep these as well,
then you can do a normal python ``.copy()`` & ``.update``:

.. code-block:: python

    >>> my_functions = simpleeval.DEFAULT_FUNCTIONS.copy()
    >>> my_functions.update(
            square=(lambda x:x*x),
            double=(lambda x:x+x),
        )
    >>> simple_eval('square(randint(100))', functions=my_functions)

Names
-----

Sometimes it's useful to have variables available, which in python terminology
are called 'names'.

.. code-block:: python

    >>> simple_eval("a + b", names={"a": 11, "b": 100})
    111

You can also hand the handling of names over to a function, if you prefer:


.. code-block:: python

    >>> def name_handler(node):
            return ord(node.id[0].lower(a))-96

    >>> simple_eval('a + b', names=name_handler)
    3

That was a bit of a silly example, but you could use this for pulling values
from a database or file, say, or doing some kind of caching system.

The two default names that are provided are ``True`` and ``False``.  So if you want to provide your own names, but want ``True`` and ``False`` to keep working, either provide them yourself, or ``.copy()`` and ``.update`` the ``DEFAULT_NAMES``. (See functions example above).

Creating an Evaluator Class
---------------------------

Rather than creating a new evaluator each time, if you are doing a lot of
evaluations, you can create a SimpleEval object, and pass it expressions each
time (which should be a bit quicker, and certainly more convenient for some use
cases):

.. code-block:: python

    >>> s = SimpleEval()

    >>> s.eval("1 + 1")
    2

    >>> s.eval('100 * 10')
    1000

    # and so on...

You can assign / edit the various options of the ``SimpleEval`` object if you
want to.  Either assign them during creation (like the ``simple_eval``
function)

.. code-block:: python

    def boo():
        return 'Boo!'

    s = SimpleEval(functions={"boo": boo})

or edit them after creation:

.. code-block:: python

    s.names['fortytwo'] = 42

this actually means you can modify names (or functions) with functions, if you
really feel so inclined:

.. code-block:: python

    s = SimpleEval()
    def set_val(name, value):
        s.names[name.value] = value.value
        return value.value

    s.functions = {'set': set_val}

    s.eval("set('age', 111)")

Say.  This would allow a certain level of 'scriptyness' if you had these
evaluations happening as callbacks in a program.  Although you really are
reaching the end of what this library is intended for at this stage.

Compound Types
--------------

Compound types (``dict``, ``tuple``, ``list``, ``set``) in general just work if
you pass them in as named objects.  If you want to allow creation of these, the
``EvalWithCompoundTypes`` class works.  Just replace any use of ``SimpleEval`` with
that.

The ``EvalWithCompoundTypes`` class also contains support for simple comprehensions.
eg: ``[x + 1 for x in [1,2,3]]``.  There's a safety `MAX_COMPREHENSION_LENGTH` to control
how many items it'll allow before bailing too.  This also takes into account nested
comprehensions.

Extending
---------

The ``SimpleEval`` class is pretty easy to extend.  For instance, to create a
version that disallows method invocation on objects:

.. code-block:: python

    import ast
    import simpleeval

    class EvalNoMethods(simpleeval.SimpleEval):
        def _eval_call(self, node):
            if isinstance(node.func, ast.Attribute):
                raise simpleeval.FeatureNotAvailable("No methods please, we're British")
            return super(EvalNoMethods, self)._eval_call(node)

and then use ``EvalNoMethods`` instead of the ``SimpleEval`` class.

Other...
--------

The library supports both python 2 and 3.

Object attributes that start with ``_`` or ``func_`` are disallowed by default.
If you really need that (BE CAREFUL!), then modify the module global
``simpleeval.DISALLOW_PREFIXES``.

The initial idea came from J.F. Sebastian on Stack Overflow
( http://stackoverflow.com/a/9558001/1973500 ) with modifications and many improvements,
see the head of the main file for contributors list.

Please read the ``test_simpleeval.py`` file for other potential gotchas or
details.  I'm very happy to accept pull requests, suggestions, or other issues.
Enjoy!

Developing
----------

Run tests::

    $ make test

Or to set the tests running on every file change:

    $ make autotest

(requires ``entr``) 
