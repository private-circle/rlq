from rlq.expr.base import BaseExpr


class YearExpr(BaseExpr):
    def __init__(self, fy):
        if fy == 'curr':
            self.fy = 0
        elif fy == 'prev':
            self.fy = -1
        elif fy == 'prev_prev':
            self.fy = -2
        else:
            self.fy = fy

    def evaluate(self, fact_or_set_or_list, model):
        return model.financial_year(self.fy)

    def evaluate_display(self, model, show='label'):
        raise NotImplementedError('Cannot use {} in a header'.format(type(self).__name__))

    def __repr__(self):
        return 'Year({})'.format(self.fy)


Y = YearExpr
