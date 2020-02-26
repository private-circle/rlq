import operator
import re


# Arithmetic operators

add = operator.add
sub = operator.sub
mul = operator.mul
truediv = operator.truediv
pow = operator.pow
mod = operator.mod


# Boolean operators

eq = operator.eq
ne = operator.ne
gt = operator.gt
ge = operator.ge
lt = operator.lt
le = operator.le


def regex(value1, value2):
    return bool(re.match(value2, value1))


def iregex(value1, value2):
    return bool(re.match(value2, value1, re.I))


def contains(value1, value2):
    return value2 in value1


def icontains(value1, value2):
    return value2.lower() in value1.lower()


def in_(value1, value2):
    return value1 in value2


def nin(value1, value2):
    return value1 not in value2
