from rlq.expr.base import BaseExpr


class Distinct(BaseExpr):
    def __init__(self, expr: BaseExpr, *exprs: BaseExpr, ignore_none=False):
        self.exprs = (expr,) + exprs
        self.ignore_none = ignore_none

    @property
    def concept_names(self):
        concept_names = set()
        for expr in self.exprs:
            concept_names |= expr.concept_names
        return concept_names

    @property
    def has_dimension_property(self):
        return any(expr.has_dimension_property for expr in self.exprs)

    def evaluate(self, fact_or_set_or_list, model):
        assert isinstance(fact_or_set_or_list, list)
        if len(self.exprs) == 1:
            values = [self.exprs[0].evaluate(fs, model) for fs in fact_or_set_or_list]
        else:
            values = [tuple(e.evaluate(fs, model) for e in self.exprs) for fs in fact_or_set_or_list]
        if self.ignore_none:
            values = [v for v in values if all(i is None for i in v)]
        if not values:
            return []
        return list(set(values))

    def evaluate_display(self, model, show='label'):
        return '{}({})'.format(
            type(self).__name__.upper(),
            ', '.join(e.evaluate_display(model, show=show) for e in self.exprs))

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, ', '.join(repr(e) for e in self.exprs))
