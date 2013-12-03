simpleeval (Simple Eval)
========================

(C) 2013 Daniel Fairhead

A quick single file library for easily adding evaluatable expressions into python
projects.  Say you want to allow a user to set an alarm volume, which could depend
on the time of day, alarm level, how many previous alarms had gone off, and if there
is music playing at the time.

Or if you want to allow simple formulae in a web application, but don't want to
give full eval() access, or don't want to run in javascript on the client side.

Basic Usage
-----------

To get very simple evaluating ::

    from simpleeval import simple_eval

    simple_eval("21 + 21")

returns `42`.

Expressions can be as complex and convoluted as you want: ::

    simple_eval("21 + 19 / 7 + (8 % 3) ** 9")

returns `535.714285714`.

You can add your own functions in as well. ::

    simple_eval("square(11)", functions={"square": lambda x: x*x})

returns `121`.

For more details of working with functions, read further down.

Note:
~~~~~
all further examples use `>>>` to designate python, as if you are using the python interactive
prompt.

Operators
---------
You can add operators yourself, using the `operators` argument, but these are the defaults:

 +----+-------------------------------+
 | +  | add two things. `x + y`       |
 |    | `1 + 1` -> `2`
 +----+-------------------------------+
 | -  | subtract two things `x - y`   |
 |    | `100 - 1` -> `99`             |
 +----+-------------------------------+
 | /  | divide one thing by another   |
 |    | `x / y`                       |
 |    | `100/10` -> `10`              |
 +----+-------------------------------+
 | *  | multiple one thing by another |
 |    | `x * y`                       |
 |    | `10 * 10` -> `100`            |
 +----+-------------------------------+
 | ** | 'to the power of' `x**y`      |
 |    | `2 ** 10` -> `1024`           |
 +----+-------------------------------+
 | %  | modulus. (remainder)  `x % y` |
 |    | `15 % 4` -> `3`               |
 +----+-------------------------------+

If Expressions
--------------

You can use python style `if x then y else z` type expressions: ::

    >>> simple_eval("'equal' if x == y else 'not equal'",
                    constants={"x": 1, "y": 2})
    'not equal'

which, of course, can be nested: ::

    >>> simple_eval("'a' if 1 == 2 else 'b' if 2 == 3 else 'c'")
    'c'
    

Functions
---------

You can define functions which you'd like the expresssions to have access to: ::

    >>> simple_eval("double(21)", functions={"double": lambda x:x*2})
    42

You can define "real" functions to pass in rather than lambdas, of course too, and even re-name them so that expressions can be shorter ::

    >>> def double(x):
            return x * 2
    >>> simple_eval("d(100) + double(1)", functions={"d": double, "double":double})
    202

Names
-----
 
Sometimes it's useful to have variables available, which in python terminology are called 'names'. ::

    >>> simple_eval("a + b", names={"a": 11, "b": 100})
    111

You can also hand the handling of names over to a function, if you prefer: ::

    >>> def name_handler(node):
            return ord(node.id[0].lower(a))-96

    >>> simple_eval('a + b', names=name_handler)
    3

That was a bit of a silly example, but you could use this for pulling values from a database or file, say, or doing some kind of caching system.

Constants
---------

You can also use 'constants', which are replaced before evaluation.  This can be useful for bringing your own 'style' into expressions, or making things feel a bit less programmy for non-techy end users

Creating an Evaluator Class
---------------------------

Rather than creating a new evaluator each time, if you are doing a lot of evaluations,
you can create a SimpleEval object, and pass it expressions each time (which should be a bit quicker, and certainly more convienient for some use cases): ::

    s = SimpleEval()
    s.eval("1 + 1")
    # and so on...

You can assign / edit the various options of the `SimpleEval` object if you want to.
Eithe assign them during creation (like the `simple_eval` function) ::

    s = SimpleEval(functions={"boo": boo})

or edit them after creation: ::

    s.constants['fortytwo'] = 42

this actually means you can modify names (or functions) with functions, if you really feel so inclined: ::

    s = SimpleEval()
    def set_val(name, value):
        s.names[name.value] = value.value
        return value.value

    s.functions = {'set':set_val}

    s.eval("set('age', 111)")

Say.  This would allow a certain level of 'scriptyness' if you had these evaluations happening as callbacks in a program.  Although you really are reaching the end of what this library is intended for at this stage.
