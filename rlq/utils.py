from rlq.executor import QExecutor


def get_query_executor(file_path=None):
    """Create an instance of QExecutor to run queries on.

    Based on provided arguments, an ExprEvaluator instance of the appropriate type
    is created for use by the QExecutor.
    """
    if file_path is not None:
        from rlq.evaluators.rl import RLExprEvaluator
        evaluator = RLExprEvaluator.load(file_path)
        return QExecutor(evaluator)
