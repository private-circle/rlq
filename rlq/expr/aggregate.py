import abc

from rlq.expr.base import BaseExpr


class Aggregate(BaseExpr, metaclass=abc.ABCMeta):
    def __init__(self, expr: BaseExpr, ignore_none=True, empty=None):
        assert not expr.is_aggregate, 'Cannot create aggregate of an aggregate'
        self.expr = expr
        self.ignore_none = ignore_none
        self.empty = empty

    @property
    def concept_names(self):
        return self.expr.concept_names

    @property
    def has_dimension_property(self):
        return self.expr.has_dimension_property

    @property
    def is_aggregate(self):
        return True

    def evaluate(self, fact_or_set_or_list, model):
        assert isinstance(fact_or_set_or_list, list)
        values = self.expr.evaluate(fact_or_set_or_list, model)
        if self.ignore_none:
            values = [v for v in values if v is not None]
        if not values:
            return self.empty
        return self.aggregate(values)

    def evaluate_display(self, model, show='label'):
        return '{}({})'.format(type(self).__name__.upper(),
                               self.expr.evaluate_display(model, show=show))

    @abc.abstractmethod
    def aggregate(self, values):
        raise NotImplementedError

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.expr)


class First(Aggregate):
    def aggregate(self, values):
        return values[0]


class Last(Aggregate):
    def aggregate(self, values):
        return values[-1]


class Count(Aggregate):
    def aggregate(self, values):
        return len(values)


class Min(Aggregate):
    def aggregate(self, values):
        return min(values)


class Max(Aggregate):
    def aggregate(self, values):
        return max(values)


class Sum(Aggregate):
    def __init__(self, expr, start=0, ignore_none=True, empty=None):
        super(Sum, self).__init__(expr, ignore_none, empty)
        self.start = start

    def aggregate(self, values):
        return sum(values, self.start)


class Avg(Sum):
    def aggregate(self, values):
        return sum(values, self.start) / len(values)


class Join(Aggregate):
    def __init__(self, expr, sep=', ', ignore_none=True, empty=None):
        super(Join, self).__init__(expr, ignore_none, empty)
        self.sep = sep

    def aggregate(self, values):
        return self.sep.join(values)
