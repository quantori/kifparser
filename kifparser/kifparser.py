from typing import TextIO, Generator
import tqdm

from aiire import Ontology, Grammar, Agenda


class KIFOntology(Ontology):
    def __init__(self):
        super().__init__()
        oconc = self.create_or_get('Ontology')
        concconc = self.create_or_get('Concept')
        have_conc = self.create_or_get('have concept')
        oconc.add_attr(have_conc, concconc)
        self.predicates = {
            'domain': self.domain_predicate,
            'documentation': self.doc_predicate,
            '=>': self.implication,
            '<=>': self.equivalence,
        }
        self.implications = []
        self.logical_operators = {
            self.create_or_get('and'): lambda c, p, v: (
                self.concept_fits_premise(c, p.getattr('have argument #0')[0], v) and
                self.concept_fits_premise(c, p.getattr('have argument #1')[0], v)
            ),
            self.create_or_get('or'): lambda c, p, v: (
                self.concept_fits_premise(c, p.getattr('have argument #0')[0], v) or
                self.concept_fits_premise(c, p.getattr('have argument #1')[0], v)
            ),
            self.create_or_get('not'): lambda c, p, v: (
                not self.concept_fits_premise(c, p.getattr('have argument #0')[0], v)
            ),
        }

    def domain_predicate(self, args):
        include = self.create_or_get('include')
        pred_conc, argno_conc, cls_conc = args.attrs[include]
        have_arg_rel = self.create_or_get(f'have argument #{argno_conc.name}')
        pred_conc.add_attr(have_arg_rel, cls_conc)

    def doc_predicate(self, args):
        include = self.create_or_get('include')
        conc, lang_conc, text = args.attrs[include]
        conc.descr = text

    def implication(self, args):
        premise, conclusion = args.getattr('include')
        self.implications.append((premise, conclusion))

    def equivalence(self, args):
        premise, conclusion = args.getattr('include')
        self.implications.append((premise, conclusion))
        self.implications.append((conclusion, premise))

    def call(self, predicate, arguments):
        if predicate.name in self.predicates:
            self.predicates[predicate.name](arguments)
        # print(f'eval {predicate.name}')
        try:
            args = arguments.getattr('include')
        except KeyError:
            args = [arguments]
        predconc = self.create_or_get(
            f'{predicate.name}({", ".join(a.name for a in args)})')
        have_pred = self.create_or_get(f'have predicate')
        predconc.add_attr(have_pred, predicate)
        for i, arg in enumerate(args):
            have_arg_rel = self.create_or_get(f'have argument #{i}')
            predconc.add_attr(have_arg_rel, arg)
        if len(args) == 2:
            if not args[0].name.startswith(
                    '?') and not args[1].name.startswith('?'):
                args[0].add_attr(predicate, args[1])
        return predconc

    def apply_implications(self):
        print('Applying implications')
        found = False
        for concept in list(self.by_name.values()):
            for premise, conclusion in self.implications:
                vd = {}
                if self.concept_fits_premise(concept, premise, vardict=vd):
                    c, is_new = self.apply_conclusion(vd, conclusion)
                    if is_new:
                        yield c
                        # print('premise:', premise)
                        # print('conclusion:', conclusion)
                        # print('c:', c)
                        found = True
        if found:
            yield from self.apply_implications()

    def concept_fits_premise(self, concept, premise, vardict=None):
        try:
            concpred = concept.getattr('have predicate')[0]
        except KeyError:
            if concept.name.startswith('?'):
                return False
            if concept.name == premise.name:
                return True
            if premise.name.startswith('?'):
                if vardict is not None:
                    vardict[premise.name] = concept
                return True
            return False
        try:
            prempred = premise.getattr('have predicate')[0]
        except KeyError:
            if premise.name.startswith('?'):
                if vardict is not None:
                    vardict[premise.name] = concept
                return True
            return False
        if prempred in self.logical_operators:
            return self.logical_operators[prempred](concept, premise, vardict)
        if concpred is not prempred:
            # print(f'Predicate mismatch: {concpred}, {prempred}')
            return False
        for attr in premise.attrs:
            if not attr.name.startswith('have argument #'):
                continue
            if attr not in concept.attrs:
                return False
            if not any(
                all(
                    self.concept_fits_premise(conc_attr_value, premise_attr_value, vardict=vardict)
                    for conc_attr_value in concept.attrs[attr]
                ) for premise_attr_value in premise.attrs[attr]
            ):
                return False
        return True

    def apply_conclusion(self, vardict, conclusion):
        try:
            conclpred = conclusion.getattr('have predicate')[0]
        except KeyError:
            if conclusion.name in vardict:
                return vardict[conclusion.name], False
            return conclusion, False
        new_attrs = {}
        args = []
        is_new = False
        for attr in conclusion.attrs:
            if not attr.name.startswith('have argument #'):
                continue
            argvalue, is_new = self.apply_conclusion(
                vardict, conclusion.attrs[attr][0])
            new_attrs[attr] = [argvalue]
            args.append(argvalue)
        have_pred = self.create_or_get(f'have predicate')
        name = f'{conclpred.name}({", ".join(a.name for a in args)})'
        is_new = is_new or (not (name in self.by_name))
        conc = self.create_or_get(name)
        if not is_new:
            return conc, False
        conc.add_attr(have_pred, conclpred)
        conc.attrs.update(new_attrs)
        if len(args) == 2:
            args[0].add_attr(conclpred, args[1])
        return conc, True


class KIFGrammar(Grammar):
    ontology = KIFOntology()

    class Atom(Grammar.Atom):

        categories = {}

        def get_cls_by_text(self):
            if self.text is None:
                return
            assert len(self.text) == 1
            return self.categories[self.get_category(self.text)]

        @staticmethod
        def get_category(char: str) -> str:
            if char == '\n':
                return 'newline'
            if char.isspace():
                return 'space'
            if char == '(':
                return 'lparenthesis'
            if char == ')':
                return 'rparenthesis'
            if char.isalpha() or char.isdigit() or char == '_' or char == '.' or char == '-':
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
        pass

    class CommentChar(TextStart):
        pass

    class CommentStart(Grammar.Constituent):
        pass

    class Semicolon(Atom, CommentChar, CommentStart):
        pass

    Atom.categories['semicolon'] = Semicolon

    class Text(Grammar.AtomicConstituent, TextStart):
        right_only = True

    Text.left = [TextStart]
    Text.right = [CommentChar]

    class Whitespaces(Grammar.AtomicConstituent, Grammar.Constituent):
        pass

    class Whitespace(Whitespaces):
        pass

    class WhitespaceComb(Whitespaces):
        pass

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


class KIFParser(object):

    def parse(
            self, io: TextIO
        ) -> Generator[KIFGrammar.Constituent, None, None]:
        agenda = self.create_agenda()
        pos = 0
        for line in tqdm.tqdm(io):
            for char in line:
                yield from agenda.put(KIFGrammar.Atom(pos, pos + 1, char))
                pos += 1

    def create_agenda(self):
        return KIFAgenda()


class KIFAgenda(Agenda):
    def __init__(self):
        super().__init__(KIFGrammar())


def main():
    import sys
    import csv
    sys.setrecursionlimit(200000)
    p = KIFParser()
    largest = None
    for obj in p.parse(sys.stdin):
        # print(obj)
        if largest is None:
            if isinstance(obj, KIFGrammar.KIFPart):
                largest = obj
            continue
        if isinstance(obj, KIFGrammar.KIFPart):
            if obj.end - obj.start > largest.end - largest.start:
                largest = obj
    print(largest)
    conc = largest.eval_conc()
    have_conc = KIFGrammar.ontology.create_or_get('have concept')
    # for impl in conc.ontology.apply_implications():
    #     conc.add_attr(have_conc, impl)
    print(conc)
    exprs_csv = open('exprs.csv', 'w')
    concs_csv = open('concs.csv', 'w')
    rels_csv = open('rels.csv', 'w')
    exprs_out = csv.writer(exprs_csv)
    concs_out = csv.writer(concs_csv)
    rels_out = csv.writer(rels_csv)
    expr_id = 1
    rel_id = 1
    for conc in conc.getattr('have concept'):
        if hasattr(conc, 'descr'):
            conc_name = conc.descr
            expr_name = conc.name
        else:
            expr_name = conc_name = conc.name
        exprs_out.writerow([expr_id, expr_name, expr_name])
        concs_out.writerow([conc.id, expr_id, conc_name])
        for attr in conc.attrs:
            for obj in conc.attrs[attr]:
                rels_out.writerow([rel_id, conc.id, attr.id, obj.id])
                rel_id += 1
        expr_id += 1
        print(conc)
    rels_csv.close()
    concs_csv.close()
    exprs_csv.close()


if __name__ == '__main__':
    main()
