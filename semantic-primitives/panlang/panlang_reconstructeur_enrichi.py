#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reconstructeur Enrichi - Systeme de decomposition et recomposition semantique
Base sur NSM (Natural Semantic Metalanguage) avec architecture a 4 niveaux
"""

from nsm_primitives import (
    NSM_PRIMITIVES,
    NSM_MOLECULES,
    COMPOSED_CONCEPTS,
    get_primitive,
    get_molecule,
    get_concept
)


class ReconstructeurEnrichi:
    """
    Reconstructeur semantique enrichi avec NSM
    Architecture: ATOMES -> MOLECULES -> COMPOSES -> CULTUREL
    """
    
    def __init__(self):
        self.primitives = NSM_PRIMITIVES
        self.molecules = NSM_MOLECULES
        self.composed = COMPOSED_CONCEPTS
        self.cache = {}
    
    def decomposer_concept(self, concept):
        """
        Decompose un concept en ses elements constitutifs
        
        Args:
            concept: Le concept a decomposer (str)
            
        Returns:
            dict avec la decomposition complete
        """
        concept_upper = concept.upper()
        
        # Deja en cache ?
        if concept_upper in self.cache:
            return self.cache[concept_upper]
        
        # Niveau 0: Primitive
        if concept_upper in self.primitives:
            result = {
                "concept": concept,
                "level": 0,
                "type": "PRIMITIVE",
                "data": self.primitives[concept_upper]
            }
            self.cache[concept_upper] = result
            return result
        
        # Niveau 1: Molecule
        if concept_upper in self.molecules:
            mol = self.molecules[concept_upper]
            result = {
                "concept": concept,
                "level": 1,
                "type": "MOLECULE",
                "composition": mol["composition"],
                "explanation": mol.get("explanation", ""),
                "sanskrit": mol.get("sanskrit", ""),
                "primitives": [
                    self.decomposer_concept(p) for p in mol["composition"]
                ]
            }
            self.cache[concept_upper] = result
            return result
        
        # Niveau 2: Compose
        if concept_upper in self.composed:
            comp = self.composed[concept_upper]
            result = {
                "concept": concept,
                "level": 2,
                "type": "COMPOSE",
                "molecules": comp["molecules"],
                "explanation": comp.get("explanation", ""),
                "sanskrit": comp.get("sanskrit", ""),
                "decomposition": [
                    self.decomposer_concept(m) for m in comp["molecules"]
                ]
            }
            self.cache[concept_upper] = result
            return result
        
        # Inconnu
        return {
            "concept": concept,
            "level": -1,
            "type": "INCONNU",
            "error": "Concept non trouve dans la base NSM"
        }
    
    def decomposition_complete(self, concept):
        """
        Decomposition recursive complete jusqu'aux primitives
        
        Args:
            concept: Le concept a decomposer
            
        Returns:
            dict avec l'arbre de decomposition complet
        """
        decomp = self.decomposer_concept(concept)
        
        if decomp["level"] == 0:
            # Deja une primitive
            return decomp
        
        if decomp["level"] == 1:
            # Molecule - decomposer les primitives
            return {
                "concept": concept,
                "level": 1,
                "type": "MOLECULE",
                "explanation": decomp.get("explanation", ""),
                "arbre": self._construire_arbre(decomp["composition"])
            }
        
        if decomp["level"] == 2:
            # Compose - decomposer molecules et primitives
            return {
                "concept": concept,
                "level": 2,
                "type": "COMPOSE",
                "explanation": decomp.get("explanation", ""),
                "arbre": self._construire_arbre(decomp["molecules"])
            }
        
        return decomp
    
    def _construire_arbre(self, elements):
        """Construit l'arbre de decomposition recursif"""
        arbre = []
        for elem in elements:
            decomp = self.decomposer_concept(elem)
            
            if decomp["level"] == 0:
                # Primitive - feuille de l'arbre
                arbre.append({
                    "concept": elem,
                    "type": "PRIMITIVE",
                    "sanskrit": decomp["data"].get("sanskrit", "")
                })
            elif decomp["level"] == 1:
                # Molecule - descendre
                arbre.append({
                    "concept": elem,
                    "type": "MOLECULE",
                    "explanation": decomp.get("explanation", ""),
                    "children": self._construire_arbre(decomp["composition"])
                })
            elif decomp["level"] == 2:
                # Compose - descendre
                arbre.append({
                    "concept": elem,
                    "type": "COMPOSE",
                    "explanation": decomp.get("explanation", ""),
                    "children": self._construire_arbre(decomp["molecules"])
                })
            else:
                arbre.append({
                    "concept": elem,
                    "type": "INCONNU"
                })
        
        return arbre
    
    def composer(self, primitives):
        """
        Compose des primitives en concepts de plus haut niveau
        
        Args:
            primitives: Liste de primitives
            
        Returns:
            Liste de concepts possibles
        """
        primitives_set = set(p.upper() for p in primitives)
        candidats = []
        
        # Chercher molecules correspondantes
        for mol_name, mol_data in self.molecules.items():
            mol_prims = set(p.upper() for p in mol_data["composition"])
            if mol_prims.issubset(primitives_set):
                candidats.append({
                    "concept": mol_name,
                    "level": 1,
                    "type": "MOLECULE",
                    "explanation": mol_data.get("explanation", ""),
                    "coverage": len(mol_prims) / len(primitives_set)
                })
        
        # Chercher composes correspondants
        for comp_name, comp_data in self.composed.items():
            comp_mols = set(m.upper() for m in comp_data["molecules"])
            # Verifier si les molecules sont disponibles
            comp_prims = set()
            for mol in comp_mols:
                if mol in self.molecules:
                    comp_prims.update(
                        p.upper() for p in self.molecules[mol]["composition"]
                    )
                elif mol in self.primitives:
                    comp_prims.add(mol)
            
            if comp_prims.issubset(primitives_set):
                candidats.append({
                    "concept": comp_name,
                    "level": 2,
                    "type": "COMPOSE",
                    "explanation": comp_data.get("explanation", ""),
                    "coverage": len(comp_prims) / len(primitives_set)
                })
        
        # Trier par couverture (meilleurs matches en premier)
        candidats.sort(key=lambda x: x["coverage"], reverse=True)
        return candidats
    
    def analyser_texte(self, texte):
        """
        Analyse un texte et identifie les concepts semantiques
        
        Args:
            texte: Le texte a analyser
            
        Returns:
            dict avec l'analyse semantique
        """
        mots = texte.upper().split()
        concepts_trouves = []
        primitives_utilisees = set()
        
        for mot in mots:
            decomp = self.decomposer_concept(mot)
            if decomp["level"] >= 0:
                concepts_trouves.append(decomp)
                
                # Collecter primitives
                if decomp["level"] == 0:
                    primitives_utilisees.add(mot)
                elif decomp["level"] == 1:
                    primitives_utilisees.update(
                        p.upper() for p in decomp["composition"]
                    )
                elif decomp["level"] == 2:
                    # Recursif pour composes
                    for mol in decomp["molecules"]:
                        mol_upper = mol.upper()
                        if mol_upper in self.molecules:
                            primitives_utilisees.update(
                                p.upper()
                                for p in self.molecules[mol_upper]["composition"]
                            )
        
        return {
            "texte": texte,
            "concepts": [c["concept"] for c in concepts_trouves],
            "concepts_trouves": len(concepts_trouves),
            "primitives_utilisees": list(primitives_utilisees),
            "nb_primitives": len(primitives_utilisees),
            "details": concepts_trouves
        }


if __name__ == "__main__":
    print("=== Reconstructeur Enrichi NSM ===")
    print()
    
    reconstructeur = ReconstructeurEnrichi()
    
    # Test decomposition
    concept = "ENSEIGNER"
    print("Test decomposition: {}".format(concept))
    decomp = reconstructeur.decomposition_complete(concept)
    print("Resultat:")
    print(decomp)
    print()
    
    # Test composition
    print("Test composition avec primitives: VOULOIR, SAVOIR")
    compo = reconstructeur.composer(["VOULOIR", "SAVOIR"])
    print("Concepts possibles:")
    for c in compo[:3]:
        print("  - {}: {}".format(c["concept"], c["explanation"]))
