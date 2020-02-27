import abc

from rlq.evaluators.base import ExprEvaluator
from rlq.expr.base import BaseExpr, DEBUG
from rlq.expr.year import Year
from rlq.fact_set import FactSet


class Property(BaseExpr, metaclass=abc.ABCMeta):
    def evaluate(self, fact_or_set_or_list, evaluator):
        if isinstance(fact_or_set_or_list, list):
            return [self.evaluate(fs, evaluator) for fs in fact_or_set_or_list]
        elif isinstance(fact_or_set_or_list, FactSet):
            return self.evaluate_set(fact_or_set_or_list, evaluator)
        else:
            return self.evaluate_fact(fact_or_set_or_list, evaluator)

    @abc.abstractmethod
    def evaluate_fact(self, fact, evaluator: ExprEvaluator):
        pass

    def evaluate_set(self, fact_set, evaluator):
        if DEBUG and len(fact_set) > 0:
            values = {self.evaluate_fact(f, evaluator) for f in fact_set}
            assert len(values) == 1
            return next(iter(values))
        else:
            first_fact = next(iter(fact_set), None)
            return self.evaluate_fact(first_fact, evaluator)

    def __repr__(self):
        prop_type = type(self).__name__
        attrs = []
        for attr, value in self.__dict__.items():
            attrs.append('{}={}'.format(attr, value))
        return '{}({})'.format(prop_type, ', '.join(attrs))


class ConceptProperty(Property, metaclass=abc.ABCMeta):
    def __init__(self, name: str=None, label_role=None):
        self.name = name
        self.label_role = label_role

    @property
    def concept_names(self):
        if self.name is not None:
            return {self.name}
        return set()

    def evaluate_set(self, fact_set, evaluator):
        if self.name is None:
            raise NotImplementedError('Cannot evaluate_set for {} with no name'.format(type(self).__name__))
        fact = fact_set.by_concept(evaluator).get(self.name)
        return self.evaluate_fact(fact, evaluator)

    def evaluate_display(self, evaluator, show='label'):
        if show == 'label':
            concept_label = evaluator.get_concept_label(None, self.name, self.label_role)
            return concept_label if concept_label is not None else self.name
        elif show == 'name':
            return self.name
        else:
            return repr(self)

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.name)


class Concept(ConceptProperty):
    def evaluate_fact(self, fact, evaluator):
        return evaluator.get_concept(fact, self.name)


class ConceptName(ConceptProperty):
    def evaluate_fact(self, fact, evaluator):
        return evaluator.get_concept_name(fact, self.name)


class ConceptLabel(ConceptProperty):
    def evaluate_fact(self, fact, evaluator):
        return evaluator.get_concept_label(fact, self.name, self.label_role)


class ConceptValue(ConceptProperty):
    def __init__(self, name, default=None, label_role=None):
        super(ConceptValue, self).__init__(name, label_role)
        self.default = default

    def evaluate_fact(self, fact, evaluator):
        return evaluator.get_concept_value(fact, self.default)


CN = ConceptName
CL = ConceptLabel
C = ConceptValue


class ContextProperty(Property, metaclass=abc.ABCMeta):
    pass


class DimProperty(ContextProperty, metaclass=abc.ABCMeta):
    @property
    def has_dimension_property(self):
        return True


class DimValProperty(DimProperty, metaclass=abc.ABCMeta):
    def __init__(self, axis_name=None, include_defaults=True, label_role=None):
        self.axis_name = axis_name
        self.include_defaults = include_defaults
        self.label_role = label_role

    def evaluate_display(self, evaluator, show='label'):
        if show == 'label':
            return evaluator.get_concept_label(None, self.axis_name, self.label_role)
        elif show == 'name':
            return self.axis_name
        else:
            return repr(self)

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.axis_name)


class DimMember(DimValProperty):
    def evaluate_fact(self, fact, evaluator):
        return evaluator.get_dim_member(fact, self.axis_name, self.include_defaults)


class DimMemberName(DimValProperty):
    def evaluate_fact(self, fact, evaluator):
        return evaluator.get_dim_member_name(fact, self.axis_name, self.include_defaults)


class DimMemberLabel(DimValProperty):
    def evaluate_fact(self, fact, evaluator):
        return evaluator.get_dim_member_label(fact, self.axis_name, self.include_defaults, self.label_role)


class DimMemberValue(DimValProperty):
    def evaluate_fact(self, fact, evaluator):
        return evaluator.get_dim_member_value(fact, self.axis_name, self.include_defaults, self.label_role)


DN = DimMemberName
DL = DimMemberLabel
D = DimMemberValue


class DimAxes(DimProperty):
    def evaluate_fact(self, fact, evaluator):
        return evaluator.get_dim_axes(fact)

    def evaluate_display(self, evaluator, show='label'):
        return 'Dimensions'

    def __repr__(self):
        return '{}()'.format(type(self).__name__)


Ax = DimAxes


class PeriodProperty(ContextProperty, metaclass=abc.ABCMeta):
    pass


class Period(PeriodProperty):
    def __init__(self, forever_dt=None):
        self.forever_dt = forever_dt

    def evaluate_fact(self, fact, evaluator):
        return evaluator.get_period(fact, self.forever_dt)

    def evaluate_display(self, evaluator, show='label'):
        return 'Period'


class PeriodStr(PeriodProperty):
    def __init__(self, instant_format='{:%d/%m/%Y}', duration_format='{0:%d/%m/%Y} to {1:%d/%m/%Y}',
                 forever_format=''):
        self.instant_format = instant_format
        self.duration_format = duration_format
        self.forever_format = forever_format

    def evaluate_fact(self, fact, evaluator):
        return evaluator.get_period_str(fact, self.instant_format, self.duration_format, self.forever_format)

    def evaluate_display(self, evaluator, show='label'):
        return 'Period'


class StartDatetime(PeriodProperty):
    def evaluate_fact(self, fact, evaluator):
        return evaluator.get_start_datetime(fact)

    def evaluate_display(self, evaluator, show='label'):
        return 'Start Datetime'


class EndDatetime(PeriodProperty):
    def evaluate_fact(self, fact, evaluator):
        return evaluator.get_end_datetime(fact)

    def evaluate_display(self, evaluator, show='label'):
        return 'End Datetime'


class EndDate(PeriodProperty):
    def evaluate_fact(self, fact, evaluator):
        return evaluator.get_end_date(fact)

    def evaluate_display(self, evaluator, show='label'):
        return 'End Datetime'


class FY(PeriodProperty):
    CURR = Year('curr')
    PREV = Year('prev')
    PREV_PREV = Year('prev_prev')

    def evaluate_fact(self, fact, evaluator):
        return evaluator.get_fy(fact)

    def evaluate_display(self, evaluator, show='label'):
        return 'FY'


class ContextID(ContextProperty):
    def evaluate_fact(self, fact, evaluator):
        return evaluator.get_context_id(fact)

    def evaluate_display(self, evaluator, show='label'):
        return 'Context ID'


CtxID = ContextID


class ContextHashNoPeriodType(ContextProperty):
    def evaluate_fact(self, fact, evaluator):
        return evaluator.get_context_hash_no_period_type(fact)

    def evaluate_display(self, evaluator, show='label'):
        return 'Context hash w/o period type'


CtxHash = ContextHashNoPeriodType
