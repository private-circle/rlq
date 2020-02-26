import collections
import warnings
from typing import Union

from arelle.ModelDtsObject import ModelConcept
from arelle.ModelInstanceObject import ModelFact, ModelContext, ModelDimensionValue
from arelle.ModelValue import qname, QName
from arelle.ModelXbrl import ModelXbrl

from rlq.expr import properties as props
from rlq.fact_set import FactSet
from rlq.rl_utils import parsed_value


def convert_to_fy(dt):
    if dt.day == 1 and dt.month == 1:
        return dt.year - 1
    else:
        return dt.year


def context_hash(fact_or_context: Union[ModelContext, ModelFact]):
    context = fact_or_context.context if isinstance(fact_or_context, ModelFact) else fact_or_context
    if context is None:
        return hash(None)
    return hash((context.entityIdentifierHash, context.dimsHash, context.endDatetime))


class QueryExecutor(object):
    def __init__(self, xbrl_model: ModelXbrl):
        self.xbrl_model = xbrl_model

    def qn(self, name):
        try:
            namespaces = self._namespaces
        except AttributeError:
            namespaces = self._namespaces = self.xbrl_model.prefixedNamespaces
        return qname(name, namespaces)

    @property
    def financial_years(self):
        try:
            return self._fys
        except AttributeError:
            fys = set()
            for context in self.xbrl_model.contexts.values():  # type: ModelContext
                dt = context.endDatetime
                if dt:
                    fys.add(convert_to_fy(dt))
            self._fys = sorted(fys, reverse=True)
            return self._fys

    def financial_year(self, fy: int):
        if fy <= 0:
            return self.financial_years[-fy]
        else:
            return fy

    def facts_by_concept_name(self, concept_name):
        return self.xbrl_model.factsByQname[self.qn(concept_name)]

    def get_property(self, obj: Union[ModelFact, ModelConcept, ModelContext, None], prop: props.Property):
        fact, concept, context = self._get_fact_concept_context(obj, prop)
        if isinstance(prop, props.ConceptProperty):
            return self._get_concept_property(fact, concept, prop)
        elif isinstance(prop, props.ContextProperty):
            return self._get_context_propery(context, prop)
        else:
            raise ValueError('Invalid property type {}'.format(type(prop).__name__))

    def _get_fact_concept_context(self, obj: Union[ModelFact, ModelConcept, ModelContext, None], prop: props.Property):
        if isinstance(obj, ModelFact):
            fact = obj  # type: ModelFact
            concept = fact.concept  # type: ModelConcept
            context = fact.context  # type: ModelContext
        elif isinstance(obj, ModelContext):
            if not isinstance(prop, props.ContextProperty):
                raise ValueError('Cannot get property {} for {}'.format(prop, obj))
            context = obj
            fact = concept = None
        elif isinstance(obj, ModelConcept):
            if not isinstance(obj, props.ConceptProperty):
                raise ValueError('Cannot get property {} for {}'.format(prop, obj))
            concept = obj
            fact = context = None
        else:
            fact = context = concept = None
            if isinstance(prop, props.ConceptProperty) and prop.name is not None:
                concept = self.xbrl_model.qnameConcepts.get(self.qn(prop.name))  # type: ModelConcept
            elif isinstance(prop, props.ContextProperty) and isinstance(obj, str):
                context = self.xbrl_model.contexts[obj]  # type: ModelContext
        return fact, concept, context

    def _get_concept_property(self, fact: ModelFact, concept: ModelConcept, prop: props.ConceptProperty):
        if concept is None:
            return None
        assert prop.name is None or prop.name == str(concept.qname)
        if isinstance(prop, props.ConceptValue):
            return parsed_value(fact)
        if isinstance(prop, props.Concept):
            return concept
        elif isinstance(prop, props.ConceptName):
            return str(concept.qname)
        elif isinstance(prop, props.ConceptLabel):
            return concept.label(prop.preferred_label, strip=True)

    def _get_context_propery(self, context: ModelContext, prop: props.ContextProperty):
        if context is None:
            return None
        if isinstance(prop, props.Period):
            if context.isInstantPeriod:
                return context.instantDatetime
            elif context.isStartEndPeriod:
                return context.startDatetime, context.endDatetime
            else:
                return prop.forever_dt
        elif isinstance(prop, props.PeriodStr):
            if context.isInstantPeriod:
                return prop.instant_format.format(context.instantDatetime)
            elif context.isStartEndPeriod:
                return prop.duration_format.format(context.startDatetime, context.endDatetime)
            else:
                return prop.forever_format
        elif isinstance(prop, props.Date):
            return context.endDatetime
        elif isinstance(prop, props.FY):
            return convert_to_fy(context.endDatetime) if context.endDatetime is not None else None
        elif isinstance(prop, props.ContextRef):
            return context.id
        elif isinstance(prop, props.ContextHashNoPeriodType):
            return context_hash(context)
        elif isinstance(prop, props.DimAxes):
            return frozenset(str(dqn) for dqn in context.qnameDims.keys())
        elif isinstance(prop, props.DimValProperty):
            return self._get_dim_val_property(context, prop)

    def _get_dim_val_property(self, context: ModelContext, prop: props.DimValProperty):
        dim_qname = self.qn(prop.axis_name)
        try:
            dim_value = context.qnameDims[dim_qname]  # type: ModelDimensionValue
        except KeyError:
            if prop.include_defaults:
                try:
                    member_qname = self.xbrl_model.qnameDimensionDefaults[dim_qname]  # type: QName
                except KeyError:
                    return None
                else:
                    if isinstance(prop, (props.DimMemberName, props.DimMemberValue)):
                        return str(member_qname)
                    elif isinstance(prop, props.DimMemberLabel):
                        member = self.xbrl_model.qnameConcepts[member_qname]
                        return member.label(prop.preferred_label, strip=True)
            else:
                return None
        else:
            if dim_value.isExplicit:
                if isinstance(prop, (props.DimMemberName, props.DimMemberValue)):
                    return str(dim_value.memberQname)
                elif isinstance(prop, props.DimMemberLabel):
                    return dim_value.member.label(prop.preferred_label, strip=True)
            else:
                if isinstance(prop, props.DimMemberName):
                    return None
                elif isinstance(prop, (props.DimMemberValue, props.DimMemberLabel)):
                    return dim_value.typedMember.textValue.strip()

    def get(self, concept):
        query_spec = {
            'select': [props.ConceptValue(concept)],
            'where': [props.FY() == props.FY.CURR],
            'output_format': 'row_wise'
        }
        data = self.query(query_spec)
        assert len(data) == 1
        return data[0][0]

    def query(self, query_spec):
        header_exprs, select_exprs = self._get_select_exprs(query_spec)
        where_exprs = self._get_where_exprs(query_spec)
        ctx_groupby_exprs = list(query_spec.get('context_groupby', [props.ContextRef()]))
        groupby_exprs = list(query_spec.get('groupby', []))
        having_exprs = list(query_spec.get('having', []))

        # Identify all concept names mentioned in the query
        all_exprs = select_exprs + where_exprs + ctx_groupby_exprs + groupby_exprs + having_exprs
        concept_names = set()
        for expr in all_exprs:
            concept_names |= expr.concept_names

        facts = self._get_facts(concept_names)
        fact_sets = self._get_fact_sets(facts, ctx_groupby_exprs, where_exprs)

        is_agg_query = any(e.is_aggregate for e in select_exprs)
        if is_agg_query:
            fact_set_lists = self._get_fact_set_lists(fact_sets, groupby_exprs, having_exprs)
            # Generate output columns
            column_values = []
            for select_expr in select_exprs:
                column = [select_expr.evaluate_aggregate(fsl, self) for fsl in fact_set_lists]
                column_values.append(column)
        else:
            # Generate output columns
            column_values = []
            for select_expr in select_exprs:
                column = select_expr.evaluate(fact_sets, self)
                column_values.append(column)

        # Create output
        header_display = query_spec.get('header_display', 'label')
        output_format = query_spec.get('output_format', 'row_wise_dicts')
        return self._format_output(column_values, header_exprs, header_display, output_format)

    def _get_select_exprs(self, query_spec):
        select = query_spec['select']
        if isinstance(select, collections.Mapping):
            header_exprs, select_exprs = map(list, zip(*select.items()))
        else:
            headers = list(query_spec.get('headers', []))
            header_exprs = []
            select_exprs = []
            for i, expr_spec in enumerate(select):
                try:
                    header_expr, select_expr = expr_spec
                except TypeError:
                    select_expr = expr_spec
                    try:
                        header_expr = headers[i]
                    except IndexError:
                        header_expr = None
                    if header_expr is None:
                        header_expr = select_expr
                select_exprs.append(select_expr)
                header_exprs.append(header_expr)
        return header_exprs, select_exprs

    def _get_where_exprs(self, query_spec):
        # Add default DimAxes() expr if no dimension property is present in where
        where_exprs = list(query_spec.get('where', []))
        has_dimension_property = False
        for expr in where_exprs:
            if expr.has_dimension_property:
                has_dimension_property = True
                break
        if not has_dimension_property:
            where_exprs.append(props.DimAxes() == set())
        return where_exprs

    def _get_facts(self, concept_names):
        # Extract facts of all the mentioned concepts
        if not concept_names:
            warnings.warn('No concepts specified in query')
            facts = self.xbrl_model.factsInInstance
        else:
            facts = set()
            for concept_name in concept_names:
                facts |= self.facts_by_concept_name(concept_name)
        return facts

    def _get_fact_sets(self, facts, ctx_groupby_exprs, where_exprs):
        # Group facts into fact sets
        fact_sets = collections.defaultdict(FactSet)
        for fact in facts:
            group_key = tuple(e.evaluate(fact, self) for e in ctx_groupby_exprs)
            fact_sets[group_key].add(fact)
        fact_sets = list(fact_sets.values())

        # Apply all filters on the fact sets
        filtered_fact_sets = [fs for fs in fact_sets if all(e.evaluate(fs, self) for e in where_exprs)]
        return filtered_fact_sets

    def _get_fact_set_lists(self, fact_sets, groupby_exprs, having_exprs):
        # Evaluate groupby clause
        grouped_fact_sets = collections.defaultdict(list)
        for fact_set in fact_sets:
            group_key = tuple(e.evaluate(fact_set, self) for e in groupby_exprs)
            grouped_fact_sets[group_key].append(fact_set)
        grouped_fact_sets = list(grouped_fact_sets.values())

        # Evaluate having clause
        filtered_fact_set_lists = [fsl for fsl in grouped_fact_sets if
                                   all(e.evaluate_aggregate(fsl, self) for e in having_exprs)]

        return filtered_fact_set_lists

    def _format_output(self, column_values, header_exprs, header_display, output_format):
        header_values = [e.evaluate_display(self, show=header_display)
                         if not isinstance(e, str) else e for e in header_exprs]
        if 'row_wise' in output_format:
            transposed = zip(*column_values)
            output = []
            for row_values in transposed:
                if any(v is not None for v in row_values):
                    if 'dict' in output_format:
                        output.append(dict(zip(header_values, row_values)))
                    elif 'header' in output_format:
                        output.append((header_values, row_values))
                    else:
                        output.append(row_values)
            return output
        elif 'column_wise' in output_format:
            if 'dict' in output_format:
                return {h: col for h, col in zip(header_values, column_values)}
            elif 'header' in output_format:
                return header_values, column_values
            else:
                return column_values
