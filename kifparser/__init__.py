"""
This package provides a SUO-KIF ontology files parser.

Possible usage:
>>> from kifparser import KIFParser
>>> p = KIFParser()
>>> largest = None
>>> #  io should be a file-like object open for reading
>>> for obj in p.parse(io):
>>>     if largest is None:
>>>         largest = obj
>>>         continue
>>>     if obj.end - obj.start > largest.end - largest.start:
>>>         largest = obj
>>> conc = largest.eval_conc()
>>> print(conc)

In the example above `obj' is a constituent object extracted by the
parser, and `conc' is the concept evaluated from this constituent.
"""
from .kifparser import KIFParser, KIFAgenda
from .ontology import KIFOntology
from .grammar import KIFGrammar

__all__ = ('KIFParser', 'KIFOntology', 'KIFGrammar', 'KIFAgenda')
__version__ = '0.0.0'
