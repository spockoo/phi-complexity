import asyncio
import logging
import pytest
from typing import Dict, Any, Optional

from phi_complexity.pipeline.orchestrator import (
    PipelineSignal,
    PipelineNode,
    PipelineOrchestrator
)
from phi_complexity.pipeline.nodes import (
    SpecificationNode,
    ValidationNode,
    ImplementationNode,
    QualityGateNode,
    SecurityGateNode
)

class MockNode(PipelineNode):
    async def execute(self) -> None:
        while True:
            signal = await self.inbox.get()
            if signal.action == "shutdown":
                break
            if signal.action == "ping":
                await self.send_signal(None, "pong")

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.anyio
async def test_pipeline_signal_json():
    """Vérifie la sérialisation/désérialisation des signaux."""
    sig = PipelineSignal(action="test", issuer="issuer", data={"key": "val"})
    js = sig.to_json()
    assert '"action": "test"' in js
    
    sig2 = PipelineSignal.from_json(js)
    assert sig2.action == "test"
    assert sig2.issuer == "issuer"
    assert sig2.data["key"] == "val"

@pytest.mark.anyio
async def test_pipeline_signal_invalid_json():
    """Vérifie la robustesse face aux JSON malformés."""
    sig = PipelineSignal.from_json("{invalid}")
    assert sig.action == "error"
    assert sig.issuer == "system"

@pytest.mark.anyio
async def test_node_send_signal_escalation():
    """Vérifie que l'envoi vers un noeud inexistant déclenche une erreur."""
    context = {"quality_node": MockNode("Quality", {})}
    node = MockNode("Tester", context)
    orchestrator = PipelineOrchestrator()
    node.orchestrator = orchestrator
    
    # On espère que broadcast_error soit appelé et mette le signal dans quality_node.inbox
    await node.send_signal(None, "lost_action")
    
    # Le broadcast_error de orchestrator.py envoie à 'quality_node'
    err_signal = await context["quality_node"].inbox.get()
    assert err_signal.action == "error"
    assert "inexistant" in err_signal.data["message"]

@pytest.mark.anyio
async def test_node_broadcast_error():
    """Vérifie la diffusion d'erreurs."""
    qual_node = MockNode("Quality", {})
    context = {"quality_node": qual_node}
    node = MockNode("Worker", context)
    
    await node.broadcast_error("Explosion")
    sig = await qual_node.inbox.get()
    assert sig.action == "error"
    assert sig.data["message"] == "Explosion"

@pytest.mark.anyio
async def test_orchestrator_registration():
    """Vérifie l'enregistrement des noeuds."""
    orch = PipelineOrchestrator()
    node = MockNode("N1", {})
    orch.register_node(node)
    assert orch.nodes["N1"] == node
    assert node.orchestrator == orch

@pytest.mark.anyio
async def test_full_pipeline_cycle():
    """Vérifie un cycle complet du pipeline (mocké)."""
    # On réduit le timeout pour le test
    orch = PipelineOrchestrator(timeout=1.0)
    
    # Le pipeline s'auto-alimente (Spec -> Val -> Impl -> Qual -> Sec -> Completion)
    await orch.run_pipeline("Test Objective", ".")
    assert orch._is_running is False

@pytest.mark.anyio
async def test_pipeline_timeout_handling():
    """Vérifie la gestion des timeouts de l'orchestrateur."""
    signals = []
    async def cb(s):
        signals.append(s)
        
    orch = PipelineOrchestrator(signal_callback=cb, timeout=0.1)
    # Le pipeline va timeout car les nodes dorment 1s
    await orch.run_pipeline("Timeout test", ".")
    
    actions = [s.action for s in signals]
    assert "error" in actions
    # L'un des messages d'erreur doit mentionner le timeout
    timeout_errors = [s for s in signals if s.action == "error" and "Timeout" in s.data.get("message", "")]
    assert len(timeout_errors) > 0

@pytest.mark.anyio
async def test_nodes_unhandled_signals(caplog):
    """Vérifie que les noeuds loggent les signaux inconnus (Suture)."""
    context = {}
    node = SpecificationNode("Spec", context)
    # On met un signal inconnu
    await node.inbox.put(PipelineSignal("alien_action", "unknown"))
    # On met un signal de shutdown pour arrêter la boucle execute
    await node.inbox.put(PipelineSignal("shutdown", "system"))
    
    with caplog.at_level(logging.DEBUG, logger="phi_pipeline.nodes"):
        await node.execute()
        
    assert "Signal ignoré : alien_action" in caplog.text

@pytest.mark.anyio
async def test_security_gate_node():
    """Vérifie le noeud de sécurité."""
    event = asyncio.Event()
    context = {"completion_event": event}
    node = SecurityGateNode("Security", context)
    
    await node.inbox.put(PipelineSignal("quality_passed", "tester"))
    await node.inbox.put(PipelineSignal("shutdown", "system"))
    
    await node.execute()
    assert event.is_set()

@pytest.mark.anyio
async def test_implementation_node():
    """Vérifie le noeud d'implémentation."""
    # On mock quality_node dans le contexte
    qual_node = MockNode("Quality", {})
    context = {"quality_node": qual_node}
    node = ImplementationNode("Impl", context)
    
    await node.inbox.put(PipelineSignal("approved_plan", "tester"))
    await node.inbox.put(PipelineSignal("shutdown", "system"))
    
    await node.execute()
    # Le signal code_ready doit être dans l'inbox du qual_node
    sig = await qual_node.inbox.get()
    assert sig.action == "code_ready"
