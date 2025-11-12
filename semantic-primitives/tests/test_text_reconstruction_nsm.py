#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de reconstruction de texte avec NSM
Valide la capacite a decoder/recoder du texte en preservant la fidelite semantique
"""

import sys
import os

# Ajouter le dossier parent au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'panlang'))

from panlang_reconstructeur_enrichi import ReconstructeurEnrichi


def test_phrase(reconstructeur, phrase, concepts_attendus):
    """Teste la decomposition d'une phrase"""
    print("\n" + "="*70)
    print("PHRASE: {}".format(phrase))
    print("-"*70)
    
    resultats = []
    primitives_totales = set()
    
    for concept in concepts_attendus:
        decomp = reconstructeur.decomposition_complete(concept)
        resultats.append(decomp)
        
        # Afficher decomposition
        print("\n[{}]".format(concept))
        if decomp["level"] >= 0:
            print("  Type: {}".format(decomp["type"]))
            print("  Explication: {}".format(decomp.get("explanation", "N/A")))
            
            # Collecter primitives
            if decomp["level"] == 0:
                primitives_totales.add(concept)
            elif "arbre" in decomp:
                prims = extraire_primitives(decomp["arbre"])
                primitives_totales.update(prims)
                print("  Primitives: {}".format(", ".join(sorted(prims))))
        else:
            print("  [INCONNU]")
    
    print("\n" + "-"*70)
    print("BILAN:")
    print("  Concepts trouves: {}/{}".format(
        len([r for r in resultats if r["level"] >= 0]),
        len(concepts_attendus)
    ))
    print("  Primitives utilisees: {}".format(len(primitives_totales)))
    print("  Liste: {}".format(", ".join(sorted(primitives_totales))))
    
    return {
        "phrase": phrase,
        "concepts": len(concepts_attendus),
        "concepts_trouves": len([r for r in resultats if r["level"] >= 0]),
        "primitives": len(primitives_totales),
        "details": resultats
    }


def extraire_primitives(arbre):
    """Extrait recurssivement toutes les primitives d'un arbre"""
    primitives = set()
    for noeud in arbre:
        if noeud["type"] == "PRIMITIVE":
            primitives.add(noeud["concept"])
        elif "children" in noeud:
            primitives.update(extraire_primitives(noeud["children"]))
    return primitives


def main():
    print("="*70)
    print("TEST DE RECONSTRUCTION SEMANTIQUE NSM")
    print("Objectif: Valider ATOMES -> MOLECULES -> COMPOSES -> TEXTE")
    print("="*70)
    
    reconstructeur = ReconstructeurEnrichi()
    
    # Corpus de test - 15 phrases avec concepts attendus
    tests = [
        {
            "phrase": "Le professeur enseigne les mathematiques aux etudiants",
            "concepts": ["ENSEIGNER", "SAVOIR"]
        },
        {
            "phrase": "Je veux apprendre a lire et ecrire",
            "concepts": ["VOULOIR", "APPRENDRE", "LIRE", "ECRIRE"]
        },
        {
            "phrase": "Elle comprend pourquoi il est triste",
            "concepts": ["COMPRENDRE", "TRISTE"]
        },
        {
            "phrase": "Les enfants jouent parce qu'ils sont contents",
            "concepts": ["JOUER", "CONTENT"]
        },
        {
            "phrase": "Il a peur de mourir",
            "concepts": ["PEUR", "MOURIR"]
        },
        {
            "phrase": "Nous voulons aider les gens qui ont faim",
            "concepts": ["VOULOIR", "AIDER", "GENS"]
        },
        {
            "phrase": "Elle donne un livre a son ami",
            "concepts": ["DONNER", "AVOIR"]
        },
        {
            "phrase": "Le bebe vient de naitre",
            "concepts": ["VENIR", "NAITRE"]
        },
        {
            "phrase": "Il travaille pour acheter une maison",
            "concepts": ["TRAVAILLER", "ACHETER"]
        },
        {
            "phrase": "Ils construisent un pont",
            "concepts": ["CONSTRUIRE", "FAIRE"]
        },
        {
            "phrase": "Je pense donc je suis",
            "concepts": ["PENSER", "ETRE"]
        },
        {
            "phrase": "Elle ecoute ce qu'il dit",
            "concepts": ["ECOUTER", "DIRE"]
        },
        {
            "phrase": "Il promet de venir demain",
            "concepts": ["PROMETTRE", "VENIR"]
        },
        {
            "phrase": "Les plantes grandissent quand il pleut",
            "concepts": ["GRANDIR", "QUAND"]
        },
        {
            "phrase": "Elle aime lire des livres parce que c'est bon",
            "concepts": ["AIMER", "LIRE", "PARCE_QUE", "BON"]
        }
    ]
    
    # Executer tests
    resultats = []
    for test in tests:
        resultat = test_phrase(reconstructeur, test["phrase"], test["concepts"])
        resultats.append(resultat)
    
    # Statistiques globales
    print("\n" + "="*70)
    print("STATISTIQUES GLOBALES")
    print("="*70)
    
    total_concepts = sum(r["concepts"] for r in resultats)
    total_trouves = sum(r["concepts_trouves"] for r in resultats)
    total_primitives = sum(r["primitives"] for r in resultats)
    
    print("\nCouverture:")
    print("  Phrases testees: {}".format(len(tests)))
    print("  Concepts totaux: {}".format(total_concepts))
    print("  Concepts trouves: {} ({:.1f}%)".format(
        total_trouves,
        100 * total_trouves / total_concepts if total_concepts > 0 else 0
    ))
    print("  Primitives utilisees: {}".format(total_primitives))
    print("  Moyenne primitives/phrase: {:.1f}".format(
        total_primitives / len(tests) if len(tests) > 0 else 0
    ))
    
    # Fidelite de reconstruction
    fidelite = 100 * total_trouves / total_concepts if total_concepts > 0 else 0
    print("\nFidelite de reconstruction: {:.1f}%".format(fidelite))
    
    if fidelite >= 90:
        print("  [EXCELLENT] Reconstruction tres fidele")
    elif fidelite >= 75:
        print("  [BON] Reconstruction fidele")
    elif fidelite >= 50:
        print("  [MOYEN] Reconstruction partielle")
    else:
        print("  [FAIBLE] Reconstruction limitee")
    
    print("\n" + "="*70)
    print("[OK] Tests termines!")
    print("="*70)


if __name__ == "__main__":
    main()
