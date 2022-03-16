"""
This module provides a SUO-KIF ontology files parser.

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

from typing import TextIO, Generator
import tqdm

from aiire import Agenda
from .grammar import KIFGrammar


class KIFAgenda(Agenda):
    """KIFAgenda is AIIRE Agenda for KIF parser with KIF grammar."""

    def __init__(self):
        """Create KIF agenda."""
        super().__init__(KIFGrammar())


class KIFParser(object):
    """KIFParser is the main parser class for SUO-KIF."""

    def parse(
        self, io: TextIO
    ) -> Generator[KIFGrammar.Constituent, None, None]:
        """
        Parse an IO (file-like object).

        Draws a progress bar while parsing.

        @param io: a file-like object to parse
        @yield: all possible constituents parser could recognize
        """
        agenda = KIFAgenda()
        pos = 0
        for line in tqdm.tqdm(io):
            for char in line:
                yield from agenda.put(KIFGrammar.Atom(pos, pos + 1, char))
                pos += 1
