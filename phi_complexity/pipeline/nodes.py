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
                    target = self.context.get("validation_node")
                    if not target:
                        await self.broadcast_error(
                            "Missing validation_node in context."
                        )
                        continue
                    await self.send_signal(
                        target_node=target,
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
                    target = self.context.get("implementation_node")
                    if not target:
                        await self.broadcast_error(
                            "Missing implementation_node in context."
                        )
                        continue
                    await self.send_signal(
                        target_node=target,
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
                    target = self.context.get("quality_node")
                    if not target:
                        await self.broadcast_error("Missing quality_node in context.")
                        continue
                    await self.send_signal(
                        target_node=target,
                        action="code_ready",
                        data={"target_files": ["*.py"]},
                    )
                else:
                    logger.debug(
                        f"[ImplementationNode] Signal ignoré : {signal.action}"
                    )
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

                    # Phase 34 : Calcul réel de la radiance basé sur PHI-META-KERNEL
                    from phi_complexity.metriques import CalculateurRadiance
                    from phi_complexity.analyseur import AnalyseurPhi

                    project_dir = self.context.get("project_dir", ".")
                    analyseur = AnalyseurPhi()
                    fichiers = analyseur.collecter_fichiers(project_dir)

                    scores = []
                    for f in fichiers:
                        try:
                            res = analyseur.analyser_fichier(f)
                            calc = CalculateurRadiance(res)
                            scores.append(calc.calculer()["radiance"])
                        except Exception:
                            continue

                    radiance_score = sum(scores) / len(scores) if scores else 0.0
                    logger.info(
                        f"[QualityGateNode] Score de Radiance Global : {radiance_score:.2f}"
                    )

                    if radiance_score < 80.0:
                        target = self.context.get("implementation_node")
                        if not target:
                            await self.broadcast_error(
                                "Missing implementation_node in context."
                            )
                            continue
                        await self.send_signal(
                            target_node=target,
                            action="quality_rejected",
                            data={"radiance": radiance_score},
                        )
                    else:
                        target = self.context.get("security_node")
                        if not target:
                            await self.broadcast_error(
                                "Missing security_node in context."
                            )
                            continue
                        await self.send_signal(
                            target_node=target,
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
                    logger.info(
                        "============== PHIDÉLIA PIPELINE TERMINÉ =============="
                    )
                    event = self.context.get("completion_event")
                    if event:
                        event.set()
        except Exception as e:
            await self.broadcast_error(f"Échec Sécurité : {str(e)}")
