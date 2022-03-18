"""
This module provides KIF ontology.

This ontology extends basic AIIRE ontology and performs logical
inference with SUO-KIF predicates
"""

from aiire import Ontology
from typing import Dict


class KIFOntology(Ontology):
    """
    KIFOntology is AIIRE Ontology for SUO-KIF concepts.

    KIFOntology provides logical inference with implications on
    predicates

    @ivar predicates: the mapping from predicate names to methods
        that implement the logic behind them.
    @ivar implications: a list of (premise, conclusion) pairs, where
        premise and conclusion are assertions on variables,
        and the conclusion can be applied (by the `apply_conclusion'
        method) to concept if and only if this concept fits the
        premise (checked by the `concept_fits_premise' method).
    @ivar logical_operators: the mapping from logical operator
        predicate names to functions checking whether a concept
        fits with the logical formula formed by the operator

    """

    def __init__(self):
        """Create a KIFOntology."""
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
            self.create_or_get('and'): self.concept_fits_premise_conjunction,
            self.create_or_get('or'): self.concept_fits_premise_disjunction,
            self.create_or_get('not'): self.concept_fits_premise_negation
        }

    def domain_predicate(self, args: Ontology.Concept):
        """
        Call the `domain' predicate.

        This predicate defines the i-th argument class for a predicate.
        When called, it should store it as an attribute of the
        predicate.
        """
        include = self.create_or_get('include')
        pred_conc, argno_conc, cls_conc = args.attrs[include]
        have_arg_rel = self.create_or_get(f'have argument #{argno_conc.name}')
        pred_conc.add_attr(have_arg_rel, cls_conc)

    def doc_predicate(self, args: Ontology.Concept):
        """
        Call the `documentation' predicate.

        When called, it should store the concept documentation as its
        description (concept.descr attribute)
        """
        include = self.create_or_get('include')
        conc, lang_conc, text = args.attrs[include]
        conc.descr = text

    def implication(self, args: Ontology.Concept):
        """
        Call the `=>' predicate.

        When called, it should store the premise and the conclusion
        of the implication in the KIFOntology implications dict.
        """
        premise, conclusion = args.getattr('include')
        self.implications.append((premise, conclusion))

    def equivalence(self, args: Ontology.Concept):
        """
        Call the `<=>' predicate.

        When called, it should store the equivalent assertions as
        premise and conclusion and vice versa in the KIFOntology
        implications dict.
        """
        premise, conclusion = args.getattr('include')
        self.implications.append((premise, conclusion))
        self.implications.append((conclusion, premise))

    def call(
        self, predicate: Ontology.Concept,
        arguments: Ontology.Concept
    ) -> Ontology.Concept:
        """
        Call an arbitrary predicate on the given arguments.

        @param predicate: the concept of the predicate
        @param arguments: the concept of the group of arguments
        """
        if predicate.name in self.predicates:
            self.predicates[predicate.name](arguments)
        # print(f'eval {predicate.name}')
        try:
            args = arguments.getattr('include')
        except KeyError:
            args = [arguments]
        predconc = self.create_or_get(
            f'{predicate.name}({", ".join(a.name for a in args)})')
        have_pred = self.create_or_get('have predicate')
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
        """Apply the implications on the whole ontology."""
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

    def concept_fits_premise(
        self,
        concept: Ontology.Concept,
        premise: Ontology.Concept,
        vardict: Dict[str, Ontology.Concept] = None
    ) -> bool:
        """
        Check whether concept fits the premise of an implication.

        Stores the premise variable values from the concept in
        `vardict' if it is not None.

        @param concept: the concept to check
        @param premise: the premise to check
        @param vardict: mapping from variable names from the premise
            to concepts related to the `concept'
        @return: True if the concept has all attributes of the
            premise, otherwise False
        """
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
                    self.concept_fits_premise(
                        conc_attr_value,
                        premise_attr_value,
                        vardict=vardict
                    )
                    for conc_attr_value in concept.attrs[attr]
                ) for premise_attr_value in premise.attrs[attr]
            ):
                return False
        return True

    def concept_fits_premise_conjunction(
        self,
        concept: Ontology.Concept, premise: Ontology.Concept,
        vardict: Dict[str, Ontology.Concept]
    ) -> bool:
        """
        Check whether `concept' fits conjunction of premises.

        @param concept: the concept to check
        @param premise: the conjunction of premises to check
        @vardict: the mapping from variable names to their values
            found in `concept'
        @return: True if `concept' fits both arguments of the
            conjunction as premises, otherwise False
        """
        return self.concept_fits_premise(
            concept, premise.getattr('have argument #0')[0], vardict
        ) and self.concept_fits_premise(
            concept, premise.getattr('have argument #1')[0], vardict
        )

    def concept_fits_premise_disjunction(
        self,
        concept: Ontology.Concept, premise: Ontology.Concept,
        vardict: Dict[str, Ontology.Concept]
    ) -> bool:
        """
        Check whether `concept' fits disjunction of premises.

        @param concept: the concept to check
        @param premise: the disjunction of premises to check
        @vardict: the mapping from variable names to their values
            found in `concept'
        @return: True if `concept' fits any of the disjunction
            arguments as premises, otherwise False
        """
        return self.concept_fits_premise(
            concept, premise.getattr('have argument #0')[0], vardict
        ) or self.concept_fits_premise(
            concept, premise.getattr('have argument #1')[0], vardict
        )

    def concept_fits_premise_negation(
        self,
        concept: Ontology.Concept, premise: Ontology.Concept,
        vardict: Dict[str, Ontology.Concept]
    ) -> bool:
        """
        Check whether `concept' fits negation of a premise.

        @param concept: the concept to check
        @param premise: the negation of a premise to check
        @vardict: the mapping from variable names to their values
            found in `concept'
        @return: True if `concept' does not fit the negation
            argument as premise, otherwise False
        """
        return not self.concept_fits_premise(
            concept, premise.getattr('have argument #0')[0], vardict
        )

    def apply_conclusion(
        self,
        vardict: Dict[str, Ontology.Concept],
        conclusion: Ontology.Concept
    ) -> Ontology.Concept:
        """
        Apply a conclusion to a concept using variable dict.

        @param vardict: a mapping from variable names to concepts
        @conclusion: a concept to be built with variables instead of
            some concepts
        @return: a concept which is a copy of the `conclusion' with
            variables substituted with their values from `vardict'
        """
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
        have_pred = self.create_or_get('have predicate')
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
