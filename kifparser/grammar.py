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

    These classes are used by Grammar.bind method to produce immediate
    constituents for parse trees.
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
        """Arbitrary sequence of spaces, e.g.: '       '."""

    class Space(Atom, CommentChar, Whitespace, Whitespaces, Spaces):
        """Space character (not including newline), e.g.: ' '."""

    Atom.categories['space'] = Space

    class SpaceComb(Spaces):
        """
        Arbitrary combination of spaces, e.g.: '  '.

        Single space character is a Spaces instance, but not a
        SpaceComb, because it is not a combination.

        CNF-style rule: SpaceComb -> Spaces Space
        """

    SpaceComb.left = [Spaces]
    SpaceComb.right = [Space]

    class LParenthesis(Atom, CommentChar):
        """Left parenthesis: '('."""

    Atom.categories['lparenthesis'] = LParenthesis

    class RParenthesis(Atom, CommentChar):
        """Right parenthesis: ')'."""

    Atom.categories['rparenthesis'] = RParenthesis

    class Quot(Atom, CommentChar):
        """Double quote: '"'."""

    Atom.categories['quot'] = Quot

    class LiteralStart(Grammar.Constituent):
        """Any combination which can be start of a literal: 'abc'."""

    class Predicate(Grammar.Constituent):
        """Any literal which bears a function of predicate: '=>'."""

    class QuantorLiteral(Grammar.Constituent):
        """Any literal which bears a function of quantor: 'exists'."""

    class Arguments(Grammar.Constituent):
        """Any sequence of arguments: '?x Human (instance ?x ?y)'."""

        right_only = True

    class SingleArgument(Arguments):
        """Single argument: 'Human'."""

        def eval_conc(self) -> KIFOntology.Concept:
            """Evaluate argument concept by name lookup."""
            return KIFGrammar.ontology.create_or_get(self.get_text())

    class ArgumentComb(Arguments, Grammar.InlineListConstituent):
        """Argument combination: '?x Human'."""

    class NonspacedArguments(Arguments):
        """Arguments without preceding space: '?x Human'."""

    class NonspacedSingleArgument(NonspacedArguments, SingleArgument):
        """Single argument without preceding space: 'Human'."""

    class NonspacedArgumentComb(NonspacedArguments, ArgumentComb):
        """
        Argument combination without preceding space: '?x Human'.

        CNF-style rule:
        NonspacedArgumentComb ->
            NonspacedArguments SpacedSingleArgument
        """

    class Literal(LiteralStart, Predicate, NonspacedSingleArgument):
        """
        Any literal: 'Human'.

        Literals can be both predicates and arguments.
        """

        right_only = False
        literals = {}

        def __init__(self, *args, **kwargs):
            """Create literal, also changing class."""
            super().__init__(*args, **kwargs)
            text = self.get_text()
            if text in self.literals:
                self.__class__ = self.literals[text]

    class UAlNum(Atom, Literal, CommentChar):
        """
        Underscore, alphanumeric, dot or dash character: 'a'.

        UAlNum can be in a Literal or a Comment.
        """

    Atom.categories['ualnum'] = UAlNum

    class ComplexLiteral(
        Literal, Grammar.AtomicConstituent, Grammar.ListConstituent
    ):
        """
        Complex (2 characters or more) literal: 'Human'.

        CNF-style rule: ComplexLiteral -> LiteralStart UAlNum
        """

        def eval_conc(self) -> KIFOntology.Concept:
            """Evaluate concept by getting or creating it by name."""
            return KIFGrammar.ontology.create_or_get(self.get_text())

    ComplexLiteral.left = [LiteralStart]
    ComplexLiteral.right = [UAlNum]

    class KIFPart(Grammar.Constituent):
        """
        Any immediate part of KIF file structure.

        KIFPart can be atomic (KIFItem) or complex (can consist of
        multiple KIFItems).
        """

    class KIFItem(KIFPart):
        """
        Any atomic immediate part of KIF file structure.

        KIFItems are: EmptyLine, CommentLine, Assertion.
        """

    class EmptyLine(KIFItem):
        """A separate line which is empty."""

        def eval_conc(self) -> KIFOntology.Concept:
            """Evaluate concept as None, do nothing."""

    class NewLine(Atom, EmptyLine, Whitespace):
        r"""Newline character: '\n'."""

    Atom.categories['newline'] = NewLine

    class BlankLine(Grammar.AtomicConstituent, EmptyLine):
        r"""
        Blank line: '     \n'.

        CNF-style rule: BlankLine -> Spaces NewLine
        """

    BlankLine.left = [Spaces]
    BlankLine.right = [NewLine]

    class NewLinedText(Grammar.Constituent):
        r"""
        Newline character followed by a text: '\n Lorem ipsum...'.

        This constituent is used to extend Text to MultilineText.

        CNF-style rule: NewLinedText -> NewLine Text
        """

    NewLinedText.left = [NewLine]
    NewLinedText.right = [Text]

    class MultilineText(Grammar.AtomicConstituent, Grammar.ListConstituent):
        r"""
        Multiline text: 'Lorem ipsum\ndolor sit\namet'.

        CNF-style rules:
            MultilineText -> TextStart NewLinedText
            MultilineText -> MultilineText NewLinedText
        """

        right_only = True

    MultilineText.left = [TextStart, MultilineText]
    MultilineText.right = [NewLinedText]

    class OpenDocText(Grammar.Constituent):
        """
        Documentation text with opening double quote: '"Lorem ...'.

        CNF-style rules:
            OpenDocText -> Quot Text
            OpenDocText -> Quot MultilineText
        """

    OpenDocText.left = [Quot]
    OpenDocText.right = [Text, MultilineText]

    class DocText(NonspacedSingleArgument):
        """
        Documentation text with both double quote: '"Lorem ..."'.

        CNF-style rules:
            DocText -> OpenDocText Quot
        """

    DocText.left = [OpenDocText]
    DocText.right = [Quot]

    class Comment(Grammar.AtomicConstituent, Grammar.ListConstituent):
        """
        Comment: ';; Lorem ipsum dolor sit amet'.

        CNF-style rule: Comment -> CommentStart TextStart
        """

    class CommentLine(EmptyLine, Grammar.AtomicConstituent):
        r"""
        Comment line: ';; Lorem ipsum dolor sit amet\n'.

        CNF-style rule: CommentLine -> Comment NewLine
        """

    class SpacedCommentStart(CommentStart):
        """
        Comment start with spaces: '  ;'.

        CNF-style rule: Spaces Semicolon
        """

    SpacedCommentStart.left = [Spaces]
    SpacedCommentStart.right = [Semicolon]

    Comment.left = [CommentStart]
    Comment.right = [TextStart]

    CommentLine.left = [Comment]
    CommentLine.right = [NewLine]

    class Unknown(Atom, CommentChar):
        """Unknown character: '!'."""

    Atom.categories['unknown'] = Unknown

    class SpacedArguments(Grammar.RightIdentityConstituent, Arguments):
        """Arbitrary arguments with preceding spaces: '  ?a b'."""

        right_only = True

    class SpacedSingleArgument(SpacedArguments, SingleArgument):
        """
        Single argument with preceding spaces: '   ?a'.

        CNF-style rule:
            SpacedSingleArgument -> Whitespaces NonspacedSingleArgument
        """

    class SpacedArgumentComb(SpacedArguments, ArgumentComb):
        """
        Argument combination with preceding spaces: '   ?a b'.

        CNF-style rule:
            SpacedArgumentComb -> Whitespaces NonspacedArgumentComb
        """

    NonspacedArgumentComb.left = [NonspacedArguments]
    NonspacedArgumentComb.right = [SpacedSingleArgument]

    SpacedSingleArgument.left = [Whitespaces]
    SpacedSingleArgument.right = [NonspacedSingleArgument]

    SpacedArgumentComb.left = [Whitespaces]
    SpacedArgumentComb.right = [NonspacedArgumentComb]

    class RightSpacedArguments(Grammar.LeftConc, SpacedArguments):
        """
        Arguments followed by spaces: ' ?a b   '.

        CNF-style rule:
            RightSpacedArguments -> SpacedArguments Whitespaces
        """

    RightSpacedArguments.left = [SpacedArguments]
    RightSpacedArguments.right = [Whitespaces]

    class AssertionContent(Grammar.Constituent):
        """
        Content of an assertion: 'predicate a ?b (c  d e )'.

        CNF-style rule:
            AssertionContent -> Predicate SpacedArguments
        """

        right_only = True

        def eval_conc(self):
            """Evaluate concept calling predicate with arguments."""
            predicate_c, arguments_c = self.childvars[0]
            predicate = KIFGrammar.ontology.create_or_get(
                predicate_c.get_text()
            )
            arguments = arguments_c.eval_conc()
            return KIFGrammar.ontology.call(predicate, arguments)

    AssertionContent.left = [Predicate]
    AssertionContent.right = [SpacedArguments]

    class SpacedAssertionContent(
        Grammar.RightIdentityConstituent,
        AssertionContent
    ):
        """
        Assertion content preceded by whitespace: ' predicate a b c'.

        CNF-style rule:
            SpacedAssertionContent -> Whitespace AssertionContent
        """

    SpacedAssertionContent.left = [Whitespace]
    SpacedAssertionContent.right = [AssertionContent]

    class OpenAssertion(Grammar.RightConc):
        """
        Assertion with opening (left) parenthesis: '(predicate a b'.

        CNF-style rule:
            OpenAssertion -> LParenthesis AssertionContent
        """

    OpenAssertion.left = [LParenthesis]
    OpenAssertion.right = [AssertionContent]

    class Assertion(Grammar.LeftConc, NonspacedSingleArgument, KIFItem):
        """
        Assertion with both parentheses: '(predicate a b)'.

        CNF-style rule: Assertion -> OpenAssertion RParenthesis
        """

        right_only = False

    Assertion.left = [OpenAssertion]
    Assertion.right = [RParenthesis]

    class SpacedAssertion(Grammar.RightIdentityConstituent, KIFItem):
        """
        Assertion preceded by whitespaces: '  (predicate a b)'.

        CNF-style rule: SpacedAssertion -> Whitespaces Assertion
        """

    SpacedAssertion.left = [Whitespaces]
    SpacedAssertion.right = [Assertion]

    class Amp(Atom, CommentChar):
        """Ampersand sign: '&'."""

    Atom.categories['amp'] = Amp

    class Percent(Atom, CommentChar):
        """Percent sign: '%'."""

    Atom.categories['percent'] = Percent

    class QMark(Atom, CommentChar):
        """Question mark: '?'."""

    Atom.categories['qmark'] = QMark

    class AtSign(Atom, CommentChar):
        """At sign: '@'."""

    Atom.categories['atsign'] = AtSign

    class Variables(Arguments):
        """Arbitrary sequence of variables: '?a ?b @c'."""

    class SingleVariable(
        Grammar.AtomicConstituent,
        Variables,
        SingleArgument,
        Predicate
    ):
        """Single variable: '?a'."""

    class VariableComb(Variables, ArgumentComb):
        """Variable combination: '?a @b'."""

    class NonspacedVariables(Variables, NonspacedArguments):
        """Variable sequence without preceding spaces: '?a @b ?c'."""

    class NonspacedSingleVariable(
        NonspacedVariables,
        SingleVariable,
        NonspacedSingleArgument
    ):
        """
        Single variable without preceding spaces: '?a'.

        CNF-style rule: NonspacedSingleVariable -> QMark Literal
        """

    NonspacedSingleVariable.left = [QMark]
    NonspacedSingleVariable.right = [Literal]

    class NonspacedSingleVariadicVariable(NonspacedSingleVariable):
        """
        Single variadic variable without preceding spaces: '@a'.

        CNF-style rule:
            NonspacedSingleVariadicVariable -> AtSign Literal
        """

    NonspacedSingleVariadicVariable.left = [AtSign]
    NonspacedSingleVariadicVariable.righ = [Literal]

    class NonspacedVariableComb(NonspacedVariables, VariableComb):
        """
        Variable combination without preceding spaces: '?a ?b'.

        CNF-style rule:
            NonspacedVariableComb ->
                NonspacedVariables SpacedSingleVariable
        """

    class SpacedVariables(Variables, Grammar.RightIdentityConstituent):
        """Variable sequence with preceding spaces: ' ?a ?b'."""

    class SpacedVariableComb(SpacedVariables, VariableComb):
        """
        Variable combination with preceding whitespaces: ' ?a ?b'.

        CNF-style rule:
            SpacedVariableComb -> Whitespaces NonspacedVariableComb
        """

    class SpacedSingleVariable(SpacedVariables, SingleVariable):
        """
        Single variable with preceding whitespaces: ' ?a'.

        CNF-style rule:
            SpacedSingleVariable ->
                Whitespaces NonspacedSingleVariable
        """

    NonspacedVariableComb.left = [NonspacedVariables]
    NonspacedVariableComb.right = [SpacedSingleVariable]

    SpacedVariableComb.left = [Whitespaces]
    SpacedVariableComb.right = [NonspacedVariableComb]

    SpacedSingleVariable.left = [Whitespaces]
    SpacedSingleVariable.right = [NonspacedSingleVariable]

    class OpenVarGroup(Grammar.Constituent):
        """
        Variable group with opening (left) parenthesis: '( ?a ?b'.

        CNF-style rule: OpenVarGroup -> LParenthesis Variables
        """

    OpenVarGroup.left = [LParenthesis]
    OpenVarGroup.right = [Variables]

    class QuantorArgument(Grammar.Constituent):
        """Quantor argument, a group of bound variables: '(?a ?b)'."""

    class SpacedQuantorArgument(Grammar.Constituent):
        """
        Quantor argument with preceding spaces: '  (?a ?b)'.

        CNF-style rule:
            SpacedQuantorArgument -> Spaces QuantorArgument
        """

    class Quantor(Predicate):
        """
        Quantor with its bound variables: 'exists (?a ?b)'.

        CNF-style rule:
            Quantor -> QuantorLiteral SpacedQuantorArgument
        """

    class Forall(QuantorLiteral, Grammar.AtomicConstituent):
        """The universal ∀ ('for all') quantifier: 'forall'."""

    Literal.literals['forall'] = Forall

    class Exists(QuantorLiteral, Grammar.AtomicConstituent):
        """The existential ∃ ('exists') quantifier: 'exists'."""

    Literal.literals['exists'] = Exists

    SpacedQuantorArgument.left = [Spaces]
    SpacedQuantorArgument.right = [QuantorArgument]
    Quantor.left = [QuantorLiteral]
    Quantor.right = [SpacedQuantorArgument]

    class VarGroup(QuantorArgument, Grammar.LeftConc):
        """
        Variable group with both parentheses: '(?a ?b)'.

        CNF-style rule: VarGroup -> OpenVarGroup RParenthesis
        """

    VarGroup.left = [OpenVarGroup]
    VarGroup.right = [RParenthesis]

    class ImplPredPart(Grammar.Constituent):
        """Implication predicate part: '=>'."""

    class Impl(Atom, CommentChar, ImplPredPart):
        """Implication predicate character: '>'."""

    Atom.categories['impl'] = Impl

    class ImplPredicate(Predicate, ImplPredPart, Grammar.AtomicConstituent):
        """
        Implication predicate: '=>'.

        A predicate with name which consists of characters:
        '=', '>', '<'.

        CNF-style rule: ImplPredicate -> ImplPredPart Impl
        """

    ImplPredicate.left = [ImplPredPart]
    ImplPredicate.right = [Impl]

    class KIF(KIFPart, Grammar.ListConstituent):
        """
        SUO-KIF language file.

        CNF-style rule: KIF -> KIFPart KIFItem
        """

        def eval_conc(self) -> KIFOntology.Concept:
            """
            Evaluate KIF concept from its parts.

            @return: a concept of ontology with all concepts
                extracted from KIF items. This concept is not an
                Ontology instance, but rather a Concept instance;
                it can be further transformed into an Ontology.
            """
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
