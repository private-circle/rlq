import abc


class ExprEvaluator(abc.ABC):
    @abc.abstractmethod
    def get_facts(self, concept_name=None):
        pass

    @abc.abstractmethod
    def get_year(self, year):
        pass

    @abc.abstractmethod
    def get_concept(self, fact, name):
        pass

    @abc.abstractmethod
    def get_concept_name(self, fact, name):
        pass

    @abc.abstractmethod
    def get_concept_label(self, fact, name, label_role):
        pass

    @abc.abstractmethod
    def get_concept_value(self, fact, default):
        pass

    @abc.abstractmethod
    def get_dim_member(self, fact, axis_name, include_defaults):
        pass

    @abc.abstractmethod
    def get_dim_member_name(self, fact, axis_name, include_defaults):
        pass

    @abc.abstractmethod
    def get_dim_member_label(self, fact, axis_name, include_defaults, label_role):
        pass

    @abc.abstractmethod
    def get_dim_member_value(self, fact, axis_name, include_defaults, label_role):
        pass

    @abc.abstractmethod
    def get_dim_axes(self, fact):
        pass

    @abc.abstractmethod
    def get_period(self, fact, forever_dt):
        pass

    @abc.abstractmethod
    def get_period_str(self, fact, instant_format, duration_format, forever_format):
        pass

    @abc.abstractmethod
    def get_start_datetime(self, fact):
        pass

    @abc.abstractmethod
    def get_end_datetime(self, fact):
        pass

    @abc.abstractmethod
    def get_end_date(self, fact):
        pass

    @abc.abstractmethod
    def get_fy(self, fact):
        pass

    @abc.abstractmethod
    def get_context_id(self, fact):
        pass

    @abc.abstractmethod
    def get_context_hash_no_period_type(self, fact):
        pass
