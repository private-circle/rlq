import abc

from rlq.expr.base import BaseExpr, DEBUG
from rlq.expr.year import YearExpr
from rlq.fact_set import FactSet


class Property(BaseExpr, metaclass=abc.ABCMeta):
    def evaluate(self, fact_or_set_or_list, model):
        if isinstance(fact_or_set_or_list, list):
            return [self.evaluate(fs, model) for fs in fact_or_set_or_list]
        elif isinstance(fact_or_set_or_list, FactSet):
            return self.evaluate_set(fact_or_set_or_list, model)
        else:
            return self.evaluate_fact(fact_or_set_or_list, model)

    def evaluate_fact(self, fact, model):
        return model.get_property(fact, self)

    def evaluate_set(self, fact_set, model):
        if DEBUG and len(fact_set) > 0:
            values = {model.get_property(f, self) for f in fact_set}
            assert len(values) == 1
            return next(iter(values))
        else:
            first_fact = next(iter(fact_set), None)
            return model.get_property(first_fact, self)

    def __repr__(self):
        prop_type = type(self).__name__
        attrs = []
        for attr, value in self.__dict__.items():
            attrs.append('{}={}'.format(attr, value))
        return '{}({})'.format(prop_type, ', '.join(attrs))


class ConceptProperty(Property):
    def __init__(self, name: str=None):
        self.name = name

    @property
    def concept_names(self):
        if self.name is not None:
            return {self.name}
        return set()

    def evaluate_set(self, fact_set, model):
        if self.name is None:
            raise NotImplementedError('Cannot evaluate_set for {} with no name'.format(type(self).__name__))
        fact = fact_set.by_concept(model).get(self.name)
        return model.get_property(fact, self)

    def evaluate_display(self, model, show='label'):
        if show == 'label':
            concept_label = model.get_property(None, ConceptLabel(self.name))
            return concept_label if concept_label is not None else self.name
        elif show == 'name':
            return self.name
        else:
            return repr(self)

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.name)


class Concept(ConceptProperty):
    pass


class ConceptName(ConceptProperty):
    pass


class ConceptLabel(ConceptProperty):
    def __init__(self, name, preferred_label=None):
        super(ConceptLabel, self).__init__(name)
        self.preferred_label = preferred_label


class ConceptValue(ConceptProperty):
    def __init__(self, name, default=None):
        super(ConceptValue, self).__init__(name)
        self.default = default

    def evaluate_fact(self, fact, model):
        value = super(ConceptValue, self).evaluate_fact(fact, model)
        if value is None:
            return self.default
        return value

    def evaluate_set(self, fact_set, model):
        value = super(ConceptValue, self).evaluate_set(fact_set, model)
        if value is None:
            return self.default
        return value


CN = ConceptName
CL = ConceptLabel
C = ConceptValue


class ContextProperty(Property, metaclass=abc.ABCMeta):
    pass


class DimProperty(ContextProperty, metaclass=abc.ABCMeta):
    @property
    def has_dimension_property(self):
        return True


class DimValProperty(DimProperty):
    def __init__(self, axis_name=None, include_defaults=True):
        self.axis_name = axis_name
        self.include_defaults = include_defaults

    def evaluate_display(self, model, show='label'):
        if show == 'label':
            axis_label = model.get_property(None, ConceptLabel(self.axis_name))
            return axis_label.replace(' [Axis]', '') if axis_label is not None else axis_label
        elif show == 'name':
            return self.axis_name
        else:
            return repr(self)

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.axis_name)


class DimMember(DimValProperty):
    pass


class DimMemberName(DimValProperty):
    pass


class DimMemberLabel(DimValProperty):
    def __init__(self, axis_name, include_defaults=True, preferred_label=None):
        super(DimMemberLabel, self).__init__(axis_name, include_defaults)
        self.preferred_label = preferred_label


class DimMemberValue(DimValProperty):
    def __init__(self, axis_name, include_defaults=True, preferred_label=None):
        super(DimMemberValue, self).__init__(axis_name, include_defaults)
        self.preferred_label = preferred_label


DN = DimMemberName
DL = DimMemberLabel
D = DimMemberValue


class SingletonProperty(Property, metaclass=abc.ABCMeta):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SingletonProperty, cls).__new__(cls)
        return cls._instance


class DimAxes(DimProperty, SingletonProperty):
    def evaluate_display(self, model, show='label'):
        return 'Dimensions'

    def __repr__(self):
        return '{}()'.format(type(self).__name__)


Ax = DimAxes


class Period(ContextProperty):
    def __init__(self, forever_dt=None):
        self.forever_dt = forever_dt

    def evaluate_display(self, model, show='label'):
        return 'Period'


class PeriodStr(ContextProperty):
    def __init__(self, instant_format='{:%d/%m/%Y}', duration_format='{0:%d/%m/%Y} to {1:%d/%m/%Y}', forever_format=''):
        self.instant_format = instant_format
        self.duration_format = duration_format
        self.forever_format = forever_format

    def evaluate_display(self, model, show='label'):
        return 'Period'


class Date(ContextProperty):
    def evaluate_display(self, model, show='label'):
        return 'Instant / Period End Date'


class FY(ContextProperty):
    CURR = YearExpr('curr')
    PREV = YearExpr('prev')
    PREV_PREV = YearExpr('prev_prev')

    def evaluate_display(self, model, show='label'):
        return 'FY'


class ContextRef(ContextProperty, SingletonProperty):
    def evaluate_display(self, model, show='label'):
        return 'Context ID'


CtxID = ContextRef


class ContextHashNoPeriodType(ContextProperty, SingletonProperty):
    def evaluate_display(self, model, show='label'):
        return 'Context hash w/o period type'


CtxHash = ContextHashNoPeriodType
