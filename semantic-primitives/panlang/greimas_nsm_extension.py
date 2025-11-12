#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extension Greimas-NSM - Enrichissement du systeme NSM avec concepts sémiotiques
Integre le carre semiotique et le modele actantiel dans le graphe semantique
"""

from nsm_primitives import NSM_PRIMITIVES, NSM_MOLECULES
from panlang_reconstructeur_enrichi import ReconstructeurEnrichi
from enum import Enum
from typing import Dict, List, Tuple, Optional


class OppositionType(Enum):
    """Types d'opposition selon le carre semiotique de Greimas"""
    CONTRAIRE = "contraire"           # S1 <-> S2 (VIE <-> MORT)
    CONTRADICTION = "contradiction"   # S1 <-> non-S1 (VIE <-> NON-VIE)
    SUBCONTRAIRE = "subcontraire"    # non-S1 <-> non-S2 (NON-VIE <-> NON-MORT)


class ActantRole(Enum):
    """Roles actantiels selon le modele de Greimas"""
    SUJET = "sujet"                  # Celui qui accomplit l'action
    OBJET = "objet"                  # Ce qui est vise
    DESTINATEUR = "destinateur"      # Celui qui mandate
    DESTINATAIRE = "destinataire"    # Beneficiaire final
    ADJUVANT = "adjuvant"           # Aide le sujet
    OPPOSANT = "opposant"           # Fait obstacle


class NarrativePhase(Enum):
    """Phases du schema narratif canonique"""
    MANIPULATION = "manipulation"     # Incitation a agir
    COMPETENCE = "competence"         # Acquisition de moyens
    PERFORMANCE = "performance"       # Action principale
    SANCTION = "sanction"            # Evaluation finale


class CarreSemiotique:
    """
    Implementation du carre semiotique de Greimas
    Structure d'opposition semantique a 4 positions
    """
    
    def __init__(self, s1: str, s2: str):
        """
        Initialise un carre avec deux termes contraires
        
        Args:
            s1: Premier terme (ex: BON)
            s2: Second terme contraire (ex: MAUVAIS)
        """
        self.s1 = s1.upper()
        self.s2 = s2.upper()
        self.non_s1 = "NON_{}".format(s1.upper())
        self.non_s2 = "NON_{}".format(s2.upper())
        
        # Structure du carre
        self.oppositions = {
            (self.s1, self.s2): OppositionType.CONTRAIRE,
            (self.s2, self.s1): OppositionType.CONTRAIRE,
            
            (self.s1, self.non_s1): OppositionType.CONTRADICTION,
            (self.non_s1, self.s1): OppositionType.CONTRADICTION,
            (self.s2, self.non_s2): OppositionType.CONTRADICTION,
            (self.non_s2, self.s2): OppositionType.CONTRADICTION,
            
            (self.non_s1, self.non_s2): OppositionType.SUBCONTRAIRE,
            (self.non_s2, self.non_s1): OppositionType.SUBCONTRAIRE,
        }
    
    def get_opposition(self, terme1: str, terme2: str) -> Optional[OppositionType]:
        """Retourne le type d'opposition entre deux termes"""
        key = (terme1.upper(), terme2.upper())
        return self.oppositions.get(key)
    
    def get_position(self, terme: str) -> str:
        """Retourne la position d'un terme dans le carre"""
        terme_upper = terme.upper()
        if terme_upper == self.s1:
            return "S1"
        elif terme_upper == self.s2:
            return "S2"
        elif terme_upper == self.non_s1:
            return "non-S2"
        elif terme_upper == self.non_s2:
            return "non-S1"
        else:
            return "HORS_CARRE"
    
    def afficher(self) -> str:
        """Affiche le carre semiotique"""
        return """
Carre Semiotique:

    {}  <------- contraire ------->  {}
     |                                  |
     |                                  |
  contradiction                    contradiction
     |                                  |
     v                                  v
    {}  <---- subcontraire ---->  {}
        """.format(self.s1, self.s2, self.non_s2, self.non_s1)


class ModeleActantiel:
    """
    Implementation du modele actantiel de Greimas
    Structure a 6 actants
    """
    
    def __init__(self):
        self.actants = {role: None for role in ActantRole}
    
    def definir_actant(self, role: ActantRole, actant: str):
        """Definit un actant pour un role"""
        self.actants[role] = actant
    
    def get_actant(self, role: ActantRole) -> Optional[str]:
        """Retourne l'actant d'un role"""
        return self.actants.get(role)
    
    def valider(self) -> bool:
        """Valide que SUJET et OBJET sont definis (minimum)"""
        return (self.actants[ActantRole.SUJET] is not None and
                self.actants[ActantRole.OBJET] is not None)
    
    def afficher(self) -> str:
        """Affiche le schema actantiel"""
        d1 = self.actants[ActantRole.DESTINATEUR] or "?"
        obj = self.actants[ActantRole.OBJET] or "?"
        d2 = self.actants[ActantRole.DESTINATAIRE] or "?"
        sujet = self.actants[ActantRole.SUJET] or "?"
        adj = self.actants[ActantRole.ADJUVANT] or "?"
        opp = self.actants[ActantRole.OPPOSANT] or "?"
        
        return """
Schema Actantiel:

DESTINATEUR: {} ---> OBJET: {} ---> DESTINATAIRE: {}
                        ^
                        |
                    SUJET: {}
                    /         \\
                   /           \\
           ADJUVANT: {}    OPPOSANT: {}
        """.format(d1, obj, d2, sujet, adj, opp)


class ReconstructeurGreimasNSM(ReconstructeurEnrichi):
    """
    Extension du reconstructeur NSM avec concepts de Greimas
    Integre carre semiotique et modele actantiel
    """
    
    def __init__(self):
        super().__init__()
        
        # Carres semiotiques predefinis pour primitives
        self.carres = self._initialiser_carres_primitives()
        
        # Cache pour analyses actantielles
        self.analyses_actantielles = {}
    
    def _initialiser_carres_primitives(self) -> Dict[str, CarreSemiotique]:
        """Initialise les carres semiotiques pour primitives NSM"""
        carres = {}
        
        # Oppositions principales
        paires_contraires = [
            ("BON", "MAUVAIS"),
            ("GRAND", "PETIT"),
            ("BEAUCOUP", "PEU"),
            ("AVANT", "APRES"),
            ("AU_DESSUS", "EN_DESSOUS"),
            ("PRES", "LOIN"),
            ("VIVRE", "MOURIR"),
        ]
        
        for s1, s2 in paires_contraires:
            cle = "{}_{}".format(s1, s2)
            carres[cle] = CarreSemiotique(s1, s2)
        
        return carres
    
    def analyser_opposition(self, terme1: str, terme2: str) -> Optional[Dict]:
        """
        Analyse l'opposition entre deux termes
        
        Returns:
            Dict avec type d'opposition et carre correspondant
        """
        terme1_upper = terme1.upper()
        terme2_upper = terme2.upper()
        
        # Chercher dans les carres existants
        for cle, carre in self.carres.items():
            opp = carre.get_opposition(terme1_upper, terme2_upper)
            if opp:
                return {
                    "type": opp,
                    "carre": carre,
                    "position_t1": carre.get_position(terme1_upper),
                    "position_t2": carre.get_position(terme2_upper)
                }
        
        return None
    
    def creer_modele_actantiel(self, phrase: str, 
                               analyse_linguistique: Dict) -> ModeleActantiel:
        """
        Cree un modele actantiel a partir d'une analyse linguistique
        
        Args:
            phrase: La phrase analysee
            analyse_linguistique: Dict avec sujet, verbe, objet, etc.
        
        Returns:
            ModeleActantiel complete
        """
        modele = ModeleActantiel()
        
        # Mapping simple (a enrichir selon contexte)
        if "sujet" in analyse_linguistique:
            modele.definir_actant(ActantRole.SUJET, 
                                 analyse_linguistique["sujet"])
        
        if "objet" in analyse_linguistique:
            modele.definir_actant(ActantRole.OBJET, 
                                 analyse_linguistique["objet"])
        
        if "complement_attribution" in analyse_linguistique:
            modele.definir_actant(ActantRole.DESTINATAIRE,
                                 analyse_linguistique["complement_attribution"])
        
        # Sauvegarder
        self.analyses_actantielles[phrase] = modele
        
        return modele
    
    def detecter_isotopies(self, texte: str) -> Dict[str, int]:
        """
        Detecte les isotopies (repetitions de primitives) dans un texte
        Equivalent computationnel du concept greimassien
        
        Returns:
            Dict des primitives recurrentes avec leurs frequences
        """
        analyse = self.analyser_texte(texte)
        
        # Compter frequences primitives
        frequences = {}
        
        for concept_detail in analyse["details"]:
            if concept_detail["level"] == 0:
                # Primitive directe
                prim = concept_detail["concept"]
                frequences[prim] = frequences.get(prim, 0) + 1
            
            elif concept_detail["level"] == 1 and "composition" in concept_detail:
                # Molecule - compter ses primitives
                for prim in concept_detail["composition"]:
                    frequences[prim] = frequences.get(prim, 0) + 1
        
        # Trier par frequence decroissante
        isotopies = dict(sorted(frequences.items(), 
                               key=lambda x: x[1], 
                               reverse=True))
        
        return isotopies
    
    def analyser_coherence_oppositions(self, texte: str) -> Dict:
        """
        Analyse la coherence des oppositions dans un texte
        Detecte tensions et contradictions semantiques
        
        Returns:
            Dict avec oppositions detectees et score de coherence
        """
        analyse = self.analyser_texte(texte)
        primitives_presentes = set()
        
        # Collecter toutes les primitives du texte
        for concept_detail in analyse["details"]:
            if concept_detail["level"] == 0:
                primitives_presentes.add(concept_detail["concept"])
            elif concept_detail["level"] == 1 and "composition" in concept_detail:
                primitives_presentes.update(concept_detail["composition"])
        
        # Detecter oppositions
        oppositions_detectees = []
        contradictions = []
        
        primitives_list = list(primitives_presentes)
        for i, p1 in enumerate(primitives_list):
            for p2 in primitives_list[i+1:]:
                analyse_opp = self.analyser_opposition(p1, p2)
                if analyse_opp:
                    oppositions_detectees.append({
                        "terme1": p1,
                        "terme2": p2,
                        "type": analyse_opp["type"].value
                    })
                    
                    # Contradiction = tension semantique
                    if analyse_opp["type"] == OppositionType.CONTRADICTION:
                        contradictions.append((p1, p2))
        
        # Score de coherence (moins de contradictions = plus coherent)
        score_coherence = 1.0
        if len(primitives_presentes) > 0:
            taux_contradiction = len(contradictions) / len(primitives_presentes)
            score_coherence = max(0.0, 1.0 - taux_contradiction)
        
        return {
            "oppositions": oppositions_detectees,
            "contradictions": contradictions,
            "score_coherence": score_coherence,
            "primitives_totales": len(primitives_presentes)
        }


def demo_greimas_nsm():
    """Demonstration de l'integration Greimas-NSM"""
    print("="*70)
    print("DEMONSTRATION INTEGRATION GREIMAS-NSM")
    print("="*70)
    
    reconstructeur = ReconstructeurGreimasNSM()
    
    # Test 1: Carre semiotique
    print("\n[TEST 1] Carre Semiotique: BON/MAUVAIS")
    print("-"*70)
    carre = reconstructeur.carres["BON_MAUVAIS"]
    print(carre.afficher())
    
    analyse_opp = reconstructeur.analyser_opposition("BON", "MAUVAIS")
    print("\nAnalyse opposition BON <-> MAUVAIS:")
    print("  Type: {}".format(analyse_opp["type"].value))
    print("  Position BON: {}".format(analyse_opp["position_t1"]))
    print("  Position MAUVAIS: {}".format(analyse_opp["position_t2"]))
    
    # Test 2: Modele actantiel
    print("\n[TEST 2] Modele Actantiel")
    print("-"*70)
    modele = ModeleActantiel()
    modele.definir_actant(ActantRole.SUJET, "Professeur")
    modele.definir_actant(ActantRole.OBJET, "Connaissance")
    modele.definir_actant(ActantRole.DESTINATAIRE, "Etudiants")
    modele.definir_actant(ActantRole.DESTINATEUR, "Universite")
    modele.definir_actant(ActantRole.ADJUVANT, "Manuel")
    modele.definir_actant(ActantRole.OPPOSANT, "Difficulte")
    
    print(modele.afficher())
    print("Validation: {}".format("OK" if modele.valider() else "INCOMPLET"))
    
    # Test 3: Detection isotopies
    print("\n[TEST 3] Detection Isotopies")
    print("-"*70)
    texte_test = "Je veux apprendre parce que je veux savoir"
    isotopies = reconstructeur.detecter_isotopies(texte_test)
    
    print("Texte: \"{}\"".format(texte_test))
    print("\nIsotopies detectees (primitives recurrentes):")
    for prim, freq in list(isotopies.items())[:5]:
        print("  {}: {} occurrences".format(prim, freq))
    
    # Test 4: Coherence oppositions
    print("\n[TEST 4] Coherence des Oppositions")
    print("-"*70)
    texte_test2 = "Il est bon mais mauvais, grand et petit"
    coherence = reconstructeur.analyser_coherence_oppositions(texte_test2)
    
    print("Texte: \"{}\"".format(texte_test2))
    print("\nOppositions detectees: {}".format(len(coherence["oppositions"])))
    for opp in coherence["oppositions"]:
        print("  {} <-> {} ({})".format(
            opp["terme1"], opp["terme2"], opp["type"]
        ))
    
    print("\nContradictions (tensions semantiques): {}".format(
        len(coherence["contradictions"])
    ))
    print("Score de coherence: {:.2f}".format(coherence["score_coherence"]))
    
    print("\n" + "="*70)
    print("DEMONSTRATION TERMINEE")
    print("="*70)


if __name__ == "__main__":
    demo_greimas_nsm()
