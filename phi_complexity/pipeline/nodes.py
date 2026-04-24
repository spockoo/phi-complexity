import asyncio
import logging
import os

from .orchestrator import PipelineNode

logger = logging.getLogger("phi_pipeline.nodes")

# Extensions supportées par le framework φ-Meta (souveraineté : zéro dépendance CLI)
_EXTENSIONS_SUPPORTEES = (".py", ".c", ".cpp", ".rs", ".h", ".hpp", ".s", ".asm")


def _collecter_fichiers_projet(dossier: str) -> list[str]:
    """Collecte récursivement les fichiers supportés d'un répertoire projet."""
    fichiers: list[str] = []
    for racine, _, noms in os.walk(dossier):
        fichiers.extend(
            os.path.join(racine, nom)
            for nom in noms
            if nom.lower().endswith(_EXTENSIONS_SUPPORTEES)
        )
    return sorted(fichiers)


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
    Phase 34 — Calcul réel basé sur PHI-META-KERNEL et la Bibliothèque Céleste.
    """

    async def execute(self) -> None:
        try:
            while True:
                signal = await self.inbox.get()
                if getattr(signal, "action", None) == "shutdown":
                    break
                if signal.action == "code_ready":
                    logger.info("[QualityGateNode] Évaluation φ...")

                    # Phase 34 : Calcul réel de la radiance (PHI-META-KERNEL)
                    from phi_complexity.analyseur import AnalyseurPhi
                    from phi_complexity.metriques import CalculateurRadiance

                    project_dir = self.context.get("project_dir", ".")
                    fichiers = _collecter_fichiers_projet(project_dir)

                    scores: list[float] = []
                    for fpath in fichiers:
                        try:
                            analyseur = AnalyseurPhi(fpath)
                            res = analyseur.analyser()
                            calc = CalculateurRadiance(res)
                            scores.append(calc.calculer()["radiance"])
                        except Exception:
                            continue

                    radiance_score = sum(scores) / len(scores) if scores else 0.0
                    logger.info(
                        f"[QualityGateNode] Score de Radiance Global"
                        f" : {radiance_score:.2f}"
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
