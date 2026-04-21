import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional, Callable

# Configuration du module de logs
logger = logging.getLogger("phi_pipeline")
logger.setLevel(logging.INFO)
# Éviter de dupliquer les handlers si le logger racine est déjà configuré
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    logger.addHandler(ch)


class PipelineSignal:
    """Structure de communication formelle (JSON synapsique) entre les nodes."""
    def __init__(self, action: str, issuer: str, data: Optional[Dict[str, Any]] = None):
        self.action = action  # e.g., 'approved', 'rejected', 'issues'
        self.issuer = issuer  # e.g., 'QualityGateNode'
        self.data = data or {}
        self.timestamp = time.time()

    def to_json(self) -> str:
        return json.dumps({
            "action": self.action,
            "issuer": self.issuer,
            "data": self.data,
            "timestamp": self.timestamp
        })

    @classmethod
    def from_json(cls, payload: str) -> 'PipelineSignal':
        try:
            d = json.loads(payload)
            return cls(
                action=d.get("action", "unknown"),
                issuer=d.get("issuer", "unknown"),
                data=d.get("data", {})
            )
        except json.JSONDecodeError:
            return cls(action="error", issuer="system", data={"raw": payload})


class PipelineNode:
    """Modèle de base abstrait pour un outil d'ingénierie (anciennement appelé 'Agent')."""
    def __init__(self, name: str, pipeline_context: dict):
        self.name = name
        self.context = pipeline_context
        # File d'attente asynchrone pour recevoir les signaux (JSON)
        self.inbox: asyncio.Queue = asyncio.Queue()

    async def send_signal(self, target_node: 'PipelineNode', action: str, data: dict = None):
        """Transmet un signal structuré au noeud suivant."""
        signal = PipelineSignal(action=action, issuer=self.name, data=data)
        logger.info(f"[{self.name}] -> [{target_node.name}] : {signal.action}")
        await target_node.inbox.put(signal)

    async def execute(self):
        """Méthode principale à implémenter par chaque Node spécifique."""
        raise NotImplementedError("Les noeuds doivent implémenter la méthode execute()")


class PipelineOrchestrator:
    """Centralise et exécute les noeuds dans un flux continu et mathématiquement borné."""
    def __init__(self):
        self.nodes: Dict[str, PipelineNode] = {}
        self.context: Dict[str, Any] = {
            "project_dir": "",
            "concept": "",
            "start_time": None
        }
        self._is_running = False

    def register_node(self, node: PipelineNode):
        """Ajoute un noeud au pipeline."""
        self.nodes[node.name] = node
        logger.info(f"Noeud enregistré dans le pipeline : {node.name}")

    async def run_pipeline(self, concept: str, project_dir: str):
        """Démarre l'exécution du Phidélia Pipeline."""
        self.context["concept"] = concept
        self.context["project_dir"] = project_dir
        self.context["start_time"] = time.time()
        self._is_running = True

        logger.info("============== PHIDÉLIA PIPELINE INITIÉ ==============")
        logger.info(f"Objectif : {concept}")
        
        # Résolution de la dépendance circulaire
        from .nodes import (
            SpecificationNode, ValidationNode, ImplementationNode, 
            QualityGateNode, SecurityGateNode
        )
        
        # 1. Initialisation de la Topologie
        spec_node = SpecificationNode("Node-1-Specification", self.context)
        val_node = ValidationNode("Node-2-Validation", self.context)
        impl_node = ImplementationNode("Node-3-Implementation", self.context)
        qual_node = QualityGateNode("Node-4-QualityGate", self.context)
        sec_node = SecurityGateNode("Node-5-SecurityGate", self.context)
        
        # Montage du contexte réseau (qui connait qui)
        self.context["validation_node"] = val_node
        self.context["implementation_node"] = impl_node
        self.context["quality_node"] = qual_node
        self.context["security_node"] = sec_node
        
        for n in [spec_node, val_node, impl_node, qual_node, sec_node]:
            self.register_node(n)
            
        # 2. Lancement des boucles d'inférence en tâche de fond (Swarm)
        tasks = [
            asyncio.create_task(spec_node.execute()),
            asyncio.create_task(val_node.execute()),
            asyncio.create_task(impl_node.execute()),
            asyncio.create_task(qual_node.execute()),
            asyncio.create_task(sec_node.execute()),
        ]
        
        # 3. L'étincelle initiale (Lancement du Pipeline)
        await spec_node.inbox.put(PipelineSignal(action="start_planning", issuer="System_Orchestrator"))
        
        # 4. Attente de résolution (Simulation: attendre 10 secondes puis stopper)
        await asyncio.sleep(8)
        logger.warning("[System] Arrêt simulé de l'event loop pour test factice.")
        
        # Nettoyage
        for task in tasks:
            task.cancel()
        self._is_running = False

