"""
This module provides an AIIRE grammar for SUO-KIF language.

Immediate constituent classes, as well as the grammar class itself,
can be subclassed and/or overriden.
"""
from aiire import Grammar
from .ontology import KIFOntology
from typing import Type


class KIFGrammar(Grammar):
    """
    KIFGrammar is an AIIRE grammar for SUO-KIF language.

    This grammar is a combined object-oriented immediate constituent
    grammar for AIIRE NLU core parser.

    Classes of immediate constituents are defined as nested classes
    of this class.
    """

    ontology = KIFOntology()

    class Atom(Grammar.Atom):
        """
        KIFGrammar.Atom is the basic class of KIF language atoms.

        These atoms are characters, their classes being determined
        based on some categories determined in `get_category' method.

        @cvar categories: a mapping between category names and
            corresponding immediate constituent classes (Atom
            subclasses), which is used to get Atom class in
            `get_cls_by_text' method.
        """

        categories = {}  # Filled later for each category-class pair

        def get_cls_by_text(self) -> Type['KIFGrammar.Atom']:
            """
            Get atom class by its text.

            @return: Atom subclass that corresponds to the category
                of the character which is the atom's text.
            """
            if self.text is None:
                return
            # Artoms should be characters
            assert len(self.text) == 1
            return self.categories[self.get_category(self.text)]

        @staticmethod
        def get_category(char: str) -> str:
            """
            Get KIF Atom category for a given character.

            @param char: the character
            @return: category name
            """
            if char == '\n':
                return 'newline'
            if char.isspace():
                return 'space'
            if char == '(':
                return 'lparenthesis'
            if char == ')':
                return 'rparenthesis'
            if(
                char.isalpha() or char.isdigit() or char == '_' or
                char == '.' or char == '-'
            ):
                # FIXME: ualnum is the old name for
                # underscore/alphanumeric, which can be misleading.
                # A new name should be found like ddualnum (dot,
                # dash, underscore, alphanumeric) which will be
                # readable and good for the constituent class
                return 'ualnum'
            if char == ';':
                return 'semicolon'
            if char == '&':
                return 'amp'
            if char == '%':
                return 'percent'
            if char == '?':
                return 'qmark'
            if char == '@':
                return 'atsign'
            if char == '"':
                return 'quot'
            if char in frozenset('<=>'):
                return 'impl'
            return 'unknown'

    class TextStart(Grammar.Constituent):
        """Any combination a text can start with, e.g.: 'SUMO'."""

    class CommentChar(TextStart):
        """A character that can be inside a comment, e.g.: 'a'."""

    class CommentStart(Grammar.Constituent):
        """Any combination that marks the start of a comment: ';'."""

    class Semicolon(Atom, CommentChar, CommentStart):
        """Semiclolon character: ';'."""

    Atom.categories['semicolon'] = Semicolon

    class Text(Grammar.AtomicConstituent, TextStart):
        """
        Arbitrary one-line text, e.g.: 'SUMO ontology is'.

        CNF-style rule: Text -> TextStart CommentChar
        """

        right_only = True

    Text.left = [TextStart]
    Text.right = [CommentChar]

    class Whitespaces(Grammar.AtomicConstituent, Grammar.Constituent):
        r"""Arbitrary sequence of whitespaces, e.g.: '    \n   '."""

    class Whitespace(Whitespaces):
        """Any whitespace character including newline, e.g.: ' '."""

    class WhitespaceComb(Whitespaces):
        """
        Arbitrary combination of whitespaces, e.g.: '  '.

        Single whitespace is a Whitespaces instance, but not
        WhitespaceComb, because it is not a combination.

        CNF-style rule: WhitespaceComb -> Whitespaces Whitespace
        """

    WhitespaceComb.left = [Whitespaces]
    WhitespaceComb.right = [Whitespace]

    class Spaces(Grammar.AtomicConstituent, Grammar.Constituent):
        pass

    class Space(Atom, CommentChar, Whitespace, Whitespaces, Spaces):
        pass

    Atom.categories['space'] = Space

    class SpaceComb(Spaces):
        pass

    SpaceComb.left = [Spaces]
    SpaceComb.right = [Space]

    class LParenthesis(Atom, CommentChar):
        pass

    Atom.categories['lparenthesis'] = LParenthesis

    class RParenthesis(Atom, CommentChar):
        pass

    Atom.categories['rparenthesis'] = RParenthesis

    class Quot(Atom, CommentChar):
        pass

    Atom.categories['quot'] = Quot

    class LiteralStart(Grammar.Constituent):
        pass

    class Predicate(Grammar.Constituent):
        pass

    class QuantorLiteral(Grammar.Constituent):
        pass

    class Arguments(Grammar.Constituent):
        right_only = True

    class SingleArgument(Arguments):
        def eval_conc(self):
            return KIFGrammar.ontology.create_or_get(self.get_text())

    class ArgumentComb(Arguments, Grammar.InlineListConstituent):
        pass

    class NonspacedArguments(Arguments):
        pass

    class NonspacedSingleArgument(NonspacedArguments, SingleArgument):
        pass

    class NonspacedArgumentComb(NonspacedArguments, ArgumentComb):
        pass

    class Literal(LiteralStart, Predicate, NonspacedSingleArgument):
        right_only = False
        literals = {}

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            text = self.get_text()
            if text in self.literals:
                self.__class__ = self.literals[text]

    class UAlNum(Atom, Literal, CommentChar):
        pass

    Atom.categories['ualnum'] = UAlNum

    class ComplexLiteral(
            Literal,
            Grammar.AtomicConstituent,
            Grammar.ListConstituent):
        def eval_conc(self):
            return KIFGrammar.ontology.create_or_get(self.get_text())

    ComplexLiteral.left = [LiteralStart]
    ComplexLiteral.right = [UAlNum]

    class KIFPart(Grammar.Constituent):
        pass

    class KIFItem(KIFPart):
        pass

    class EmptyLine(KIFItem):
        def eval_conc(self):
            return None

    class NewLine(Atom, EmptyLine, Whitespace):
        pass

    Atom.categories['newline'] = NewLine

    class BlankLine(Grammar.AtomicConstituent, EmptyLine):
        pass

    BlankLine.left = [Spaces]
    BlankLine.right = [NewLine]

    class NewLinedText(Grammar.Constituent):
        pass

    NewLinedText.left = [NewLine]
    NewLinedText.right = [Text]

    class MultilineText(Grammar.AtomicConstituent, Grammar.ListConstituent):
        right_only = True

    MultilineText.left = [TextStart, MultilineText]
    MultilineText.right = [NewLinedText]

    class OpenDocText(Grammar.Constituent):
        pass

    OpenDocText.left = [Quot]
    OpenDocText.right = [Text, MultilineText]

    class DocText(NonspacedSingleArgument):
        pass

    DocText.left = [OpenDocText]
    DocText.right = [Quot]

    class Comment(Grammar.AtomicConstituent, Grammar.ListConstituent):
        pass

    class CommentLine(EmptyLine, Grammar.AtomicConstituent):
        pass

    class SpacedCommentStart(CommentStart):
        pass

    SpacedCommentStart.left = [Spaces]
    SpacedCommentStart.right = [Semicolon]

    Comment.left = [CommentStart]
    Comment.right = [TextStart]

    CommentLine.left = [Comment]
    CommentLine.right = [NewLine]

    class Unknown(Atom, CommentChar):
        pass

    Atom.categories['unknown'] = Unknown

    class SpacedArguments(Grammar.RightIdentityConstituent, Arguments):
        right_only = True

    class SpacedSingleArgument(SpacedArguments, SingleArgument):
        pass

    class SpacedArgumentComb(SpacedArguments, ArgumentComb):
        pass

    NonspacedArgumentComb.left = [NonspacedArguments]
    NonspacedArgumentComb.right = [SpacedSingleArgument]

    SpacedSingleArgument.left = [Whitespaces]
    SpacedSingleArgument.right = [NonspacedSingleArgument]

    SpacedArgumentComb.left = [Whitespaces]
    SpacedArgumentComb.right = [NonspacedArgumentComb]

    class RightSpacedArguments(Grammar.LeftConc, SpacedArguments):
        pass

    RightSpacedArguments.left = [SpacedArguments]
    RightSpacedArguments.right = [Whitespaces]

    class AssertionContent(Grammar.Constituent):
        right_only = True

        def eval_conc(self):
            predicate_c, arguments_c = self.childvars[0]
            predicate = KIFGrammar.ontology.create_or_get(
                predicate_c.get_text())
            arguments = arguments_c.eval_conc()
            return KIFGrammar.ontology.call(predicate, arguments)

    AssertionContent.left = [Predicate]
    AssertionContent.right = [SpacedArguments]

    class SpacedAssertionContent(
            Grammar.RightIdentityConstituent,
            AssertionContent):
        pass

    SpacedAssertionContent.left = [Whitespace]
    SpacedAssertionContent.right = [AssertionContent]

    class OpenAssertion(Grammar.RightConc):
        pass

    OpenAssertion.left = [LParenthesis]
    OpenAssertion.right = [AssertionContent]

    class Assertion(Grammar.LeftConc, NonspacedSingleArgument, KIFItem):
        right_only = False

    Assertion.left = [OpenAssertion]
    Assertion.right = [RParenthesis]

    class SpacedAssertion(Grammar.RightIdentityConstituent, KIFItem):
        pass

    SpacedAssertion.left = [Whitespaces]
    SpacedAssertion.right = [Assertion]

    class Amp(Atom, CommentChar):
        pass

    Atom.categories['amp'] = Amp

    class Percent(Atom, CommentChar):
        pass

    Atom.categories['percent'] = Percent

    class QMark(Atom, CommentChar):
        pass

    Atom.categories['qmark'] = QMark

    class AtSign(Atom, CommentChar):
        pass

    Atom.categories['atsign'] = AtSign

    class Variables(Arguments):
        pass

    class SingleVariable(
            Grammar.AtomicConstituent,
            Variables,
            SingleArgument,
            Predicate):
        pass

    class VariableComb(Variables, ArgumentComb):
        pass

    class NonspacedVariables(Variables, NonspacedArguments):
        pass

    class NonspacedSingleVariable(
            NonspacedVariables,
            SingleVariable,
            NonspacedSingleArgument):
        pass

    NonspacedSingleVariable.left = [QMark]
    NonspacedSingleVariable.right = [Literal]

    class NonspacedSingleVariadicVariable(NonspacedSingleVariable):
        pass

    NonspacedSingleVariadicVariable.left = [AtSign]
    NonspacedSingleVariadicVariable.righ = [Literal]

    class NonspacedVariableComb(NonspacedVariables, VariableComb):
        pass

    class SpacedVariables(Variables, Grammar.RightIdentityConstituent):
        pass

    class SpacedVariableComb(SpacedVariables, VariableComb):
        pass

    class SpacedSingleVariable(SpacedVariables, SingleVariable):
        pass

    NonspacedVariableComb.left = [NonspacedVariables]
    NonspacedVariableComb.right = [SpacedSingleVariable]

    SpacedVariableComb.left = [Whitespaces]
    SpacedVariableComb.right = [NonspacedVariableComb]

    SpacedSingleVariable.left = [Whitespaces]
    SpacedSingleVariable.right = [NonspacedSingleVariable]

    class OpenVarGroup(Grammar.Constituent):
        pass

    OpenVarGroup.left = [LParenthesis]
    OpenVarGroup.right = [Variables]

    class QuantorArgument(Grammar.Constituent):
        pass

    class SpacedQuantorArgument(Grammar.Constituent):
        pass

    class Quantor(Predicate):
        pass

    class Forall(QuantorLiteral, Grammar.AtomicConstituent):
        pass

    Literal.literals['forall'] = Forall

    class Exists(QuantorLiteral, Grammar.AtomicConstituent):
        pass

    Literal.literals['exists'] = Exists

    SpacedQuantorArgument.left = [Spaces]
    SpacedQuantorArgument.right = [QuantorArgument]
    Quantor.left = [QuantorLiteral]
    Quantor.right = [SpacedQuantorArgument]

    class VarGroup(QuantorArgument, Grammar.LeftConc):
        pass

    VarGroup.left = [OpenVarGroup]
    VarGroup.right = [RParenthesis]

    class ImplPredPart(Grammar.Constituent):
        pass

    class Impl(Atom, CommentChar, ImplPredPart):
        pass

    Atom.categories['impl'] = Impl

    class ImplPredicate(Predicate, ImplPredPart, Grammar.AtomicConstituent):
        pass

    ImplPredicate.left = [ImplPredPart]
    ImplPredicate.right = [Impl]

    class KIF(KIFPart, Grammar.ListConstituent):
        def eval_conc(self):
            items = self.get_list_items()
            conc = KIFGrammar.ontology.create_or_get('Ontology')
            have_conc = KIFGrammar.ontology.create_or_get('have concept')
            for item in items:
                item_conc = item.eval_conc()
                if item_conc is None:
                    continue
                for attr, value in item_conc.attrs.items():
                    if attr.name.startswith('have argument #'):
                        conc.add_attr(have_conc, value[0])
                conc.add_attr(have_conc, item_conc)
            return conc

    KIF.left = [KIFPart]
    KIF.right = [KIFItem]
