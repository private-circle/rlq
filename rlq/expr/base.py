import abc
from typing import Set

from rlq.expr import _op

DEBUG = True


class BaseExpr(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def evaluate(self, fact_or_set_or_list, model):
        raise NotImplementedError

    @abc.abstractmethod
    def evaluate_display(self, model, show='label') -> str:
        raise NotImplementedError

    def evaluate_aggregate(self, fact_set_list, model):
        if self.is_aggregate:
            return self.evaluate(fact_set_list, model)
        elif DEBUG and len(fact_set_list) > 0:
            values = set(self.evaluate(fact_set_list, model))
            assert len(values) == 1
            return next(iter(values))
        else:
            first_fact_set = next(iter(fact_set_list), None)
            return self.evaluate(first_fact_set, model)

    @property
    def concept_names(self) -> Set[str]:
        return set()

    @property
    def has_dimension_property(self) -> bool:
        return False

    @property
    def is_aggregate(self) -> bool:
        return False

    # Arithmetic operators

    def __add__(self, other):
        return BinaryExpr(_op.add, self, other)

    def __radd__(self, other):
        return BinaryExpr(_op.add, other, self)

    def __sub__(self, other):
        return BinaryExpr(_op.sub, self, other)

    def __rsub__(self, other):
        return BinaryExpr(_op.sub, other, self)

    def __mul__(self, other):
        return BinaryExpr(_op.mul, self, other)

    def __rmul__(self, other):
        return BinaryExpr(_op.mul, other, self)

    def __truediv__(self, other):
        return BinaryExpr(_op.truediv, self, other)

    def __rtruediv__(self, other):
        return BinaryExpr(_op.truediv, other, self)

    def __pow__(self, other):
        return BinaryExpr(_op.pow, self, other)

    def __rpow__(self, other):
        return BinaryExpr(_op.pow, other, self)

    def __mod__(self, other):
        return BinaryExpr(_op.mod, self, other)

    def __rmod__(self, other):
        return BinaryExpr(_op.mod, other, self)

    # Boolean operators

    BOOL_OPS = frozenset(['eq', 'ne', 'gt', 'ge', 'lt', 'le', 'regex', 'iregex',
                          'contains', 'icontains', 'in_', 'nin'])

    def __eq__(self, other):
        return BinaryExpr(_op.eq, self, other)

    def __ne__(self, other):
        return BinaryExpr(_op.ne, self, other)

    def __gt__(self, other):
        return BinaryExpr(_op.gt, self, other)

    def __ge__(self, other):
        return BinaryExpr(_op.ge, self, other)

    def __lt__(self, other):
        return BinaryExpr(_op.lt, self, other)

    def __le__(self, other):
        return BinaryExpr(_op.le, self, other)

    def regex(self, other):
        return BinaryExpr(_op.regex, self, other)

    def iregex(self, other):
        return BinaryExpr(_op.iregex, self, other)

    def contains(self, other):
        return BinaryExpr(_op.contains, self, other)

    def icontains(self, other):
        return BinaryExpr(_op.icontains, self, other)

    def in_(self, other):
        return BinaryExpr(_op.in_, self, other)

    def nin(self, other):
        return BinaryExpr(_op.nin, self, other)

    def __bool__(self):
        raise TypeError('An object of type {0} should never be used in a bool context since all '
                        'its comparison operators have been overloaded to return {0} objects. '
                        'To compare two {0} objects compare their string representations instead '
                        'with repr().'.format(BaseExpr.__name__))


class Literal(BaseExpr):
    def __init__(self, value):
        self.value = value

    def evaluate(self, fact_or_set_or_list, model):
        return self.value

    def evaluate_display(self, model, show='label'):
        return str(self.value)

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.value)


class Constant(BaseExpr):
    def __init__(self, value: str):
        self.value = value

    def evaluate(self, fact_or_set_or_list, model):
        return self

    def evaluate_display(self, model, show='label'):
        return self.value.upper()

    def __repr__(self):
        return self.value.upper()


class BinaryExpr(BaseExpr):
    def __init__(self, operator, operand1, operand2):
        self.operator = operator
        self.operand1 = self.ensure_expr(operand1)
        self.operand2 = self.ensure_expr(operand2)
        from rlq.expr.distinct import Distinct
        if isinstance(self.operand1, Distinct) or isinstance(self.operand2, Distinct):
            raise ValueError('Cannot combine Distinct with other expressions')

    @staticmethod
    def ensure_expr(other):
        if not isinstance(other, BaseExpr):
            return Literal(other)
        return other

    @property
    def concept_names(self):
        concept_names1 = self.operand1.concept_names
        concept_names2 = self.operand2.concept_names
        return concept_names1 | concept_names2

    @property
    def has_dimension_property(self):
        return self.operand1.has_dimension_property or self.operand2.has_dimension_property

    @property
    def is_aggregate(self):
        return self.operand1.is_aggregate or self.operand2.is_aggregate

    @property
    def opname(self):
        return self.operator.__name__

    @property
    def missing_operand_value(self):
        return False if self.opname in self.BOOL_OPS else None

    def evaluate(self, fact_or_set_or_list, model):
        if not self.is_aggregate and isinstance(fact_or_set_or_list, list):
            return [self.evaluate(fs, model) for fs in fact_or_set_or_list]
        value1 = self.operand1.evaluate(fact_or_set_or_list, model)
        if value1 is None:
            return self.missing_operand_value
        value2 = self.operand2.evaluate(fact_or_set_or_list, model)
        if value2 is None:
            return self.missing_operand_value
        return self.operator(value1, value2)

    def evaluate_display(self, model, show='label'):
        return '({} {} {})'.format(self.operand1.evaluate_display(model, show=show),
                                   '$' + self.opname.upper(),
                                   self.operand2.evaluate_display(model, show=show))

    def __repr__(self):
        return '{}({}, {}, {})'.format(type(self).__name__, self.opname, self.operand1, self.operand2)


E = BinaryExpr
