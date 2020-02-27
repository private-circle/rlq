from rlq.expr.base import BaseExpr


class Year(BaseExpr):
    def __init__(self, year_spec):
        if year_spec == 'curr':
            self.year = 0
        elif year_spec == 'prev':
            self.year = -1
        elif year_spec == 'prev_prev':
            self.year = -2
        else:
            self.year = year_spec

    def evaluate(self, fact_or_set_or_list, evaluator):
        return evaluator.get_year(self.year)

    def evaluate_display(self, evaluator, show='label'):
        raise NotImplementedError('Cannot use {} in a header'.format(type(self).__name__))

    def __repr__(self):
        return 'Year({})'.format(self.year)


Y = Year
