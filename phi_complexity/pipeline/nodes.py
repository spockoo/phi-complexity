import asyncio
import logging

from .orchestrator import PipelineNode

# Import mathématiques souveraines de phi-complexity
# from phi_complexity.metriques import CalculateurRadiance
# from phi_complexity.securite import verifier_cwe

logger = logging.getLogger("phi_pipeline.nodes")


class SpecificationNode(PipelineNode):
    """
    Rédige le contrat architectural (Anciennement Planner 'A').
    S'assure de l'absence de zones grises.
    """

    async def execute(self) -> None:
        try:
            while True:
                signal = await self.inbox.get()
                if getattr(signal, "action", None) == "shutdown":
                    break
                if signal.action == "start_planning":
                    logger.info("[SpecificationNode] Élaboration du contrat...")
                    await asyncio.sleep(1)
                    await self.send_signal(
                        target_node=self.context.get("validation_node"),
                        action="review_plan",
                        data={"plan_path": "plan.md"},
                    )
                else:
                    logger.debug(f"[SpecificationNode] Signal ignoré : {signal.action}")
        except Exception as e:
            await self.broadcast_error(f"Échec de Spécification : {str(e)}")


class ValidationNode(PipelineNode):
    """
    Challenge le plan (Anciennement Reviewer 'B').
    Renvoie le plan au SpecificationNode tant qu'il n'est pas parfait.
    """

    async def execute(self) -> None:
        try:
            while True:
                signal = await self.inbox.get()
                if getattr(signal, "action", None) == "shutdown":
                    break
                if signal.action == "review_plan":
                    logger.info("[ValidationNode] Analyse du contrat...")
                    await asyncio.sleep(1)
                    await self.send_signal(
                        target_node=self.context.get("implementation_node"),
                        action="approved_plan",
                        data=signal.data,
                    )
                else:
                    logger.debug(f"[ValidationNode] Signal ignoré : {signal.action}")
        except Exception as e:
            await self.broadcast_error(f"Échec de Validation : {str(e)}")


class ImplementationNode(PipelineNode):
    """
    Produit exactement le code imposé par le plan (Anciennement Coder 'C').
    """

    async def execute(self) -> None:
        try:
            while True:
                signal = await self.inbox.get()
                if getattr(signal, "action", None) == "shutdown":
                    break
                if signal.action in ["approved_plan", "quality_rejected"]:
                    logger.info("[ImplementationNode] Synthèse du code...")
                    await asyncio.sleep(1)
                    await self.send_signal(
                        target_node=self.context.get("quality_node"),
                        action="code_ready",
                        data={"target_files": ["*.py"]},
                    )
                else:
                    logger.debug(f"[ImplementationNode] Signal ignoré : {signal.action}")
        except Exception as e:
            await self.broadcast_error(f"Échec d'Implémentation : {str(e)}")


class QualityGateNode(PipelineNode):
    """
    Le Bloqueur Ultime Mathématique (L'Oracle).
    Remplace le testeur incertain par un analyseur déterministe (Radiance >= 80).
    """

    async def execute(self) -> None:
        try:
            while True:
                signal = await self.inbox.get()
                if getattr(signal, "action", None) == "shutdown":
                    break
                if signal.action == "code_ready":
                    logger.info("[QualityGateNode] Évaluation φ...")
                    radiance_score = 100.0  # Mock
                    if radiance_score < 80.0:
                        await self.send_signal(
                            target_node=self.context.get("implementation_node"),
                            action="quality_rejected",
                            data={"radiance": radiance_score},
                        )
                    else:
                        await self.send_signal(
                            target_node=self.context.get("security_node"),
                            action="quality_passed",
                            data=signal.data,
                        )
                else:
                    logger.debug(f"[QualityGateNode] Signal ignoré : {signal.action}")
        except Exception as e:
            await self.broadcast_error(f"Échec Qualité : {str(e)}")


class SecurityGateNode(PipelineNode):
    """
    Le Gardien (Cybersécurité).
    CWE-Auditor du repo the-dev-squad transposé avec le Cerveau de phi-complexity.
    """

    async def execute(self) -> None:
        try:
            while True:
                signal = await self.inbox.get()
                if getattr(signal, "action", None) == "shutdown":
                    break
                if signal.action == "quality_passed":
                    logger.info("[SecurityGateNode] Scan CWE...")
                    logger.info("============== PHIDÉLIA PIPELINE TERMINÉ ==============")
                    event = self.context.get("completion_event")
                    if event:
                        event.set()
        except Exception as e:
            await self.broadcast_error(f"Échec Sécurité : {str(e)}")
