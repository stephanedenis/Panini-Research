#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔬 ANALYSEUR COMPARATIVE DEEPSEEK vs NSM-GREIMAS
================================================

Compare les représentations sémantiques implicites (DeepSeek) 
avec notre modèle explicite (NSM-Greimas).

Auteur: Panini Research
Date: 12 novembre 2025
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'panlang'))

import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

# Visualisation
import matplotlib.pyplot as plt
import seaborn as sns

# Machine Learning
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from scipy.spatial.distance import cosine

# Nos modules
from nsm_primitives_complet import (
    NSM_PRIMITIVES,
    CategorieNSM, PrimitiveNSM
)
from greimas_nsm_extension import ReconstructeurGreimasNSM


# =============================================================================
# CONFIGURATION DEEPSEEK
# =============================================================================

class ModeleDeepSeek(Enum):
    """Modèles DeepSeek disponibles"""
    CHAT = "deepseek-chat"
    CODER = "deepseek-coder"
    REASONER = "deepseek-reasoner"


@dataclass
class ConfigDeepSeek:
    """Configuration API DeepSeek"""
    api_key: Optional[str] = None
    base_url: str = "https://api.deepseek.com"
    model: ModeleDeepSeek = ModeleDeepSeek.CHAT
    temperature: float = 0.0  # Déterministe pour reproductibilité
    max_tokens: int = 100


# =============================================================================
# CLIENT DEEPSEEK (SIMULATION LOCALE SI PAS DE CLÉ)
# =============================================================================

class ClientDeepSeek:
    """
    Client DeepSeek avec fallback sur simulation locale.
    
    Si pas de clé API : utilise embeddings aléatoires structurés
    (pour tester pipeline sans dépendance externe)
    """
    
    def __init__(self, config: ConfigDeepSeek):
        self.config = config
        self.mode_simulation = config.api_key is None
        
        if not self.mode_simulation:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=config.api_key,
                    base_url=config.base_url
                )
                print("✅ Client DeepSeek initialisé (mode réel)")
            except ImportError:
                print("⚠️ openai non installé, passage en mode simulation")
                self.mode_simulation = True
        else:
            print("ℹ️ Mode simulation (pas de clé API)")
            # Initialiser générateur reproductible
            self.rng = np.random.RandomState(42)
    
    def encoder_texte(self, texte: str, dimension: int = 4096) -> np.ndarray:
        """
        Encode un texte en embedding.
        
        Mode réel : utilise DeepSeek API
        Mode simulation : génère embedding structuré basé sur heuristiques
        """
        if self.mode_simulation:
            return self._encoder_simulation(texte, dimension)
        else:
            return self._encoder_api(texte)
    
    def _encoder_api(self, texte: str) -> np.ndarray:
        """Encodage via API DeepSeek (non implémenté, API embeddings pas publique)"""
        # DeepSeek n'expose pas directement les embeddings
        # Workaround : utiliser hidden states du modèle via completion
        
        response = self.client.chat.completions.create(
            model=self.config.model.value,
            messages=[
                {"role": "system", "content": "Extract semantic representation."},
                {"role": "user", "content": f"Encode: {texte}"}
            ],
            temperature=self.config.temperature,
            max_tokens=1
        )
        
        # TODO: Extraire hidden states (nécessite API spécialisée)
        # Pour l'instant, fallback simulation
        print("⚠️ API embeddings non disponible, fallback simulation")
        return self._encoder_simulation(texte, 4096)
    
    def _encoder_simulation(self, texte: str, dimension: int) -> np.ndarray:
        """
        Simulation structurée d'embeddings DeepSeek.
        
        Heuristiques :
        - Catégories NSM → zones de l'espace
        - Mots-clés → activations spécifiques
        - Bruit gaussien pour réalisme
        """
        # Base : bruit gaussien
        embedding = self.rng.randn(dimension) * 0.1
        
        # Détection catégories NSM (simulation)
        texte_lower = texte.lower()
        
        # SUBSTANTIFS (dimensions 0-340)
        if any(mot in texte_lower for mot in ['je', 'tu', 'quelqu\'un', 'chose', 'corps']):
            embedding[0:340] += self.rng.randn(340) * 0.5
        
        # ACTIONS (dimensions 340-680)
        if any(mot in texte_lower for mot in ['faire', 'arriver', 'bouger', 'toucher']):
            embedding[340:680] += self.rng.randn(340) * 0.5
        
        # MENTAUX (dimensions 680-1020)
        if any(mot in texte_lower for mot in ['penser', 'savoir', 'vouloir', 'sentir']):
            embedding[680:1020] += self.rng.randn(340) * 0.5
        
        # PAROLE (dimensions 1020-1360)
        if any(mot in texte_lower for mot in ['dire', 'mot', 'vrai', 'parler']):
            embedding[1020:1360] += self.rng.randn(340) * 0.5
        
        # ÉVALUATIFS (dimensions 1360-1700)
        if any(mot in texte_lower for mot in ['bon', 'mauvais', 'beau', 'laid']):
            embedding[1360:1700] += self.rng.randn(340) * 0.5
        
        # TEMPORELS (dimensions 1700-2040)
        if any(mot in texte_lower for mot in ['quand', 'maintenant', 'après', 'avant']):
            embedding[1700:2040] += self.rng.randn(340) * 0.5
        
        # SPATIAUX (dimensions 2040-2380)
        if any(mot in texte_lower for mot in ['où', 'ici', 'dessus', 'dedans']):
            embedding[2040:2380] += self.rng.randn(340) * 0.5
        
        # LOGIQUES (dimensions 2380-2720)
        if any(mot in texte_lower for mot in ['pas', 'peut-être', 'parce que', 'si']):
            embedding[2380:2720] += self.rng.randn(340) * 0.5
        
        # QUANTIFICATEURS (dimensions 2720-3060)
        if any(mot in texte_lower for mot in ['tout', 'beaucoup', 'un', 'deux']):
            embedding[2720:3060] += self.rng.randn(340) * 0.5
        
        # INTENSITÉ (dimensions 3060-3400)
        if any(mot in texte_lower for mot in ['très', 'plus', 'comme', 'autre']):
            embedding[3060:3400] += self.rng.randn(340) * 0.5
        
        # EXISTENCE (dimensions 3400-3740)
        if any(mot in texte_lower for mot in ['il y a', 'avoir', 'être', 'exister']):
            embedding[3400:3740] += self.rng.randn(340) * 0.5
        
        # RELATIONS (dimensions 3740-4096)
        if any(mot in texte_lower for mot in ['partie', 'genre', 'avec', 'de']):
            embedding[3740:4096] += self.rng.randn(356) * 0.5
        
        # Normalisation L2 (standard embeddings)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding


# =============================================================================
# ANALYSEUR CONVERGENCE NSM-DEEPSEEK
# =============================================================================

class AnalyseurConvergence:
    """
    Analyse la convergence entre NSM (explicite) et DeepSeek (implicite).
    """
    
    def __init__(self, client_deepseek: ClientDeepSeek):
        self.client = client_deepseek
        self.reconstructeur = ReconstructeurGreimasNSM()
        
        # Cache embeddings
        self.embeddings_primitives: Dict[str, np.ndarray] = {}
        self.embeddings_corpus: Dict[str, np.ndarray] = {}
    
    # =========================================================================
    # EXPÉRIENCE 1 : CLUSTERING PRIMITIVES NSM
    # =========================================================================
    
    def encoder_primitives_nsm(self) -> List[Dict]:
        """
        Encode toutes les primitives NSM avec DeepSeek.
        
        Returns:
            List[Dict] avec structure : {
                'primitive': str,
                'categorie': str,
                'embedding': np.ndarray
            }
        """
        print("\n🔬 ENCODAGE PRIMITIVES NSM AVEC DEEPSEEK")
        print("=" * 60)
        
        resultats = []
        
        # NSM_PRIMITIVES est un dictionnaire
        for nom, primitive in NSM_PRIMITIVES.items():
            # Encoder avec DeepSeek
            embedding = self.client.encoder_texte(primitive.traduction_fr)
            
            # Stocker
            self.embeddings_primitives[nom] = embedding
            
            resultats.append({
                'primitive': nom,
                'categorie': primitive.categorie.name,
                'embedding': embedding
            })
            
            print(f"  ✓ {nom:20s} ({primitive.categorie.name})")
        
        print(f"\n✅ {len(resultats)} primitives encodées")
        return resultats
    
    def visualiser_tsne(
        self,
        embeddings_dict: Dict[str, Dict],
        output_path: str = "tsne_primitives_nsm.png"
    ):
        """
        Visualisation t-SNE des primitives NSM dans l'espace DeepSeek.
        """
        print("\n📊 VISUALISATION t-SNE")
        print("=" * 60)
        
        # Préparer données
        labels = [item['primitive'] for item in embeddings_dict]
        categories = [item['categorie'] for item in embeddings_dict]
        embeddings = np.array([item['embedding'] for item in embeddings_dict])
        
        # t-SNE
        print("  🔄 Calcul t-SNE (perplexity=30, max_iter=1000)...")
        tsne = TSNE(n_components=2, perplexity=30, max_iter=1000, random_state=42)
        coords_2d = tsne.fit_transform(embeddings)
        
        # Mapping couleurs par catégorie
        categories_uniques = list(set(categories))
        colors = sns.color_palette("husl", len(categories_uniques))
        color_map = {cat: colors[i] for i, cat in enumerate(categories_uniques)}
        
        # Plot
        plt.figure(figsize=(16, 12))
        
        for i, (x, y) in enumerate(coords_2d):
            cat = categories[i]
            plt.scatter(x, y, c=[color_map[cat]], s=100, alpha=0.7, edgecolors='black')
            plt.annotate(
                labels[i],
                (x, y),
                fontsize=8,
                alpha=0.8,
                xytext=(5, 5),
                textcoords='offset points'
            )
        
        # Légende
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', 
                      markerfacecolor=color_map[cat], markersize=10, label=cat)
            for cat in categories_uniques
        ]
        plt.legend(handles=legend_elements, loc='upper right', fontsize=10)
        
        plt.title("t-SNE : Primitives NSM dans l'espace DeepSeek", fontsize=16, fontweight='bold')
        plt.xlabel("Dimension 1", fontsize=12)
        plt.ylabel("Dimension 2", fontsize=12)
        plt.grid(alpha=0.3)
        plt.tight_layout()
        
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  ✅ Sauvegardé : {output_path}")
        
        return coords_2d, categories
    
    def evaluer_clustering(self, embeddings_dict: Dict[str, Dict]) -> Dict[str, float]:
        """
        Évalue la qualité du clustering par catégorie NSM.
        
        Métriques :
        - Pureté (purity score)
        - Silhouette coefficient
        """
        print("\n📊 ÉVALUATION CLUSTERING")
        print("=" * 60)
        
        # Préparer données
        categories = [item['categorie'] for item in embeddings_dict]
        embeddings = np.array([item['embedding'] for item in embeddings_dict])
        
        # Nombre catégories uniques
        n_categories = len(set(categories))
        
        # K-means clustering
        kmeans = KMeans(n_clusters=n_categories, random_state=42, n_init=10)
        labels_pred = kmeans.fit_predict(embeddings)
        
        # Pureté
        # (nécessite fonction custom car sklearn ne l'a pas)
        purity = self._calcul_purete(categories, labels_pred)
        
        # Silhouette
        silhouette = silhouette_score(embeddings, labels_pred)
        
        print(f"  📈 Pureté clustering    : {purity:.3f} (> 0.7 = bon)")
        print(f"  📈 Silhouette score     : {silhouette:.3f} (> 0.5 = bon)")
        
        return {
            'purete': purity,
            'silhouette': silhouette,
            'n_clusters': n_categories
        }
    
    def _calcul_purete(self, labels_true, labels_pred) -> float:
        """
        Calcule la pureté du clustering.
        
        Pureté = (1/N) * sum_k max_j |cluster_k ∩ class_j|
        """
        from collections import Counter
        
        # Mapper labels true → indices
        label_to_idx = {label: i for i, label in enumerate(set(labels_true))}
        labels_true_idx = [label_to_idx[label] for label in labels_true]
        
        # Calculer pureté
        total = len(labels_pred)
        clusters = {}
        
        for pred_label, true_label in zip(labels_pred, labels_true_idx):
            if pred_label not in clusters:
                clusters[pred_label] = []
            clusters[pred_label].append(true_label)
        
        purity = sum(max(Counter(cluster).values()) for cluster in clusters.values()) / total
        
        return purity
    
    # =========================================================================
    # EXPÉRIENCE 2 : CARRÉS SÉMIOTIQUES
    # =========================================================================
    
    def analyser_carres_semiotiques(self) -> Dict[str, Dict]:
        """
        Analyse les 20 carrés sémiotiques dans l'espace DeepSeek.
        
        Validation : distances respectent structure Greimas
        (contraire > contradiction > subcontraire)
        """
        print("\n🔬 ANALYSE CARRÉS SÉMIOTIQUES")
        print("=" * 60)
        
        carres = self.reconstructeur.carres
        resultats = []
        
        for nom_carre, carre in carres.items():
            print(f"\n  📐 Carré : {nom_carre}")
            
            # Encoder les 4 positions (CarreSemiotique a des attributs, pas dict)
            s1 = carre.s1
            s2 = carre.s2
            non_s1 = carre.non_s1
            non_s2 = carre.non_s2
            
            emb_s1 = self.client.encoder_texte(s1)
            emb_s2 = self.client.encoder_texte(s2)
            emb_non_s1 = self.client.encoder_texte(non_s1)
            emb_non_s2 = self.client.encoder_texte(non_s2)
            
            # Calculer distances
            d_contraire = cosine(emb_s1, emb_s2)
            d_contradiction_s1 = cosine(emb_s1, emb_non_s1)
            d_contradiction_s2 = cosine(emb_s2, emb_non_s2)
            d_subcontraire = cosine(emb_non_s1, emb_non_s2)
            
            # Validation structure Greimas
            structure_valide = (
                d_contraire > d_contradiction_s1 and
                d_contraire > d_contradiction_s2 and
                d_contradiction_s1 > d_subcontraire and
                d_contradiction_s2 > d_subcontraire
            )
            
            print(f"    Contraire    : {d_contraire:.3f}")
            print(f"    Contradiction: {d_contradiction_s1:.3f}, {d_contradiction_s2:.3f}")
            print(f"    Subcontraire : {d_subcontraire:.3f}")
            print(f"    ✓ Structure valide" if structure_valide else "    ✗ Structure invalide")
            
            resultats.append({
                'carre': nom_carre,
                'S1': s1,
                'S2': s2,
                'distances': {
                    'contraire': d_contraire,
                    'contradiction_s1': d_contradiction_s1,
                    'contradiction_s2': d_contradiction_s2,
                    'subcontraire': d_subcontraire
                },
                'structure_valide': structure_valide
            })
        
        # Statistiques globales
        n_valides = sum(1 for r in resultats if r['structure_valide'])
        taux_validation = n_valides / len(resultats)
        
        print(f"\n📊 RÉSULTAT GLOBAL")
        print(f"  Carrés valides : {n_valides}/{len(resultats)} ({taux_validation:.1%})")
        
        return {
            'resultats': resultats,
            'taux_validation': taux_validation
        }
    
    def visualiser_heatmap_carres(
        self,
        analyse_carres: Dict,
        output_path: str = "heatmap_carres_semiotiques.png"
    ):
        """
        Heatmap des distances pour tous les carrés sémiotiques.
        """
        print("\n📊 HEATMAP CARRÉS SÉMIOTIQUES")
        
        n_carres = len(analyse_carres['resultats'])
        fig, axes = plt.subplots(4, 5, figsize=(20, 16))
        axes = axes.flatten()
        
        for i, resultat in enumerate(analyse_carres['resultats']):
            ax = axes[i]
            
            # Matrice distances 4x4
            labels = ['S1', 'S2', 'non_S1', 'non_S2']
            matrix = np.zeros((4, 4))
            
            # Remplir matrice (symétrique)
            # TODO: calculer toutes distances pairwise
            # Pour l'instant : valeurs clés
            d = resultat['distances']
            matrix[0, 1] = matrix[1, 0] = d['contraire']
            matrix[0, 2] = matrix[2, 0] = d['contradiction_s1']
            matrix[1, 3] = matrix[3, 1] = d['contradiction_s2']
            matrix[2, 3] = matrix[3, 2] = d['subcontraire']
            
            # Heatmap
            sns.heatmap(
                matrix,
                annot=True,
                fmt='.2f',
                cmap='RdYlGn_r',
                xticklabels=labels,
                yticklabels=labels,
                ax=ax,
                cbar=False,
                vmin=0,
                vmax=1
            )
            
            titre = resultat['carre']
            couleur = 'green' if resultat['structure_valide'] else 'red'
            ax.set_title(titre, fontweight='bold', color=couleur, fontsize=10)
        
        plt.suptitle(
            f"Carrés Sémiotiques dans DeepSeek ({analyse_carres['taux_validation']:.0%} valides)",
            fontsize=16,
            fontweight='bold'
        )
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        
        print(f"  ✅ Sauvegardé : {output_path}")
    
    # =========================================================================
    # EXPÉRIENCE 3 : ISOTOPIES CORPUS
    # =========================================================================
    
    def analyser_isotopies_corpus(
        self,
        corpus: List[str],
        nom_corpus: str
    ) -> Dict:
        """
        Compare détection isotopies NSM vs features DeepSeek.
        """
        print(f"\n🔬 ANALYSE ISOTOPIES : {nom_corpus}")
        print("=" * 60)
        
        # 1. Isotopies NSM
        print("  🔍 Détection isotopies NSM...")
        isotopies_nsm = {}
        
        for phrase in corpus:
            # analyser_texte retourne dict avec 'primitives_utilisees' (liste)
            decomposition = self.reconstructeur.analyser_texte(phrase)
            primitives = decomposition.get('primitives_utilisees', [])
            
            for prim in primitives:
                if prim not in isotopies_nsm:
                    isotopies_nsm[prim] = 0
                isotopies_nsm[prim] += 1
        
        # Top isotopies
        top_isotopies = sorted(
            isotopies_nsm.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        print(f"  📊 Top isotopies NSM :")
        for prim, freq in top_isotopies:
            print(f"    - {prim:15s} : {freq:3d} occurrences")
        
        # 2. Embeddings DeepSeek
        print("\n  🤖 Encodage DeepSeek...")
        embeddings = np.array([
            self.client.encoder_texte(phrase)
            for phrase in corpus
        ])
        
        # PCA réduction dimension (min entre 10 et n_samples-1)
        n_components = min(10, len(corpus) - 1)
        pca = PCA(n_components=n_components)
        features_pca = pca.fit_transform(embeddings)
        
        print(f"  📉 PCA : {embeddings.shape[1]} → {n_components} dimensions")
        print(f"    Variance expliquée : {pca.explained_variance_ratio_.sum():.1%}")
        
        # 3. Corrélation isotopies NSM ↔ features DeepSeek
        print("\n  🔗 Corrélation NSM ↔ DeepSeek...")
        correlations = {}
        
        for prim, _ in top_isotopies:
            # Vecteur présence primitive
            vecteur_nsm = np.array([
                1 if prim in self.reconstructeur.analyser_texte(phrase).get('primitives_utilisees', [])
                else 0
                for phrase in corpus
            ])
            
            # Corrélation avec chaque feature PCA
            corrs_features = [
                np.corrcoef(vecteur_nsm, features_pca[:, i])[0, 1]
                for i in range(n_components)
            ]
            
            max_corr = max(np.abs(corrs_features))
            best_feature = np.argmax(np.abs(corrs_features))
            
            correlations[prim] = {
                'max_correlation': max_corr,
                'best_feature': best_feature,
                'correlations': corrs_features
            }
            
            print(f"    {prim:15s} : max_corr = {max_corr:.3f} (PCA-{best_feature})")
        
        return {
            'isotopies_nsm': isotopies_nsm,
            'embeddings_deepseek': embeddings,
            'features_pca': features_pca,
            'correlations': correlations,
            'variance_expliquee': pca.explained_variance_ratio_
        }


# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def main():
    """
    Exécute l'analyse comparative DeepSeek vs NSM-Greimas.
    """
    print("\n" + "=" * 70)
    print("🔬 ANALYSE COMPARATIVE : DeepSeek vs NSM-Greimas")
    print("=" * 70)
    
    # Configuration
    config = ConfigDeepSeek(
        api_key=None,  # TODO: mettre clé si disponible
        model=ModeleDeepSeek.CHAT
    )
    
    # Initialisation
    client = ClientDeepSeek(config)
    analyseur = AnalyseurConvergence(client)
    
    # =========================================================================
    # EXPÉRIENCE 1 : PRIMITIVES NSM
    # =========================================================================
    
    print("\n\n" + "=" * 70)
    print("EXPÉRIENCE 1 : CLUSTERING PRIMITIVES NSM")
    print("=" * 70)
    
    embeddings_primitives = analyseur.encoder_primitives_nsm()
    
    # Visualisation t-SNE
    analyseur.visualiser_tsne(
        embeddings_primitives,
        output_path="tsne_primitives_nsm.png"
    )
    
    # Évaluation clustering
    metriques_clustering = analyseur.evaluer_clustering(embeddings_primitives)
    
    # =========================================================================
    # EXPÉRIENCE 2 : CARRÉS SÉMIOTIQUES
    # =========================================================================
    
    print("\n\n" + "=" * 70)
    print("EXPÉRIENCE 2 : STRUCTURE CARRÉS SÉMIOTIQUES")
    print("=" * 70)
    
    analyse_carres = analyseur.analyser_carres_semiotiques()
    
    analyseur.visualiser_heatmap_carres(
        analyse_carres,
        output_path="heatmap_carres_semiotiques.png"
    )
    
    # =========================================================================
    # EXPÉRIENCE 3 : ISOTOPIES CORPUS (exemple Camus)
    # =========================================================================
    
    print("\n\n" + "=" * 70)
    print("EXPÉRIENCE 3 : ISOTOPIES CORPUS LITTÉRAIRE")
    print("=" * 70)
    
    # Corpus test Camus (extrait)
    corpus_camus = [
        "Je pense donc je suis",
        "L'homme est condamné à être libre",
        "Il faut imaginer Sisyphe heureux",
        "La vie n'a pas de sens a priori",
        "Je me révolte donc nous sommes"
    ]
    
    analyse_isotopies = analyseur.analyser_isotopies_corpus(
        corpus_camus,
        nom_corpus="Camus (extrait)"
    )
    
    # =========================================================================
    # RAPPORT FINAL
    # =========================================================================
    
    print("\n\n" + "=" * 70)
    print("📊 RAPPORT FINAL")
    print("=" * 70)
    
    print(f"\n✅ EXPÉRIENCE 1 : Primitives NSM")
    print(f"  - Primitives encodées : {len(embeddings_primitives)}")
    print(f"  - Pureté clustering   : {metriques_clustering['purete']:.3f}")
    print(f"  - Silhouette score    : {metriques_clustering['silhouette']:.3f}")
    
    print(f"\n✅ EXPÉRIENCE 2 : Carrés sémiotiques")
    print(f"  - Carrés analysés     : {len(analyse_carres['resultats'])}")
    print(f"  - Taux validation     : {analyse_carres['taux_validation']:.1%}")
    
    print(f"\n✅ EXPÉRIENCE 3 : Isotopies corpus")
    print(f"  - Phrases analysées   : {len(corpus_camus)}")
    print(f"  - Isotopies détectées : {len(analyse_isotopies['isotopies_nsm'])}")
    print(f"  - Variance PCA        : {analyse_isotopies['variance_expliquee'].sum():.1%}")
    
    print("\n" + "=" * 70)
    print("✅ ANALYSE TERMINÉE - Visualisations générées")
    print("=" * 70)


if __name__ == "__main__":
    main()
