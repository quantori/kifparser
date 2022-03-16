"""This module contains unit tests for kifparser module."""

import unittest
from kifparser import KIFParser, KIFGrammar
from io import StringIO


class TestKIFParser(unittest.TestCase):
    """This test suite checks the KIFParser class functionality."""

    def test_basic_parsing(self):
        """Checks create_or_get method."""
        p = KIFParser()
        largest = None
        for obj in p.parse(StringIO("""
            ;; Just a test
            (=>
                (subclass Human Animal)
                (
                    forall (?X)
                    (=>
                        (instance ?X Human)
                        (instance ?X Animal)
                    )
                )
            )
        """)):
            if largest is None:
                largest = obj
                continue
            if obj.end - obj.start > largest.end - largest.start:
                largest = obj
        self.assertIsInstance(largest, KIFGrammar.KIF)
        items = list(largest.get_list_items())
        self.assertEqual(len(items), 4)
        self.assertIsInstance(items[1], KIFGrammar.CommentLine)
        comment = items[1].childvars[0][0]
        self.assertIsInstance(comment, KIFGrammar.Comment)
        comment_text = comment.childvars[0][1]
        self.assertIsInstance(comment_text, KIFGrammar.Text)
        self.assertEqual(comment_text.get_text(), '; Just a test')
        self.assertIsInstance(items[2], KIFGrammar.Assertion)
