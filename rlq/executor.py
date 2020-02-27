import collections
import warnings

from rlq.evaluators.base import ExprEvaluator
from rlq.expr import properties as p
from rlq.fact_set import FactSet


def _get_select_exprs(query_spec):
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


def _get_where_exprs(query_spec):
    where_exprs = list(query_spec.get('where', []))

    # If there is no dimension related clause in the query,
    # assume that only non-dimensional facts are requested
    # and add a default DimAxes() condition.
    has_dimension_property = False
    for expr in where_exprs:
        if expr.has_dimension_property:
            has_dimension_property = True
            break
    if not has_dimension_property:
        where_exprs.append(p.DimAxes() == set())
    return where_exprs


class QExecutor(object):
    def __init__(self, evaluator: ExprEvaluator):
        self.evaluator = evaluator

    def get(self, concept):
        query_spec = {
            'select': [p.ConceptValue(concept)],
            'where': [p.FY() == p.FY.CURR, p.DimAxes() == set()],
            'output_format': 'row_wise'
        }
        data = self.query(query_spec)
        assert len(data) == 1
        return data[0][0]

    def getall(self, concept):
        query_spec = {
            'select': [p.ConceptValue(concept), p.FY()],
            'where': [p.DimAxes() == set()],
            'output_format': 'row_wise_dicts'
        }
        return self.query(query_spec)

    def query(self, query_spec):
        header_exprs, select_exprs = _get_select_exprs(query_spec)
        where_exprs = _get_where_exprs(query_spec)
        ctx_groupby_exprs = list(query_spec.get('context_groupby', [p.ContextID()]))
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
                column = [select_expr.evaluate_aggregate(fsl, self.evaluator) for fsl in fact_set_lists]
                column_values.append(column)
        else:
            # Generate output columns
            column_values = []
            for select_expr in select_exprs:
                column = select_expr.evaluate(fact_sets, self.evaluator)
                column_values.append(column)

        # Create output
        header_display = query_spec.get('header_display', 'label')
        output_format = query_spec.get('output_format', 'row_wise_dicts')
        return self._format_output(column_values, header_exprs, header_display, output_format)

    def _get_facts(self, concept_names):
        # Extract facts of all the mentioned concepts
        if not concept_names:
            warnings.warn('No concepts specified in query')
            facts = self.evaluator.get_facts()
        else:
            facts = set()
            for concept_name in concept_names:
                facts |= self.evaluator.get_facts(concept_name)
        return facts

    def _get_fact_sets(self, facts, ctx_groupby_exprs, where_exprs):
        # Group facts into fact sets
        fact_sets = collections.defaultdict(FactSet)
        for fact in facts:
            group_key = tuple(e.evaluate(fact, self.evaluator) for e in ctx_groupby_exprs)
            fact_sets[group_key].add(fact)
        fact_sets = list(fact_sets.values())

        # Apply all filters on the fact sets
        filtered_fact_sets = [fs for fs in fact_sets if all(e.evaluate(fs, self.evaluator) for e in where_exprs)]
        return filtered_fact_sets

    def _get_fact_set_lists(self, fact_sets, groupby_exprs, having_exprs):
        # Evaluate groupby clause
        grouped_fact_sets = collections.defaultdict(list)
        for fact_set in fact_sets:
            group_key = tuple(e.evaluate(fact_set, self.evaluator) for e in groupby_exprs)
            grouped_fact_sets[group_key].append(fact_set)
        grouped_fact_sets = list(grouped_fact_sets.values())

        # Evaluate having clause
        filtered_fact_set_lists = [fsl for fsl in grouped_fact_sets if
                                   all(e.evaluate_aggregate(fsl, self.evaluator) for e in having_exprs)]

        return filtered_fact_set_lists

    def _format_output(self, column_values, header_exprs, header_display, output_format):
        header_values = [e.evaluate_display(self.evaluator, show=header_display)
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