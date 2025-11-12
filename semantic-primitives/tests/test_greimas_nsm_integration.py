#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Integration Greimas-NSM
Valide l'enrichissement du systeme NSM avec concepts semiotiques
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'panlang'))

from greimas_nsm_extension import (
    ReconstructeurGreimasNSM,
    CarreSemiotique,
    ModeleActantiel,
    ActantRole
)


def test_carres_semiotiques():
    """Test des carres semiotiques"""
    print("\n" + "="*70)
    print("TEST 1: CARRES SEMIOTIQUES")
    print("="*70)
    
    reconstructeur = ReconstructeurGreimasNSM()
    
    tests = [
        ("BON", "MAUVAIS", "contraire"),
        ("BON", "NON_BON", "contradiction"),
        ("NON_MAUVAIS", "NON_BON", "subcontraire"),
        ("GRAND", "PETIT", "contraire"),
        ("VIVRE", "MOURIR", "contraire"),
    ]
    
    reussis = 0
    for t1, t2, type_attendu in tests:
        analyse = reconstructeur.analyser_opposition(t1, t2)
        if analyse and analyse["type"].value == type_attendu:
            print("[OK] {} <-> {} : {}".format(t1, t2, type_attendu))
            reussis += 1
        else:
            print("[FAIL] {} <-> {} : attendu {}, obtenu {}".format(
                t1, t2, type_attendu, 
                analyse["type"].value if analyse else "None"
            ))
    
    print("\nResultat: {}/{} tests reussis".format(reussis, len(tests)))
    return reussis == len(tests)


def test_modele_actantiel():
    """Test du modele actantiel"""
    print("\n" + "="*70)
    print("TEST 2: MODELE ACTANTIEL")
    print("="*70)
    
    scenarios = [
        {
            "nom": "Enseignement",
            "actants": {
                ActantRole.SUJET: "Professeur",
                ActantRole.OBJET: "Connaissance",
                ActantRole.DESTINATAIRE: "Etudiants",
                ActantRole.DESTINATEUR: "Universite",
                ActantRole.ADJUVANT: "Manuel",
                ActantRole.OPPOSANT: "Difficulte"
            }
        },
        {
            "nom": "Quete heroique",
            "actants": {
                ActantRole.SUJET: "Heros",
                ActantRole.OBJET: "Tresor",
                ActantRole.DESTINATAIRE: "Royaume",
                ActantRole.DESTINATEUR: "Roi",
                ActantRole.ADJUVANT: "Epee magique",
                ActantRole.OPPOSANT: "Dragon"
            }
        }
    ]
    
    reussis = 0
    for scenario in scenarios:
        modele = ModeleActantiel()
        for role, actant in scenario["actants"].items():
            modele.definir_actant(role, actant)
        
        if modele.valider():
            print("[OK] Scenario '{}' valide".format(scenario["nom"]))
            reussis += 1
        else:
            print("[FAIL] Scenario '{}' invalide".format(scenario["nom"]))
    
    print("\nResultat: {}/{} scenarios valides".format(reussis, len(scenarios)))
    return reussis == len(scenarios)


def test_isotopies():
    """Test detection isotopies"""
    print("\n" + "="*70)
    print("TEST 3: DETECTION ISOTOPIES")
    print("="*70)
    
    reconstructeur = ReconstructeurGreimasNSM()
    
    tests = [
        {
            "texte": "Je veux apprendre parce que je veux savoir",
            "isotopies_attendues": ["JE", "VOULOIR", "SAVOIR"],
            "theme": "volition cognitive"
        },
        {
            "texte": "Il aime lire et comprendre",
            "isotopies_attendues": ["SAVOIR"],
            "theme": "cognition"
        }
    ]
    
    reussis = 0
    for test in tests:
        isotopies = reconstructeur.detecter_isotopies(test["texte"])
        
        # Verifier presence des isotopies attendues
        trouvees = all(
            iso in isotopies for iso in test["isotopies_attendues"]
        )
        
        if trouvees:
            print("[OK] Theme '{}' detecte".format(test["theme"]))
            print("     Texte: \"{}\"".format(test["texte"]))
            print("     Isotopies: {}".format(
                ", ".join(
                    "{} ({})".format(k, v) 
                    for k, v in list(isotopies.items())[:3]
                )
            ))
            reussis += 1
        else:
            print("[FAIL] Theme '{}' non detecte".format(test["theme"]))
    
    print("\nResultat: {}/{} themes detectes".format(reussis, len(tests)))
    return reussis == len(tests)


def test_coherence_oppositions():
    """Test analyse coherence par oppositions"""
    print("\n" + "="*70)
    print("TEST 4: COHERENCE DES OPPOSITIONS")
    print("="*70)
    
    reconstructeur = ReconstructeurGreimasNSM()
    
    tests = [
        {
            "texte": "C'est bon et agreable",
            "coherence_min": 0.8,
            "contradictions_max": 0,
            "description": "texte coherent"
        },
        {
            "texte": "Il est grand et petit en meme temps",
            "coherence_min": 0.5,
            "contradictions_max": 2,
            "description": "texte avec tension"
        }
    ]
    
    reussis = 0
    for test in tests:
        coherence = reconstructeur.analyser_coherence_oppositions(test["texte"])
        
        coherent = (
            coherence["score_coherence"] >= test["coherence_min"] and
            len(coherence["contradictions"]) <= test["contradictions_max"]
        )
        
        if coherent:
            print("[OK] {} : score {:.2f}".format(
                test["description"], 
                coherence["score_coherence"]
            ))
            print("     Texte: \"{}\"".format(test["texte"]))
            print("     Oppositions: {}".format(len(coherence["oppositions"])))
            print("     Contradictions: {}".format(
                len(coherence["contradictions"])
            ))
            reussis += 1
        else:
            print("[FAIL] {} : score {:.2f} (attendu >= {})".format(
                test["description"],
                coherence["score_coherence"],
                test["coherence_min"]
            ))
    
    print("\nResultat: {}/{} analyses coherentes".format(reussis, len(tests)))
    return reussis == len(tests)


def test_integration_complete():
    """Test d'integration complete: NSM + Greimas"""
    print("\n" + "="*70)
    print("TEST 5: INTEGRATION COMPLETE NSM + GREIMAS")
    print("="*70)
    
    reconstructeur = ReconstructeurGreimasNSM()
    
    phrase = "Le professeur enseigne les mathematiques aux etudiants"
    
    print("\nPhrase analysee: \"{}\"".format(phrase))
    print("-"*70)
    
    # 1. Decomposition NSM
    print("\n[1] DECOMPOSITION NSM")
    decomp = reconstructeur.decomposer_concept("ENSEIGNER")
    if decomp["level"] >= 0:
        print("    ENSEIGNER = {} + {} + {}".format(
            *decomp.get("composition", ["?", "?", "?"])
        ))
        print("    Niveau: {} ({})".format(decomp["level"], decomp["type"]))
    
    # 2. Analyse actantielle
    print("\n[2] ANALYSE ACTANTIELLE")
    modele = ModeleActantiel()
    modele.definir_actant(ActantRole.SUJET, "Professeur")
    modele.definir_actant(ActantRole.OBJET, "Connaissance mathematique")
    modele.definir_actant(ActantRole.DESTINATAIRE, "Etudiants")
    modele.definir_actant(ActantRole.DESTINATEUR, "Systeme educatif")
    print("    SUJET: {}".format(modele.get_actant(ActantRole.SUJET)))
    print("    OBJET: {}".format(modele.get_actant(ActantRole.OBJET)))
    print("    DESTINATAIRE: {}".format(
        modele.get_actant(ActantRole.DESTINATAIRE)
    ))
    
    # 3. Isotopies
    print("\n[3] ISOTOPIES THEMATIQUES")
    isotopies = reconstructeur.detecter_isotopies(phrase)
    print("    Primitives recurrentes:")
    for prim, freq in list(isotopies.items())[:3]:
        print("      - {}: {} occurrence(s)".format(prim, freq))
    
    # 4. Coherence
    print("\n[4] COHERENCE SEMANTIQUE")
    coherence = reconstructeur.analyser_coherence_oppositions(phrase)
    print("    Score coherence: {:.2f}".format(coherence["score_coherence"]))
    print("    Oppositions: {}".format(len(coherence["oppositions"])))
    print("    Contradictions: {}".format(len(coherence["contradictions"])))
    
    # Validation globale
    print("\n" + "-"*70)
    success = (
        decomp["level"] >= 0 and
        modele.valider() and
        coherence["score_coherence"] >= 0.8
    )
    # Note: isotopies peut etre vide si aucun concept reconnu dans phrase
    
    if success:
        print("[OK] Integration complete validee")
        print("     Toutes les analyses fonctionnent ensemble")
    else:
        print("[FAIL] Integration incomplete")
    
    return success


def main():
    """Execute tous les tests"""
    print("="*70)
    print("SUITE DE TESTS: INTEGRATION GREIMAS-NSM")
    print("Objectif: Valider enrichissement semiotique du systeme NSM")
    print("="*70)
    
    tests = [
        ("Carres semiotiques", test_carres_semiotiques),
        ("Modele actantiel", test_modele_actantiel),
        ("Detection isotopies", test_isotopies),
        ("Coherence oppositions", test_coherence_oppositions),
        ("Integration complete", test_integration_complete)
    ]
    
    resultats = []
    for nom, test_func in tests:
        try:
            resultat = test_func()
            resultats.append((nom, resultat))
        except Exception as e:
            print("\n[ERREUR] Test '{}': {}".format(nom, e))
            import traceback
            traceback.print_exc()
            resultats.append((nom, False))
    
    # Rapport final
    print("\n" + "="*70)
    print("RAPPORT FINAL")
    print("="*70)
    
    reussis = sum(1 for _, r in resultats if r)
    total = len(resultats)
    
    print("\nResultats par test:")
    for nom, resultat in resultats:
        statut = "[OK]  " if resultat else "[FAIL]"
        print("  {} {}".format(statut, nom))
    
    print("\n" + "-"*70)
    print("BILAN: {}/{} tests reussis ({:.1f}%)".format(
        reussis, total, 100 * reussis / total if total > 0 else 0
    ))
    
    if reussis == total:
        print("\n[SUCCES] Integration Greimas-NSM pleinement fonctionnelle!")
        print("Le systeme NSM est maintenant enrichi avec:")
        print("  - Carres semiotiques (oppositions)")
        print("  - Modele actantiel (roles narratifs)")
        print("  - Detection isotopies (coherence thematique)")
        print("  - Analyse coherence (tensions semantiques)")
    else:
        print("\n[ATTENTION] {}/{} tests ont echoue".format(
            total - reussis, total
        ))
    
    print("="*70)
    
    return reussis == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
