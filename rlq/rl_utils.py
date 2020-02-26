import fractions
import os
from typing import Union

from arelle import PackageManager
from arelle.Cntlr import Cntlr
from arelle.ModelDtsObject import ModelConcept
from arelle.ModelInstanceObject import ModelFact, ModelContext
from arelle.ModelManager import ModelManager
from arelle.ModelValue import dateTime
from arelle.ValidateXbrlCalcs import roundValue
from arelle.ValidateXbrlDimensions import loadDimensionDefaults


def convert_to_fy(dt):
    if dt.day == 1 and dt.month == 1:
        return dt.year - 1
    else:
        return dt.year


def parsed_value(fact: ModelFact):
    if fact is None:
        return None
    concept = fact.concept  # type: ModelConcept
    if concept is None or concept.isTuple or fact.isNil:
        return None
    if concept.isFraction:
        num, den = map(fractions.Fraction, fact.fractionValue)
        return num / den
    val = fact.value.strip()
    if concept.isInteger:
        return int(val)
    elif concept.isNumeric:
        dec = fact.decimals
        if dec is None or dec == "INF":  # show using decimals or reported format
            dec = len(val.partition(".")[2])
        else:  # max decimals at 28
            dec = max(min(int(dec), 28), -28)  # 2.7 wants short int, 3.2 takes regular int, don't use _INT here
        num = roundValue(val, fact.precision, dec)  # round using reported decimals
        return num
    elif concept.baseXbrliType == 'dateItemType':
        return dateTime(val)
    elif concept.baseXbrliType == 'booleanItemType':
        return val.lower() in ('1', 'true')
    elif concept.isTextBlock:
        return ' '.join(val.split())
    return val


def context_hash(fact_or_context: Union[ModelContext, ModelFact]):
    context = fact_or_context.context if isinstance(fact_or_context, ModelFact) else fact_or_context
    if context is None:
        return hash(None)
    return hash((context.entityIdentifierHash, context.dimsHash, context.endDatetime))


def save_taxonomy_config(taxonomies_dir, controller=None):
    if controller is None:
        controller = Cntlr(logFileName='logToStdErr')
    PackageManager.init(controller)
    for taxonomy_zip in os.listdir(taxonomies_dir):
        taxonomy_zip_path = os.path.join(taxonomies_dir, taxonomy_zip)
        PackageManager.addPackage(controller, taxonomy_zip_path)
    PackageManager.save(controller)


def load_xbrl_model(file_path, taxonomies_dir=None):
    controller = Cntlr(logFileName='logToStdErr')
    if taxonomies_dir is not None:
        save_taxonomy_config(taxonomies_dir, controller)
    else:
        PackageManager.init(controller)
    model_manager = ModelManager(controller)
    xbrl_model = model_manager.load(file_path)
    loadDimensionDefaults(xbrl_model)
    return xbrl_model
