import asyncio
import json
import time
import logging
from typing import Dict, Any, Optional, Callable, Awaitable

# Configuration du module de logs
logger = logging.getLogger("phi_pipeline")
logger.setLevel(logging.INFO)
# Éviter de dupliquer les handlers si le logger racine est déjà configuré
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )
    logger.addHandler(ch)


class PipelineSignal:
    """Structure de communication formelle (JSON synapsique) entre les nodes."""

    def __init__(self, action: str, issuer: str, data: Optional[Dict[str, Any]] = None):
        self.action = action  # e.g., 'approved', 'rejected', 'issues'
        self.issuer = issuer  # e.g., 'QualityGateNode'
        self.data = data or {}
        self.timestamp = time.time()

    def to_json(self) -> str:
        return json.dumps(
            {
                "action": self.action,
                "issuer": self.issuer,
                "data": self.data,
                "timestamp": self.timestamp,
            }
        )

    @classmethod
    def from_json(cls, payload: str) -> "PipelineSignal":
        try:
            d = json.loads(payload)
            return cls(
                action=d.get("action", "unknown"),
                issuer=d.get("issuer", "unknown"),
                data=d.get("data", {}),
            )
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to decode PipelineSignal JSON: {payload} | Exception: {e}"
            )
            return cls(action="error", issuer="system", data={"raw": payload})


class PipelineNode:
    """Modèle de base abstrait pour un outil d'ingénierie (anciennement appelé 'Agent')."""

    def __init__(self, name: str, pipeline_context: Dict[str, Any]) -> None:
        self.name = name
        self.context = pipeline_context
        # File d'attente asynchrone pour recevoir les signaux (JSON)
        self.inbox: asyncio.Queue[PipelineSignal] = asyncio.Queue()
        self.orchestrator: Optional["PipelineOrchestrator"] = None

    async def send_signal(
        self,
        target_node: Optional["PipelineNode"],
        action: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Transmet un signal structuré au noeud suivant."""
        signal = PipelineSignal(action=action, issuer=self.name, data=data)

        # Interception par le framework pour diagnostic profond
        if self.orchestrator and self.orchestrator.signal_callback:
            await self.orchestrator.signal_callback(signal)

        if target_node is None:
            # Escalation Pattern (Suture bot review)
            error_msg = f"Impossible d'envoyer '{action}' : noeud cible inexistant dans le contexte."
            await self.broadcast_error(error_msg)
            return

        logger.info(f"[{self.name}] -> [{target_node.name}] : {signal.action}")
        await target_node.inbox.put(signal)

    async def broadcast_error(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Diffuse une erreur critique à tous les observateurs via le bus de signaux."""
        data = {"message": message, "details": details or {}}
        signal = PipelineSignal(action="error", issuer=self.name, data=data)
        logger.error(f"[{self.name}] ERREUR CRITIQUE : {message}")

        # Interception par le framework pour diagnostic profond
        if self.orchestrator and self.orchestrator.signal_callback:
            await self.orchestrator.signal_callback(signal)

        # On tente d'envoyer l'erreur au noeud de validation ou directement au moteur
        if "quality_node" in self.context:
            await self.context["quality_node"].inbox.put(signal)

    async def execute(self) -> None:
        """Méthode principale à implémenter par chaque Node spécifique."""
        raise NotImplementedError("Les noeuds doivent implémenter la méthode execute()")


class PipelineOrchestrator:
    """Centralise et exécute les noeuds dans un flux continu et mathématiquement borné."""

    def __init__(self, signal_callback: Optional[Callable[[PipelineSignal], Awaitable[None]]] = None, timeout: float = 10.0) -> None:
        self.nodes: Dict[str, PipelineNode] = {}
        self.completion_event: Optional[asyncio.Event] = None
        self.signal_callback = signal_callback
        self.timeout = timeout
        self.context: Dict[str, Any] = {
            "project_dir": "",
            "concept": "",
            "start_time": None,
        }
        self._is_running = False

    def register_node(self, node: PipelineNode) -> None:
        """Ajoute un noeud au pipeline et lie l'orchestrateur."""
        node.orchestrator = self
        self.nodes[node.name] = node
        logger.info(f"Noeud enregistré dans le pipeline : {node.name}")

    async def run_pipeline(self, concept: str, project_dir: str) -> None:
        """Démarre l'exécution du Phidélia Pipeline."""
        self.completion_event = asyncio.Event()
        self.context["concept"] = concept
        self.context["project_dir"] = project_dir
        self.context["start_time"] = time.time()
        self.context["completion_event"] = self.completion_event
        self._is_running = True

        logger.info("============== PHIDÉLIA PIPELINE INITIÉ ==============")
        logger.info(f"Objectif : {concept}")

        # Résolution de la dépendance circulaire
        from .nodes import (
            SpecificationNode,
            ValidationNode,
            ImplementationNode,
            QualityGateNode,
            SecurityGateNode,
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

        # Signal initial broadcasté à la UI/CLI aussi
        start_signal = PipelineSignal(action="start_planning", issuer="System_Orchestrator")
        if self.signal_callback:
            await self.signal_callback(start_signal)

        # L'étincelle initiale (Lancement du Pipeline)
        await spec_node.inbox.put(start_signal)

        # Attente robuste basée sur un évènement
        try:
            # Simule l'attente du signal de complétion avec ou sans timeout
            await asyncio.wait_for(self.completion_event.wait(), timeout=self.timeout)
            logger.info("[System] Boucle événementielle achevée naturellement.")
        except asyncio.TimeoutError:
            error_signal = PipelineSignal(
                action="error",
                issuer="System_Orchestrator",
                data={"message": "Timeout du pipeline : cycle de test mocké atteint."}
            )
            if self.signal_callback:
                await self.signal_callback(error_signal)
            logger.warning("[System] Arrêt forcé de l'event loop.")

        # Nettoyage gracieux (graceful shutdown)
        for n in self.nodes.values():
            await n.inbox.put(
                PipelineSignal(action="shutdown", issuer="System_Orchestrator")
            )

        # Catch exceptions in tasks to avoid silent failures
        done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED, timeout=2.0)
        for task in done:
            try:
                task.result()
            except Exception as e:
                logger.error(f"Task failure: {e}")
                if self.signal_callback:
                    await self.signal_callback(PipelineSignal(action="error", issuer="System_Orchestrator", data={"message": f"Exception critique : {e}"}))

        self._is_running = False
