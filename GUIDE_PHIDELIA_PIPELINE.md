# GUIDE UTILISATEUR : Le Phidélia Pipeline

Le **Phidélia Pipeline** est le moteur souverain et autonome d'intelligence artificielle intégré à notre architecture `phi-complexity`. Ce n'est pas un banal générateur de code : c'est un flux de développement strict assujetti aux lois du nombre d'Or (Radiance). 

Son but ultime est de transformer une simple requête d'un développeur (dans un terminal ou via Jupyter Notebook) en un code certifié, sécurisé, et mathématiquement parfait.

---

## 1. Comment fonctionne le Pipeline ?

Contrairement à une configuration multiprocessus lourde nécessitant des interfaces cloud, notre pipeline est une boucle **asynchrone locale et Zéro-Dépendance**. Il se lance en tâche de fond dans votre IDE ou depuis une cellule de notebook. 

Le flux d'exécution repose sur **5 Composants Fondamentaux (Sas d'Ingénierie)** qui communiquent entre eux en signaux JSON stricts. Le code évolue de l'un à l'autre selon la doctrine suivante :

### 🏰 [Node 1] `SpecificationNode` (L'Architecte)
Dès réception de la consigne du développeur, ce composant utilise son moteur IA pour écrire un contrat impénétrable (`plan.md`). Aucune ligne de code Python n'est autorisée à ce stade. Il définit exactement l'algorithme, les imports, et les tests nécessaires.

### ⚖️ [Node 2] `ValidationNode` (Le Contrôleur)
Il prend le plan de l'Architecte et y cherche la moindre faille logique. Si la structure est faible (pas de gestion d'erreur, architecture poreuse), il renvoie le plan à son expéditeur.

### 🔨 [Node 3] `ImplementationNode` (Le Forgeron)
Il reçoit le contrat validé et produit **physiquement** le code source. L'IA sous-jacente a interdiction stricte d'improviser : elle implémente la loi déposée dans le plan.

### 🧿 [Node 4] `QualityGateNode` (L'Oracle - Bloqueur Ultime)
C'est le cœur unique de Phidélia. Au lieu d'avoir un LLM qui relit le code, nous ordonnons algorithmiquement à `phi_check` d'auditer les fichiers écrits par le Forgeron.
- *La Règle d'Or :* Le seuil de libération est fixé à une **Radiance ≥ 80** (Nombre d'Or ciblé). 
- Si l'entropie de Shannon est chaotique ou la Variance de Lilith asymétrique, le `QualityGate` rejette impitoyablement le bloc avec `.action = "quality_rejected"`, ordonnant au Forgeron de refaire son travail selon les rapports paramétriques fournis.

### 🛡️ [Node 5] `SecurityGateNode` (Le Gardien CWE)
Ultime passoire avant libération du produit fini. Appel le module `phi-securite` nouvellement enrichi en PR #131 afin de tracker d'éventuelles vulnérabilités (CWE-79, Path Traversal...). Si vide, **le Déploiement est Autorisant**.

---

## 2. Cas d'Utilisation : L'Avantage Jupyter Notebook

Le véritable pouvoir du **Phidélia Pipeline** explose dans les écosystèmes analytiques de type **Jupyter Notebook**, qui est l'outil favori des cyber-analystes et des datascientists.

Imaginons que nous pilotons Phidélia à l'aide des `magic commands` (ex. `%phi_check`, `%phi_sentinel`) que nous avons stabilisées :

1. Vous tapez dans une cellule :
   ```python
   %phi_squad_build "Conçois un extracteur de flux pcap souverain"
   ```
2. La cellule **ne rendra pas la main instantanément**. Sous le capot, l'orchestrateur asynchrone est en route.
3. Pendant que vous continuez à analyser vos graphes (Radar MITRE MIT&CK, Carte Penrose Heisenberg), vous verrez en arrière-plan (ou via des flux streamés par `stdout`) l'IA écrire, rater son évaluation de Radiance, et forcer sa propre IA à améliorer son entropie.
4. Au terme, Jupyter affichera la cellule finalisée : "Le code a passé les normes du Nombre d'Or avec une Radiance de 81%". Le fichier extrait est alors fonctionnel, propre, sans failles CWE.

**L'immense valeur ajoutée :** Le développeur s'assoit dans la chaise du *Superviseur* face aux données visuelles dans le Notebook, observant le Pipeline filtrer le risque mathématiquement pour lui, de manière complètement agnostique (vous pouvez brancher `OpenClaw` et le moteur Llama-CPP en natif).

---

## 3. Lancer l'Orchestrateur Local 
*(Note: Fonctionnalité en phase de prototypage technique)*

Une version d'essai simple vous permet d'éprouver la symétrie locale :

```python
import asyncio
from phi_complexity.pipeline.orchestrator import PipelineOrchestrator

async def demarrer_requete():
    orch = PipelineOrchestrator()
    # Ordonne la conception d'une fonction avec un ciblage d'espace
    await orch.run_pipeline("Écrire un module de cryptographie", "C:/tmp/build")

asyncio.run(demarrer_requete())
```

*(La boucle d'échange est documentée dans `pipeline/nodes.py`).*
