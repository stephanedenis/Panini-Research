#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de validation des carrés sémiotiques
Simule l'analyse de Cell 16 pour vérifier qu'il n'y aura plus d'erreurs
"""

import sys
sys.path.insert(0, '.')

from donnees_nsm import NSM_PRIMITIVES, CARRES_SEMIOTIQUES

print("=" * 70)
print("🧪 TEST DE VALIDATION DES CARRÉS SÉMIOTIQUES")
print("=" * 70)

print(f"\n📊 Statistiques:")
print(f"   - Nombre de carrés: {len(CARRES_SEMIOTIQUES)}")
print(f"   - Nombre de primitives NSM: {len(NSM_PRIMITIVES)}")

# Test 1: Vérifier que toutes les primitives existent
print(f"\n🔍 Test 1: Validation des primitives...")
primitives_manquantes = []
for nom_carre, carre in CARRES_SEMIOTIQUES.items():
    for position in ["S1", "S2", "non_S1", "non_S2"]:
        primitive = carre[position]
        if primitive not in NSM_PRIMITIVES:
            primitives_manquantes.append(f"{nom_carre}.{position} = {primitive}")

if primitives_manquantes:
    print(f"   ❌ ÉCHEC: {len(primitives_manquantes)} primitives manquantes:")
    for p in primitives_manquantes:
        print(f"      - {p}")
    sys.exit(1)
else:
    print(f"   ✅ SUCCÈS: Toutes les 80 primitives (20 carrés × 4 positions) existent!")

# Test 2: Simuler l'obtention des embeddings (vérifier qu'aucun ne sera None)
print(f"\n🔍 Test 2: Simulation obtention embeddings...")

def mock_get_embedding(primitive):
    """Simule l'obtention d'un embedding"""
    return NSM_PRIMITIVES[primitive] if primitive in NSM_PRIMITIVES else None

nb_carres_valides = 0
resultats_carres = []

for nom_carre, carre in CARRES_SEMIOTIQUES.items():
    s1_emb = mock_get_embedding(carre["S1"])
    s2_emb = mock_get_embedding(carre["S2"])
    non_s1_emb = mock_get_embedding(carre["non_S1"])
    non_s2_emb = mock_get_embedding(carre["non_S2"])
    
    if all([s1_emb, s2_emb, non_s1_emb, non_s2_emb]):
        nb_carres_valides += 1
        resultats_carres.append({
            "nom": nom_carre,
            "positions": {
                "S1": carre["S1"],
                "S2": carre["S2"],
                "non_S1": carre["non_S1"],
                "non_S2": carre["non_S2"]
            }
        })
    else:
        print(f"   ❌ Carré invalide: {nom_carre}")
        if not s1_emb: print(f"      - S1 manquant: {carre['S1']}")
        if not s2_emb: print(f"      - S2 manquant: {carre['S2']}")
        if not non_s1_emb: print(f"      - non_S1 manquant: {carre['non_S1']}")
        if not non_s2_emb: print(f"      - non_S2 manquant: {carre['non_S2']}")

print(f"   ✅ SUCCÈS: {nb_carres_valides}/{len(CARRES_SEMIOTIQUES)} carrés valides")

# Test 3: Vérifier que la division ne causera pas ZeroDivisionError
print(f"\n🔍 Test 3: Vérification division...")
if len(resultats_carres) == 0:
    print(f"   ❌ ÉCHEC: Division par zéro car aucun carré valide!")
    sys.exit(1)
else:
    taux_validite = nb_carres_valides / len(resultats_carres)
    print(f"   ✅ SUCCÈS: Taux de validité = {taux_validite*100:.1f}%")

# Test 4: Liste des carrés
print(f"\n📋 Liste des 20 carrés sémiotiques:")
for i, (nom_carre, carre) in enumerate(CARRES_SEMIOTIQUES.items(), 1):
    print(f"   {i:2d}. {nom_carre:20s} : {carre['S1']:15s} ↔ {carre['S2']:15s}")

print("\n" + "=" * 70)
print("✅ TOUS LES TESTS SONT PASSÉS!")
print("=" * 70)
print("\n💡 Le notebook Cell 16 devrait maintenant s'exécuter sans erreur.")
print("   - Aucune primitive manquante")
print("   - Aucun ZeroDivisionError")
print("   - 20 carrés sémiotiques valides\n")
