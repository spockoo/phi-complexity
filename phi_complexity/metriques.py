from __future__ import annotations
import math
from typing import List, Dict, Any, Optional

from .core import PHI, TAXE_SUTURE, ETA_GOLDEN, HBAR_PHI, statut_gnostique
from .analyseur import ResultatAnalyse


class CalculateurRadiance:
    """
    Transforme les métriques brutes en Indice de Radiance (0-100).
    Ancrage : AX-A39 (Attracteur Doré) + EQ-AFR-BMAD (Loi Antifragile).
    """

    def __init__(self, resultat: ResultatAnalyse):
        self.r = resultat

    # ────────────────────────────────────────────────────────
    # API PUBLIQUE
    # ────────────────────────────────────────────────────────

    def calculer(self) -> Dict[str, Any]:
        """Orchestre le calcul — délègue tout aux fonctions spécialisées."""
        if not self.r.fonctions:
            return self._resultat_vide()
        brutes = self._extraire_mesures()
        radiance = self._indice_radiance(brutes)
        return self._assembler_resultat(brutes, radiance)

    # ────────────────────────────────────────────────────────
    # EXTRACTION DES MESURES BRUTES (hermétique)
    # ────────────────────────────────────────────────────────

    def _extraire_mesures(self) -> Dict[str, Any]:
        """Extrait toutes les mesures brutes depuis le résultat d'analyse."""
        complexites: List[int] = [f.complexite for f in self.r.fonctions]
        variance = self._variance(complexites)
        entropie = self._entropie_shannon(complexites)
        return {
            "complexites": complexites,
            "lilith_variance": variance,
            "shannon_entropy": entropie,
            "phi_ratio": self._phi_ratio(complexites),
            "fibonacci_distance": sum(f.distance_fib for f in self.r.fonctions),
            "zeta_score": self._zeta_score(complexites),
            "nb_anomalies": len(
                [a for a in self.r.annotations if a.niveau in ("WARNING", "CRITICAL")]
            ),
            "heisenberg": self._heisenberg_phi(variance, entropie),
        }

    # ────────────────────────────────────────────────────────
    # ASSEMBLAGE DU RÉSULTAT (hermétique)
    # ────────────────────────────────────────────────────────

    def _assembler_resultat(
        self, brutes: Dict[str, Any], radiance: float
    ) -> Dict[str, Any]:
        """Construit le dictionnaire final à partir des mesures et du score."""
        phi_ratio = brutes["phi_ratio"]
        from .bmad import OrchestrateurBMAD

        orchestrateur = OrchestrateurBMAD()
        complexite_totale = sum(brutes["complexites"])

        # Phase 11.6 : Alignement Matriciel (Peuplement de la dataclass souveraine)
        self.r.radiance = radiance
        self.r.lilith_variance = float(brutes["lilith_variance"])
        self.r.shannon_entropy = float(brutes["shannon_entropy"])
        self.r.phi_ratio = float(phi_ratio)
        self.r.resistance = orchestrateur.calculer_omega_resistance(
            radiance, complexite_totale
        )
        self.r.signature = f"v{self.r.lilith_variance:.2f}_e{self.r.shannon_entropy:.2f}_p{self.r.phi_ratio:.2f}"

        return {
            "fichier": self.r.fichier,
            "radiance": round(self.r.radiance, 2),
            "statut_gnostique": statut_gnostique(self.r.radiance),
            "lilith_variance": round(self.r.lilith_variance, 3),
            "shannon_entropy": round(self.r.shannon_entropy, 3),
            "phi_ratio": round(self.r.phi_ratio, 3),
            "phi_ratio_delta": round(abs(self.r.phi_ratio - PHI), 3),
            "fibonacci_distance": round(brutes["fibonacci_distance"], 3),
            "zeta_score": round(brutes["zeta_score"], 4),
            "heisenberg_tension": round(brutes["heisenberg"]["tension_quantique"], 4),
            "resistance": round(self.r.resistance, 4),
            "pole_alpha": self.r.pole_alpha,
            "pole_omega": self.r.pole_omega,
            "signature": self.r.signature,
            "nb_fonctions": len(self.r.fonctions),
            "nb_classes": self.r.nb_classes,
            "nb_imports": self.r.nb_imports,
            "nb_lignes_total": self.r.nb_lignes_total,
            "ratio_commentaires": round(
                self.r.nb_commentaires / max(1, self.r.nb_lignes_total), 3
            ),
            "oudjat": self._serialiser_oudjat(),
            "annotations": self._serialiser_annotations(),
        }

    def _serialiser_oudjat(self) -> Optional[Dict[str, Any]]:
        """Sérialise la fonction Oudjat (la plus complexe) en dictionnaire."""
        if not self.r.oudjat:
            return None
        o = self.r.oudjat
        return {
            "nom": o.nom,
            "ligne": o.ligne,
            "complexite": o.complexite,
            "nb_lignes": o.nb_lignes,
            "phi_ratio": round(o.phi_ratio, 3),
        }

    def _serialiser_annotations(self) -> List[Dict[str, Any]]:
        """Sérialise la liste des annotations en dictionnaires."""
        return [
            {
                "ligne": a.ligne,
                "niveau": a.niveau,
                "categorie": a.categorie,
                "message": a.message,
                "extrait": a.extrait,
            }
            for a in self.r.annotations
        ]

    # ────────────────────────────────────────────────────────
    # FORMULE FONDATRICE — INDICE DE RADIANCE
    # ────────────────────────────────────────────────────────

    def _indice_radiance(self, brutes: Dict[str, Any]) -> float:
        """
        R = 100 - f(Lilith) - g(Shannon) - h(Anomalies) - i(Fibonacci)
        Chaque déduction est plafonnée (Loi d'Indulgence).
        Plancher : 40 (Loi Antifragile — EQ-AFR-BMAD).
        """
        score = 100.0
        score -= self._deduction_lilith(brutes["lilith_variance"])
        score -= self._deduction_entropie(brutes["shannon_entropy"])
        score -= self._deduction_anomalies(brutes["nb_anomalies"])
        score -= self._deduction_fibonacci(brutes["fibonacci_distance"])
        return max(40.0, score)

    def _deduction_lilith(self, variance: float) -> float:
        """f(Lilith) = min(25, (σ²_L / seuil) × 25). Seuil naturel = φ² × 100."""
        seuil = PHI**2 * 100
        return min(25.0, (variance / seuil) * 25.0)

    def _deduction_entropie(self, entropie: float) -> float:
        """g(H) = min(20, max(0, H - H_max) × 5). H_max = log₂(φ⁴) ≈ 2.88 bits."""
        seuil = math.log2(PHI**4)
        return min(20.0, max(0.0, entropie - seuil) * 5.0)

    def _deduction_anomalies(self, nb: int) -> float:
        """h(A) = min(30, A × τ_L × 3). τ_L = Taxe de Suture (CM-018)."""
        return min(30.0, nb * TAXE_SUTURE * 3)

    def _deduction_fibonacci(self, distance: float) -> float:
        """i(D_F) = min(10, D_F × η_golden)."""
        return min(10.0, distance * ETA_GOLDEN)

    # ────────────────────────────────────────────────────────
    # FORMULES MATHÉMATIQUES SOUVERAINES (atomiques)
    # ────────────────────────────────────────────────────────

    def _variance(self, valeurs: List[int]) -> float:
        """σ²_L = (1/n) · Σ(κᵢ - μ)². Variance de Lilith."""
        if not valeurs:
            return 0.0
        mean = sum(valeurs) / len(valeurs)
        return sum((v - mean) ** 2 for v in valeurs) / len(valeurs)

    def _entropie_shannon(self, valeurs: List[int]) -> float:
        """H = -Σ pᵢ · log₂(pᵢ). Entropie de Shannon normalisée."""
        if not valeurs:
            return 0.0
        total = sum(valeurs)
        if total == 0:
            return 0.0
        probas = [v / total for v in valeurs]
        return -sum(p * math.log2(p) for p in probas if p > 0)

    def _phi_ratio(self, valeurs: List[int]) -> float:
        """φ-ratio = max(κ) / μ. Doit tendre vers φ = 1.618."""
        if not valeurs or len(valeurs) < 2:
            return 1.0
        mean = sum(valeurs) / len(valeurs)
        return (max(valeurs) / mean) if mean else 1.0

    def _zeta_score(self, valeurs: List[int]) -> float:
        """ζ_meta = min(1, [Σ 1/(i+1)^φ / n] × φ). Résonance globale."""
        if not valeurs:
            return 0.0
        n: int = len(valeurs)
        zeta: float = sum(1.0 / ((i + 1) ** PHI) for i in range(n)) / n
        resultat: float = min(1.0, zeta * PHI)
        return float(resultat)

    def _heisenberg_phi(self, variance: float, entropie: float) -> Dict[str, float]:
        """
        Relation d'incertitude de Heisenberg-Phi (CM-HUP) :
        ΔC · ΔL ≥ ħ_φ / 2

        Où :
          ΔC = sqrt(σ²_L / σ²_max)    — incertitude de complexité normalisée [0, 1]
          ΔL = H_S / H_max            — incertitude de lisibilité normalisée [0, 1]
          ħ_φ = 1/φ ≈ 0.618          — constante d'action réduite dorée
          plancher = ħ_φ / 2 ≈ 0.309 — minimum d'incertitude quantique

        tension_quantique = (ΔC · ΔL) / plancher :
          < 1  → état super-cohérent (code élégamment focalisé)
          ≈ 1  → état cohérent minimal (optimum golden)
          > 1  → zone d'incertitude naturelle (évolution classique)
        """
        sigma_max_sq = PHI**2 * 100          # seuil Lilith = φ² × 100 ≈ 261.8
        h_max = math.log2(PHI**4)            # seuil Shannon = log₂(φ⁴) ≈ 2.88 bits
        plancher = HBAR_PHI / 2              # ħ_φ / 2 ≈ 0.309

        delta_c = math.sqrt(variance / sigma_max_sq) if variance > 0 else 0.0
        delta_l = entropie / h_max if h_max > 0 else 0.0

        produit = delta_c * delta_l
        tension = produit / plancher if plancher > 0 else 0.0

        return {
            "delta_complexite": delta_c,
            "delta_lisibilite": delta_l,
            "produit_incertitude": produit,
            "plancher_hbar": plancher,
            "tension_quantique": tension,
        }

    # ────────────────────────────────────────────────────────
    # RÉSULTAT NEUTRE (fichiers sans fonctions)
    # ────────────────────────────────────────────────────────

    def _resultat_vide(self) -> Dict[str, Any]:
        """Score neutre (60) pour les fichiers de constantes ou de configuration."""
        return {
            "fichier": self.r.fichier,
            "radiance": 60.0,
            "statut_gnostique": statut_gnostique(60.0),
            "lilith_variance": 0.0,
            "shannon_entropy": 0.0,
            "phi_ratio": 1.0,
            "phi_ratio_delta": PHI - 1.0,
            "fibonacci_distance": 0.0,
            "zeta_score": 0.0,
            "heisenberg_tension": 0.0,
            "nb_fonctions": 0,
            "nb_classes": self.r.nb_classes,
            "nb_imports": self.r.nb_imports,
            "nb_lignes_total": self.r.nb_lignes_total,
            "ratio_commentaires": 0.0,
            "oudjat": None,
            "annotations": [],
        }
