import collections
from datetime import timedelta
from typing import Optional

from arelle.ModelDtsObject import ModelConcept
from arelle.ModelInstanceObject import ModelDimensionValue, ModelContext
from arelle.ModelValue import qname, QName
from arelle.ModelXbrl import ModelXbrl

from rlq.evaluators.base import ExprEvaluator
from rlq.rl_utils import parsed_value, load_xbrl_model


def get_end_date(context: ModelContext):
    return (context.endDatetime - timedelta(days=1)).date() if context.endDatetime is not None else None


def get_fy(context: ModelContext):
    end_date = get_end_date(context)
    return end_date.year if end_date is not None else None


def get_context_hash_no_period_type(context: ModelContext):
    return hash((context.entityIdentifierHash, context.dimsHash, context.endDatetime))


class RLExprEvaluator(ExprEvaluator):
    @classmethod
    def load(cls, file_path):
        model = load_xbrl_model(file_path)
        return cls(model)

    def __init__(self, arelle_model: ModelXbrl):
        self.model = arelle_model

    def get_facts(self, concept_name=None):
        if concept_name is not None:
            return self.model.factsByQname[self.qn(concept_name)]
        return self.model.factsInInstance

    @property
    def all_years(self):
        try:
            return self._fys
        except AttributeError:
            fys = set()
            for context in self.model.contexts.values():  # type: ModelContext
                fy = get_fy(context)
                if fy is not None:
                    fys.add(fy)
            self._fys = sorted(fys, reverse=True)
            return self._fys

    def get_year(self, year: int):
        if year <= 0:
            return self.all_years[-year]
        else:
            return year

    def qn(self, name):
        if isinstance(name, QName):
            return name
        # if the name is a clark notation string
        if name[0] == '{':
            return qname(name)
        # else if the name contains a namespace prefix
        elif ':' in name:
            try:
                namespaces = self._namespaces
            except AttributeError:
                namespaces = self._namespaces = self.model.prefixedNamespaces
            return qname(name, namespaces)
        # else it is a local name
        else:
            try:
                local_name_to_qname = self._local_name_to_qname
            except AttributeError:
                local_name_to_qname = self._local_name_to_qname = collections.defaultdict(list)
                for qn_ in self.model.qnameConcepts:  # type: QName
                    local_name_to_qname[qn_.localName].append(qn_)
            qnames = local_name_to_qname[name]
            if len(qnames) > 1:
                raise ValueError('Multiple QNames for local name {}: {}'.format(name, qnames))
            return qnames[0]

    def get_concept(self, fact, name) -> ModelConcept:
        if fact is not None:
            return fact.concept
        elif name is not None:
            return self.model.qnameConcepts.get(self.qn(name))
        else:
            raise ValueError('Both fact and name cannot be None')

    def get_concept_name(self, fact, name) -> str:
        concept = self.get_concept(fact, name)
        return str(concept.qname) if concept is not None else None

    def get_concept_label(self, fact, name, label_role=None) -> str:
        concept = self.get_concept(fact, name)
        return concept.label(label_role, strip=True) if concept is not None else None

    def get_fact_value(self, fact, default):
        value = parsed_value(fact)
        return value if value is not None else default

    get_concept_value = get_fact_value

    def get_provided_dim_value(self, fact, axis_name) -> Optional[ModelDimensionValue]:
        if fact is None or fact.context is None:
            return None
        context = fact.context  # type: ModelContext
        return context.qnameDims.get(self.qn(axis_name))

    def get_dim_member(self, fact, axis_name, include_defaults=True):
        dim_value = self.get_provided_dim_value(fact, axis_name)
        if dim_value is not None:
            return dim_value.member if dim_value.isExplicit else dim_value.typedMember
        elif include_defaults:
            member_qn = self.model.qnameDimensionDefaults.get(self.qn(axis_name))
            if member_qn is not None:
                return self.model.qnameConcepts[member_qn]
        return None

    def get_dim_member_name(self, fact, axis_name, include_defaults=True):
        dim_value = self.get_provided_dim_value(fact, axis_name)
        if dim_value is not None:
            return str(dim_value.member.qname) if dim_value.isExplicit else None
        elif include_defaults:
            member_qn = self.model.qnameDimensionDefaults.get(self.qn(axis_name))
            if member_qn is not None:
                return str(member_qn)
        return None

    def get_dim_member_label(self, fact, axis_name, include_defaults=True, label_role=None):
        dim_value = self.get_provided_dim_value(fact, axis_name)
        if dim_value is not None:
            return (dim_value.member.label(label_role, strip=True) if dim_value.isExplicit
                    else dim_value.typedMember.textValue.strip())
        elif include_defaults:
            member_qn = self.model.qnameDimensionDefaults.get(self.qn(axis_name))
            if member_qn is not None:
                member = self.model.qnameConcepts[member_qn]
                return member.label(label_role, strip=True)
        return None

    def get_dim_member_value(self, fact, axis_name, include_defaults=True, label_role=None):
        dim_value = self.get_provided_dim_value(fact, axis_name)
        if dim_value is not None:
            return (str(dim_value.member.qname) if dim_value.isExplicit
                    else dim_value.typedMember.textValue.strip())
        elif include_defaults:
            member_qn = self.model.qnameDimensionDefaults.get(self.qn(axis_name))
            if member_qn is not None:
                return str(member_qn)
        return None

    def get_dim_axes(self, fact):
        if fact is None or fact.context is None:
            return None
        return frozenset(str(qn) for qn in fact.context.qnameDims)

    def get_period(self, fact, forever_dt=None):
        if fact is None or fact.context is None:
            return None
        context = fact.context  # type: ModelContext
        if context.isStartEndPeriod:
            return context.startDatetime, context.endDatetime
        elif context.isInstantPeriod:
            return context.instantDatetime
        else:
            return forever_dt

    def get_period_str(self, fact, instant_format, duration_format, forever_format) -> str:
        if fact is None or fact.context is None:
            return ''
        context = fact.context  # type: ModelContext
        if context.isStartEndPeriod:
            return duration_format.format(context.startDatetime, context.endDatetime)
        elif context.isInstantPeriod:
            return instant_format.format(context.instantDatetime)
        else:
            return forever_format

    def get_start_datetime(self, fact):
        if fact is None or fact.context is None:
            return None
        return fact.context.startDatetime

    def get_end_datetime(self, fact):
        if fact is None or fact.context is None:
            return None
        return fact.context.endDatetime

    def get_end_date(self, fact):
        if fact is None or fact.context is None:
            return None
        return get_end_date(fact.context)

    def get_fy(self, fact):
        if fact is None or fact.context is None:
            return None
        return get_fy(fact.context)

    def get_context_id(self, fact):
        return fact.contextID

    def get_context_hash_no_period_type(self, fact):
        if fact is None or fact.context is None:
            return hash(None)
        return get_context_hash_no_period_type(fact.context)
