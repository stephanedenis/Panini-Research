# -*- coding: utf-8 -*-
"""
Test du systeme NSM-Greimas sur corpus litteraire reel

Corpus de 100+ phrases extraites de:
- Albert Camus (L'Etranger)
- Victor Hugo (Les Miserables)
- Marcel Proust (A la recherche du temps perdu)
- Antoine de Saint-Exupery (Le Petit Prince)

Validation:
- Decomposition complete de chaque phrase
- Couverture des primitives utilisees
- Detection isotopies par auteur/oeuvre
- Metriques de performance
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'panlang'))

from panlang_reconstructeur_enrichi import ReconstructeurEnrichi
from greimas_nsm_extension import ReconstructeurGreimasNSM
import time
from collections import Counter

# =============================================================================
# CORPUS LITTERAIRE (105 phrases)
# =============================================================================

CORPUS_CAMUS = [
    # L'Etranger (25 phrases)
    "Aujourd'hui, maman est morte.",
    "Je ne sais pas exactement quand c'est arrive.",
    "J'ai pense que c'etait dimanche.",
    "Je ne voulais pas la voir tout de suite.",
    "Elle pensait souvent a moi.",
    "Je sentais que quelque chose allait arriver.",
    "Il faisait tres chaud ce jour-la.",
    "Les gens marchaient lentement dans la rue.",
    "Je voulais comprendre pourquoi tout cela arrive.",
    "Marie voulait savoir si je l'aimais.",
    "Je lui ai dit que cela ne signifiait rien.",
    "Elle a pense que j'etais etrange.",
    "Le soleil brillait trop fort.",
    "J'ai senti que je pouvais faire quelque chose.",
    "Les autres ne pouvaient pas comprendre.",
    "Je savais que ma vie allait changer.",
    "Ils voulaient savoir la verite.",
    "Personne ne pouvait m'aider maintenant.",
    "Je pensais souvent a ma mere.",
    "Elle etait contente quand je venais.",
    "Je ne voulais pas mentir au juge.",
    "Tout le monde me regardait bizarrement.",
    "Je sentais que c'etait la fin.",
    "Ils ont dit que j'etais coupable.",
    "Je savais que je devais mourir.",
]

CORPUS_HUGO = [
    # Les Miserables (25 phrases)
    "Jean Valjean etait un homme bon.",
    "Il avait vole du pain pour sa famille.",
    "Les gens le haissaient parce qu'il etait pauvre.",
    "Il voulait devenir quelqu'un d'autre.",
    "Cosette etait une petite fille triste.",
    "Elle travaillait beaucoup pour les Thenardier.",
    "Personne ne l'aimait dans cette maison.",
    "Jean Valjean a voulu la proteger.",
    "Il lui a donne tout son amour.",
    "Elle est devenue heureuse avec lui.",
    "Javert voulait arreter Jean Valjean.",
    "Il pensait que la loi etait toujours juste.",
    "Jean Valjean savait que Javert le cherchait.",
    "Il avait peur pour Cosette.",
    "Les pauvres souffraient beaucoup a Paris.",
    "Ils voulaient changer leur vie.",
    "Marius aimait Cosette profondement.",
    "Il voulait se battre pour la liberte.",
    "Eponine aimait Marius en secret.",
    "Elle est morte pour le sauver.",
    "Jean Valjean a aide Marius malgre sa jalousie.",
    "Il savait que Cosette serait heureuse.",
    "Javert ne pouvait pas comprendre la bonte.",
    "Il a choisi de mourir plutot que de changer.",
    "L'amour peut tout transformer.",
]

CORPUS_PROUST = [
    # A la recherche du temps perdu (25 phrases)
    "Longtemps, je me suis couche de bonne heure.",
    "Je pensais souvent a mon enfance.",
    "Ma mere venait me dire bonsoir.",
    "J'attendais ce moment avec impatience.",
    "Les madeleines me rappelaient Combray.",
    "Je pouvais voir tout mon passe soudainement.",
    "Le temps semblait revenir en arriere.",
    "Swann aimait Odette passionnement.",
    "Il souffrait de jalousie constamment.",
    "Elle ne l'aimait pas de la meme facon.",
    "Il voulait savoir ou elle allait.",
    "Ses doutes le rendaient malheureux.",
    "Albertine etait mysterieuse et changeante.",
    "Je ne pouvais pas la comprendre vraiment.",
    "Elle partait souvent sans me dire pourquoi.",
    "Je sentais qu'elle me cachait quelque chose.",
    "Mon desir grandissait avec la distance.",
    "Le souvenir transforme toute chose.",
    "Je cherchais le temps perdu dans ma memoire.",
    "L'art peut sauver ce qui disparait.",
    "Bergotte ecrivait des phrases magnifiques.",
    "Je voulais devenir ecrivain comme lui.",
    "La beaute existe dans les petites choses.",
    "Nous vivons dans nos souvenirs autant que maintenant.",
    "Le passe n'est jamais vraiment mort.",
]

CORPUS_SAINT_EXUPERY = [
    # Le Petit Prince (30 phrases)
    "Le petit prince vivait sur une petite planete.",
    "Il aimait beaucoup sa rose.",
    "Elle etait unique pour lui.",
    "Il en prenait soin tous les jours.",
    "La rose etait un peu capricieuse.",
    "Elle voulait qu'il la protege du vent.",
    "Le petit prince a decide de partir.",
    "Il voulait voir d'autres mondes.",
    "Il a rencontre un roi sur une planete.",
    "Le roi voulait commander tout le monde.",
    "Le petit prince ne comprenait pas pourquoi.",
    "Sur une autre planete vivait un vaniteux.",
    "Il voulait que tout le monde l'admire.",
    "Le petit prince trouvait cela tres etrange.",
    "Il a vu un buveur qui buvait pour oublier.",
    "L'homme avait honte de boire.",
    "Le petit prince etait triste pour lui.",
    "Un businessman comptait les etoiles.",
    "Il pensait qu'elles lui appartenaient.",
    "Le petit prince ne voyait pas l'interet.",
    "Le renard lui a appris un secret important.",
    "On ne voit bien qu'avec le coeur.",
    "L'essentiel est invisible pour les yeux.",
    "Le petit prince a compris qu'il aimait sa rose.",
    "Il devait retourner pour s'occuper d'elle.",
    "Le temps qu'on perd avec quelqu'un le rend important.",
    "Tu deviens responsable de ce que tu apprivoises.",
    "Le petit prince voulait rentrer chez lui.",
    "Il savait que sa rose l'attendait.",
    "L'amour donne du sens a notre vie.",
]

# =============================================================================
# FONCTIONS D'ANALYSE
# =============================================================================

def analyser_corpus(corpus: list, nom: str) -> dict:
    """Analyse complete d'un corpus"""
    print(f"\n{'='*70}")
    print(f"ANALYSE : {nom}")
    print(f"{'='*70}\n")
    
    recon = ReconstructeurGreimasNSM()
    
    stats = {
        'nom': nom,
        'nb_phrases': len(corpus),
        'concepts_trouves': [],
        'primitives_utilisees': Counter(),
        'molecules_utilisees': Counter(),
        'composes_utilises': Counter(),
        'isotopies': Counter(),
        'temps_total': 0.0,
        'phrases_analysees': 0,
        'erreurs': []
    }
    
    start_time = time.time()
    
    for i, phrase in enumerate(corpus, 1):
        try:
            # Analyse de la phrase
            resultat = recon.analyser_texte(phrase)
            
            # Collecte statistiques
            if 'concepts' in resultat:
                stats['concepts_trouves'].extend(resultat['concepts'])
            
            if 'primitives_utilisees' in resultat:
                for prim in resultat['primitives_utilisees']:
                    stats['primitives_utilisees'][prim] += 1
            
            # Detection isotopies
            isotopies = recon.detecter_isotopies(phrase)
            for concept, freq in isotopies.items():
                stats['isotopies'][concept] += freq
            
            stats['phrases_analysees'] += 1
            
            # Affichage progression
            if i % 10 == 0:
                print(f"  [{i}/{len(corpus)}] phrases analysees...")
                
        except Exception as e:
            stats['erreurs'].append((i, phrase, str(e)))
            print(f"  ERREUR phrase {i}: {e}")
    
    stats['temps_total'] = time.time() - start_time
    
    # Calcul statistiques finales
    stats['concepts_uniques'] = len(set(stats['concepts_trouves']))
    stats['primitives_uniques'] = len(stats['primitives_utilisees'])
    stats['temps_moyen'] = stats['temps_total'] / stats['nb_phrases'] if stats['nb_phrases'] > 0 else 0
    
    return stats

def afficher_rapport(stats: dict):
    """Affiche un rapport detaille des statistiques"""
    print(f"\n{'-'*70}")
    print(f"RAPPORT : {stats['nom']}")
    print(f"{'-'*70}\n")
    
    print(f"Phrases analysees    : {stats['phrases_analysees']}/{stats['nb_phrases']}")
    print(f"Concepts trouves     : {len(stats['concepts_trouves'])} total, {stats['concepts_uniques']} uniques")
    print(f"Primitives utilisees : {stats['primitives_uniques']} differentes")
    print(f"Temps total          : {stats['temps_total']:.3f}s")
    print(f"Temps moyen/phrase   : {stats['temps_moyen']*1000:.2f}ms")
    
    if stats['erreurs']:
        print(f"\nERREURS              : {len(stats['erreurs'])}")
        for i, phrase, err in stats['erreurs'][:3]:
            print(f"  - Phrase {i}: {err[:50]}...")
    
    # Top 10 primitives
    print(f"\nTOP 10 PRIMITIVES:")
    for prim, count in stats['primitives_utilisees'].most_common(10):
        print(f"  {prim:20} : {count:3} fois")
    
    # Top 10 isotopies
    if stats['isotopies']:
        print(f"\nTOP 10 ISOTOPIES (themes recurrents):")
        for concept, freq in stats['isotopies'].most_common(10):
            print(f"  {concept:20} : {freq:3} occurrences")

def comparer_corpus(all_stats: list):
    """Compare les statistiques entre differents corpus"""
    print(f"\n{'='*70}")
    print("COMPARAISON INTER-CORPUS")
    print(f"{'='*70}\n")
    
    # Tableau comparatif
    print(f"{'Auteur':<20} | {'Phrases':>8} | {'Concepts':>8} | {'Primitives':>10} | {'Temps (ms)':>11}")
    print(f"{'-'*70}")
    
    for stats in all_stats:
        print(f"{stats['nom']:<20} | {stats['phrases_analysees']:>8} | {stats['concepts_uniques']:>8} | "
              f"{stats['primitives_uniques']:>10} | {stats['temps_moyen']*1000:>10.2f}")
    
    # Primitives communes vs specifiques
    print(f"\n{'='*70}")
    print("ANALYSE DES PRIMITIVES")
    print(f"{'='*70}\n")
    
    all_primitives = set()
    for stats in all_stats:
        all_primitives.update(stats['primitives_utilisees'].keys())
    
    print(f"Total primitives utilisees : {len(all_primitives)}/61")
    
    # Primitives communes a tous
    common_primitives = set(all_stats[0]['primitives_utilisees'].keys())
    for stats in all_stats[1:]:
        common_primitives &= set(stats['primitives_utilisees'].keys())
    
    print(f"Primitives communes        : {len(common_primitives)}")
    print(f"Exemples : {', '.join(list(common_primitives)[:10])}")
    
    # Isotopies par auteur
    print(f"\n{'='*70}")
    print("ISOTOPIES CARACTERISTIQUES PAR AUTEUR")
    print(f"{'='*70}\n")
    
    for stats in all_stats:
        print(f"\n{stats['nom']} (top 5):")
        for concept, freq in stats['isotopies'].most_common(5):
            print(f"  - {concept:20} : {freq} fois")

# =============================================================================
# TESTS PRINCIPAUX
# =============================================================================

def test_corpus_camus():
    """Test sur L'Etranger de Camus"""
    stats = analyser_corpus(CORPUS_CAMUS, "Albert Camus - L'Etranger")
    afficher_rapport(stats)
    
    # Validations specifiques
    assert stats['phrases_analysees'] == 25, "Toutes les phrases doivent etre analysees"
    assert stats['primitives_uniques'] >= 5, "Au moins 5 primitives differentes"
    assert stats['temps_moyen'] < 0.5, "Temps moyen < 500ms par phrase"
    
    print("\n✓ Test Camus reussi")
    return stats

def test_corpus_hugo():
    """Test sur Les Miserables de Hugo"""
    stats = analyser_corpus(CORPUS_HUGO, "Victor Hugo - Les Miserables")
    afficher_rapport(stats)
    
    # Validations specifiques
    assert stats['phrases_analysees'] == 25
    assert stats['primitives_uniques'] >= 5
    assert stats['temps_moyen'] < 0.5
    
    # Verification isotopies (simplifie)
    assert len(stats['isotopies']) > 0, "Au moins une isotopie detectee"
    
    print("\n✓ Test Hugo reussi")
    return stats

def test_corpus_proust():
    """Test sur A la recherche du temps perdu"""
    stats = analyser_corpus(CORPUS_PROUST, "Marcel Proust - Le Temps Perdu")
    afficher_rapport(stats)
    
    # Validations specifiques
    assert stats['phrases_analysees'] == 25
    assert stats['primitives_uniques'] >= 5
    assert stats['temps_moyen'] < 0.5
    
    # Verification isotopies (simplifie)
    assert len(stats['isotopies']) > 0, "Au moins une isotopie detectee"
    
    print("\n✓ Test Proust reussi")
    return stats

def test_corpus_saint_exupery():
    """Test sur Le Petit Prince"""
    stats = analyser_corpus(CORPUS_SAINT_EXUPERY, "Saint-Exupery - Le Petit Prince")
    afficher_rapport(stats)
    
    # Validations specifiques
    assert stats['phrases_analysees'] == 30
    assert stats['primitives_uniques'] >= 5
    assert stats['temps_moyen'] < 0.5
    
    # Verification isotopies (simplifie)
    assert len(stats['isotopies']) > 0, "Au moins une isotopie detectee"
    
    print("\n✓ Test Saint-Exupery reussi")
    return stats

def test_corpus_complet():
    """Test sur l'ensemble du corpus (105 phrases)"""
    print(f"\n{'#'*70}")
    print("TEST CORPUS LITTERAIRE COMPLET")
    print(f"{'#'*70}\n")
    
    all_stats = []
    
    # Analyse chaque corpus
    all_stats.append(test_corpus_camus())
    all_stats.append(test_corpus_hugo())
    all_stats.append(test_corpus_proust())
    all_stats.append(test_corpus_saint_exupery())
    
    # Comparaison inter-corpus
    comparer_corpus(all_stats)
    
    # Statistiques globales
    total_phrases = sum(s['phrases_analysees'] for s in all_stats)
    total_temps = sum(s['temps_total'] for s in all_stats)
    total_concepts = sum(s['concepts_uniques'] for s in all_stats)
    
    print(f"\n{'='*70}")
    print("STATISTIQUES GLOBALES")
    print(f"{'='*70}\n")
    print(f"Total phrases analysees : {total_phrases}")
    print(f"Total concepts uniques  : {total_concepts}")
    print(f"Temps total             : {total_temps:.3f}s")
    print(f"Temps moyen global      : {(total_temps/total_phrases)*1000:.2f}ms/phrase")
    
    # Validation finale
    assert total_phrases == 105, "105 phrases attendues"
    assert total_temps < 60, "Moins de 60s pour tout le corpus"
    
    print(f"\n{'#'*70}")
    print("✓✓✓ TOUS LES TESTS CORPUS REUSSIS ✓✓✓")
    print(f"{'#'*70}\n")

# =============================================================================
# EXECUTION
# =============================================================================

if __name__ == "__main__":
    test_corpus_complet()
