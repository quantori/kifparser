"""
This module provides KIF ontology.

This ontology extends basic AIIRE ontology and performs logical
inference with SUO-KIF predicates
"""

from aiire import Ontology


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
