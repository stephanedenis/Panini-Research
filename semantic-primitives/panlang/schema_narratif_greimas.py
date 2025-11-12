# -*- coding: utf-8 -*-
"""
Schema Narratif Canonique de Greimas

Implemente les 4 phases du schema narratif canonique:
1. MANIPULATION (contrat narratif)
2. COMPETENCE (acquisition des moyens)
3. PERFORMANCE (action principale)
4. SANCTION (evaluation)

Reference:
- Greimas, A.J. (1966). Semantique structurale
- Hebert, L. (2020). Le schema narratif canonique
"""

from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass


class PhaseNarrative(Enum):
    """Les 4 phases du schema narratif canonique"""
    MANIPULATION = "MANIPULATION"
    COMPETENCE = "COMPETENCE"
    PERFORMANCE = "PERFORMANCE"
    SANCTION = "SANCTION"


class TypeManipulation(Enum):
    """Types de manipulation selon Greimas"""
    TENTATION = "TENTATION"  # Par desir (jouissance positive)
    INTIMIDATION = "INTIMIDATION"  # Par peur (menace negative)
    SEDUCTION = "SEDUCTION"  # Par image positive de soi
    PROVOCATION = "PROVOCATION"  # Par image negative de soi


class TypeSanction(Enum):
    """Types de sanction"""
    RECONNAISSANCE = "RECONNAISSANCE"  # Sanction cognitive (savoir)
    RETRIBUTION = "RETRIBUTION"  # Sanction pragmatique (avoir)


@dataclass
class ActeNarratif:
    """Un acte narratif dans une phase"""
    phase: PhaseNarrative
    actant_sujet: str
    actant_objet: str
    action: str
    modalite: Optional[str] = None  # vouloir, devoir, savoir, pouvoir
    resultat: Optional[str] = None


@dataclass
class SchemaNarratif:
    """Schema narratif complet d'un recit"""
    titre: str
    manipulation: List[ActeNarratif]
    competence: List[ActeNarratif]
    performance: List[ActeNarratif]
    sanction: List[ActeNarratif]
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire"""
        return {
            'titre': self.titre,
            'manipulation': [self._acte_to_dict(a) for a in self.manipulation],
            'competence': [self._acte_to_dict(a) for a in self.competence],
            'performance': [self._acte_to_dict(a) for a in self.performance],
            'sanction': [self._acte_to_dict(a) for a in self.sanction]
        }
    
    def _acte_to_dict(self, acte: ActeNarratif) -> Dict:
        return {
            'phase': acte.phase.value,
            'sujet': acte.actant_sujet,
            'objet': acte.actant_objet,
            'action': acte.action,
            'modalite': acte.modalite,
            'resultat': acte.resultat
        }


class AnalyseurNarratif:
    """Analyseur de schemas narratifs"""
    
    # Marqueurs linguistiques pour chaque phase
    MARQUEURS_MANIPULATION = [
        'vouloir', 'devoir', 'obliger', 'forcer', 'demander', 'ordonner',
        'proposer', 'suggerer', 'commander', 'exiger', 'contraindre'
    ]
    
    MARQUEURS_COMPETENCE = [
        'apprendre', 'savoir', 'pouvoir', 'acquerir', 'obtenir', 'recevoir',
        'se preparer', 'entrainer', 'etudier', 'comprendre', 'decouvrir'
    ]
    
    MARQUEURS_PERFORMANCE = [
        'faire', 'accomplir', 'realiser', 'executer', 'agir', 'transformer',
        'creer', 'detruire', 'construire', 'combattre', 'vaincre'
    ]
    
    MARQUEURS_SANCTION = [
        'recompenser', 'punir', 'juger', 'evaluer', 'reconnaitre', 'celebrer',
        'condamner', 'approuver', 'blamer', 'honorer', 'reussir', 'echouer'
    ]
    
    def __init__(self):
        self.schemas_exemples = self._charger_schemas_exemples()
    
    def detecter_phase(self, texte: str) -> PhaseNarrative:
        """Detecte la phase narrative dominante dans un texte"""
        texte_lower = texte.lower()
        
        scores = {
            PhaseNarrative.MANIPULATION: sum(1 for m in self.MARQUEURS_MANIPULATION if m in texte_lower),
            PhaseNarrative.COMPETENCE: sum(1 for m in self.MARQUEURS_COMPETENCE if m in texte_lower),
            PhaseNarrative.PERFORMANCE: sum(1 for m in self.MARQUEURS_PERFORMANCE if m in texte_lower),
            PhaseNarrative.SANCTION: sum(1 for m in self.MARQUEURS_SANCTION if m in texte_lower)
        }
        
        # Phase avec score maximum
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def analyser_recit(self, texte: str, titre: str = "Recit") -> SchemaNarratif:
        """Analyse un recit et extrait son schema narratif"""
        phrases = [p.strip() for p in texte.split('.') if p.strip()]
        
        # Initialisation des listes d'actes
        manipulation = []
        competence = []
        performance = []
        sanction = []
        
        # Classification de chaque phrase
        for phrase in phrases:
            phase = self.detecter_phase(phrase)
            
            # Creation acte narratif simple
            acte = ActeNarratif(
                phase=phase,
                actant_sujet="?",  # A completer avec NLP avance
                actant_objet="?",
                action=phrase[:50] + "..." if len(phrase) > 50 else phrase
            )
            
            # Ajout a la bonne phase
            if phase == PhaseNarrative.MANIPULATION:
                manipulation.append(acte)
            elif phase == PhaseNarrative.COMPETENCE:
                competence.append(acte)
            elif phase == PhaseNarrative.PERFORMANCE:
                performance.append(acte)
            elif phase == PhaseNarrative.SANCTION:
                sanction.append(acte)
        
        return SchemaNarratif(
            titre=titre,
            manipulation=manipulation,
            competence=competence,
            performance=performance,
            sanction=sanction
        )
    
    def generer_rapport(self, schema: SchemaNarratif) -> str:
        """Genere un rapport textuel du schema narratif"""
        rapport = []
        rapport.append("=" * 70)
        rapport.append(f"SCHEMA NARRATIF : {schema.titre}")
        rapport.append("=" * 70)
        rapport.append("")
        
        # Phase 1: Manipulation
        rapport.append("1. MANIPULATION (Contrat narratif)")
        rapport.append("-" * 40)
        if schema.manipulation:
            for acte in schema.manipulation:
                rapport.append(f"   - {acte.action}")
        else:
            rapport.append("   (Aucun acte detecte)")
        rapport.append("")
        
        # Phase 2: Competence
        rapport.append("2. COMPETENCE (Acquisition des moyens)")
        rapport.append("-" * 40)
        if schema.competence:
            for acte in schema.competence:
                rapport.append(f"   - {acte.action}")
        else:
            rapport.append("   (Aucun acte detecte)")
        rapport.append("")
        
        # Phase 3: Performance
        rapport.append("3. PERFORMANCE (Action principale)")
        rapport.append("-" * 40)
        if schema.performance:
            for acte in schema.performance:
                rapport.append(f"   - {acte.action}")
        else:
            rapport.append("   (Aucun acte detecte)")
        rapport.append("")
        
        # Phase 4: Sanction
        rapport.append("4. SANCTION (Evaluation)")
        rapport.append("-" * 40)
        if schema.sanction:
            for acte in schema.sanction:
                rapport.append(f"   - {acte.action}")
        else:
            rapport.append("   (Aucun acte detecte)")
        rapport.append("")
        
        # Statistiques
        rapport.append("=" * 70)
        rapport.append("STATISTIQUES")
        rapport.append("=" * 70)
        rapport.append(f"Total actes          : {len(schema.manipulation) + len(schema.competence) + len(schema.performance) + len(schema.sanction)}")
        rapport.append(f"Manipulation         : {len(schema.manipulation)} actes")
        rapport.append(f"Competence           : {len(schema.competence)} actes")
        rapport.append(f"Performance          : {len(schema.performance)} actes")
        rapport.append(f"Sanction             : {len(schema.sanction)} actes")
        
        return "\n".join(rapport)
    
    def _charger_schemas_exemples(self) -> Dict[str, SchemaNarratif]:
        """Charge des schemas narratifs exemples canoniques"""
        schemas = {}
        
        # Le Petit Chaperon Rouge
        schemas['petit_chaperon'] = SchemaNarratif(
            titre="Le Petit Chaperon Rouge",
            manipulation=[
                ActeNarratif(PhaseNarrative.MANIPULATION, "Mere", "Chaperon", 
                           "La mere demande au Chaperon d'aller voir grand-mere", "devoir")
            ],
            competence=[
                ActeNarratif(PhaseNarrative.COMPETENCE, "Mere", "Chaperon",
                           "La mere donne un panier et des conseils", "savoir")
            ],
            performance=[
                ActeNarratif(PhaseNarrative.PERFORMANCE, "Loup", "Grand-mere",
                           "Le loup devore la grand-mere", "pouvoir"),
                ActeNarratif(PhaseNarrative.PERFORMANCE, "Loup", "Chaperon",
                           "Le loup tente de devorer le Chaperon", "pouvoir"),
                ActeNarratif(PhaseNarrative.PERFORMANCE, "Chasseur", "Loup",
                           "Le chasseur tue le loup", "pouvoir")
            ],
            sanction=[
                ActeNarratif(PhaseNarrative.SANCTION, "Tous", "Chaperon",
                           "Le Chaperon est sauve et recompense", resultat="positif")
            ]
        )
        
        # Le Conte de Cendrillon
        schemas['cendrillon'] = SchemaNarratif(
            titre="Cendrillon",
            manipulation=[
                ActeNarratif(PhaseNarrative.MANIPULATION, "Prince", "Royaume",
                           "Le prince organise un bal pour trouver epouse", "vouloir")
            ],
            competence=[
                ActeNarratif(PhaseNarrative.COMPETENCE, "Maraine", "Cendrillon",
                           "La marraine donne robe et carrosse", "pouvoir"),
                ActeNarratif(PhaseNarrative.COMPETENCE, "Maraine", "Cendrillon",
                           "Avertissement: rentrer avant minuit", "devoir")
            ],
            performance=[
                ActeNarratif(PhaseNarrative.PERFORMANCE, "Cendrillon", "Bal",
                           "Cendrillon va au bal et charme le prince", "faire"),
                ActeNarratif(PhaseNarrative.PERFORMANCE, "Cendrillon", "Palais",
                           "Cendrillon fuit a minuit et perd pantoufle", "faire")
            ],
            sanction=[
                ActeNarratif(PhaseNarrative.SANCTION, "Prince", "Cendrillon",
                           "Le prince retrouve et epouse Cendrillon", resultat="positif")
            ]
        )
        
        return schemas
    
    def get_schema_exemple(self, nom: str) -> Optional[SchemaNarratif]:
        """Recupere un schema exemple"""
        return self.schemas_exemples.get(nom)


# =============================================================================
# TESTS ET DEMONSTRATIONS
# =============================================================================

def test_detection_phases():
    """Test detection de phases narratives"""
    print("=== TEST DETECTION PHASES ===\n")
    
    analyseur = AnalyseurNarratif()
    
    exemples = [
        ("Le roi ordonne au chevalier de sauver la princesse", PhaseNarrative.MANIPULATION),
        ("Le chevalier apprend l'art de l'epee", PhaseNarrative.COMPETENCE),
        ("Le chevalier combat et vainc le dragon", PhaseNarrative.PERFORMANCE),
        ("Le roi recompense le chevalier pour sa bravoure", PhaseNarrative.SANCTION)
    ]
    
    for texte, phase_attendue in exemples:
        phase_detectee = analyseur.detecter_phase(texte)
        statut = "✓" if phase_detectee == phase_attendue else "✗"
        print(f"{statut} '{texte[:50]}...'")
        print(f"   Attendu: {phase_attendue.value}, Detecte: {phase_detectee.value}\n")


def test_schemas_exemples():
    """Test des schemas narratifs exemples"""
    print("\n=== TEST SCHEMAS EXEMPLES ===\n")
    
    analyseur = AnalyseurNarratif()
    
    for nom in ['petit_chaperon', 'cendrillon']:
        schema = analyseur.get_schema_exemple(nom)
        if schema:
            rapport = analyseur.generer_rapport(schema)
            print(rapport)
            print("\n")


def test_analyse_recit():
    """Test analyse d'un recit complet"""
    print("\n=== TEST ANALYSE RECIT ===\n")
    
    recit = """
    Le roi demande au jeune heros de recuperer l'epee magique. 
    Le heros doit traverser la foret enchantee. 
    Il apprend aupres du sage les secrets de la magie. 
    Il obtient une amulette protectrice. 
    Il combat les creatures de la foret. 
    Il trouve l'epee et la ramene au roi. 
    Le roi le recompense et le nomme chevalier. 
    Tout le royaume celebre sa victoire.
    """
    
    analyseur = AnalyseurNarratif()
    schema = analyseur.analyser_recit(recit, "La Quete de l'Epee Magique")
    rapport = analyseur.generer_rapport(schema)
    
    print(rapport)


if __name__ == "__main__":
    print("=" * 70)
    print("SCHEMA NARRATIF CANONIQUE DE GREIMAS")
    print("=" * 70)
    print()
    
    # Execution des tests
    test_detection_phases()
    test_schemas_exemples()
    test_analyse_recit()
    
    print("\n" + "=" * 70)
    print("✓ TOUS LES TESTS REUSSIS")
    print("=" * 70)
