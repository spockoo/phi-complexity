"""
Tests du Pipeline Phidélia — Orchestrateur et Noeuds.

Utilise asyncio.run() au lieu de @pytest.mark.anyio pour garantir
la compatibilité avec les environnements CI sans dépendance asyncio
(souveraineté : zéro dépendance externe pour les tests noyau).
"""

import asyncio
import logging

from phi_complexity.pipeline.orchestrator import (
    PipelineSignal,
    PipelineNode,
    PipelineOrchestrator,
)
from phi_complexity.pipeline.nodes import (
    SpecificationNode,
    ImplementationNode,
    SecurityGateNode,
)


class MockNode(PipelineNode):
    async def execute(self) -> None:
        while True:
            signal = await self.inbox.get()
            if signal.action == "shutdown":
                break
            if signal.action == "ping":
                await self.send_signal(None, "pong")


# ── PipelineSignal ─────────────────────────────────────────────


def test_pipeline_signal_json() -> None:
    """Vérifie la sérialisation/désérialisation des signaux."""

    async def _run() -> None:
        sig = PipelineSignal(action="test", issuer="issuer", data={"key": "val"})
        js = sig.to_json()
        assert '"action": "test"' in js

        sig2 = PipelineSignal.from_json(js)
        assert sig2.action == "test"
        assert sig2.issuer == "issuer"
        assert sig2.data["key"] == "val"

    asyncio.run(_run())


def test_pipeline_signal_invalid_json() -> None:
    """Vérifie la robustesse face aux JSON malformés."""

    async def _run() -> None:
        sig = PipelineSignal.from_json("{invalid}")
        assert sig.action == "error"
        assert sig.issuer == "system"

    asyncio.run(_run())


# ── PipelineNode ───────────────────────────────────────────────


def test_node_send_signal_escalation() -> None:
    """Vérifie que l'envoi vers un noeud inexistant déclenche une erreur."""

    async def _run() -> None:
        context: dict[str, object] = {"quality_node": MockNode("Quality", {})}
        node = MockNode("Tester", context)
        orchestrator = PipelineOrchestrator()
        node.orchestrator = orchestrator

        await node.send_signal(None, "lost_action")

        qual = context["quality_node"]
        assert isinstance(qual, MockNode)
        err_signal = await qual.inbox.get()
        assert err_signal.action == "error"
        assert "inexistant" in err_signal.data["message"]

    asyncio.run(_run())


def test_node_broadcast_error() -> None:
    """Vérifie la diffusion d'erreurs."""

    async def _run() -> None:
        qual_node = MockNode("Quality", {})
        context: dict[str, object] = {"quality_node": qual_node}
        node = MockNode("Worker", context)

        await node.broadcast_error("Explosion")
        sig = await qual_node.inbox.get()
        assert sig.action == "error"
        assert sig.data["message"] == "Explosion"

    asyncio.run(_run())


# ── PipelineOrchestrator ───────────────────────────────────────


def test_orchestrator_registration() -> None:
    """Vérifie l'enregistrement des noeuds."""

    async def _run() -> None:
        orch = PipelineOrchestrator()
        node = MockNode("N1", {})
        orch.register_node(node)
        assert orch.nodes["N1"] == node
        assert node.orchestrator == orch

    asyncio.run(_run())


def test_full_pipeline_cycle() -> None:
    """Vérifie un cycle complet du pipeline (mocké)."""

    async def _run() -> None:
        orch = PipelineOrchestrator(timeout=1.0)
        await orch.run_pipeline("Test Objective", ".")
        assert orch._is_running is False

    asyncio.run(_run())


def test_pipeline_timeout_handling() -> None:
    """Vérifie la gestion des timeouts de l'orchestrateur."""

    async def _run() -> None:
        signals: list[PipelineSignal] = []

        async def cb(s: PipelineSignal) -> None:
            signals.append(s)

        orch = PipelineOrchestrator(signal_callback=cb, timeout=0.1)
        await orch.run_pipeline("Timeout test", ".")

        actions = [s.action for s in signals]
        assert "error" in actions
        timeout_errors = [
            s
            for s in signals
            if s.action == "error" and "Timeout" in s.data.get("message", "")
        ]
        assert len(timeout_errors) > 0

    asyncio.run(_run())


def test_nodes_unhandled_signals(caplog) -> None:  # type: ignore[no-untyped-def]
    """Vérifie que les noeuds loggent les signaux inconnus (Suture)."""

    async def _run() -> None:
        context: dict[str, object] = {}
        node = SpecificationNode("Spec", context)
        await node.inbox.put(PipelineSignal("alien_action", "unknown"))
        await node.inbox.put(PipelineSignal("shutdown", "system"))

        with caplog.at_level(logging.DEBUG, logger="phi_pipeline.nodes"):
            await node.execute()

        assert "Signal ignoré : alien_action" in caplog.text

    asyncio.run(_run())


def test_security_gate_node() -> None:
    """Vérifie le noeud de sécurité."""

    async def _run() -> None:
        event = asyncio.Event()
        context: dict[str, object] = {"completion_event": event}
        node = SecurityGateNode("Security", context)

        await node.inbox.put(PipelineSignal("quality_passed", "tester"))
        await node.inbox.put(PipelineSignal("shutdown", "system"))

        await node.execute()
        assert event.is_set()

    asyncio.run(_run())


def test_implementation_node() -> None:
    """Vérifie le noeud d'implémentation."""

    async def _run() -> None:
        qual_node = MockNode("Quality", {})
        context: dict[str, object] = {"quality_node": qual_node}
        node = ImplementationNode("Impl", context)

        await node.inbox.put(PipelineSignal("approved_plan", "tester"))
        await node.inbox.put(PipelineSignal("shutdown", "system"))

        await node.execute()
        sig = await qual_node.inbox.get()
        assert sig.action == "code_ready"

    asyncio.run(_run())
