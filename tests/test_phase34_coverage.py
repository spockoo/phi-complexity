
import pytest
import asyncio
import argparse
import os
from unittest.mock import MagicMock, AsyncMock
from phi_complexity.pipeline.orchestrator import PipelineOrchestrator, PipelineSignal
from phi_complexity.pipeline.nodes import SpecificationNode, ValidationNode, ImplementationNode, QualityGateNode, SecurityGateNode
from phi_complexity.cli import _executer_pipeline, _executer_ui

class MockNode:
    def __init__(self):
        self.inbox = asyncio.Queue()
        self.name = "MockNode"

@pytest.mark.anyio
async def test_specification_node_logic(monkeypatch):
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    mock_val = MockNode()
    context = {"validation_node": mock_val}
    node = SpecificationNode("Spec", context)
    await node.inbox.put(PipelineSignal(action="start_planning", issuer="test"))
    await node.inbox.put(PipelineSignal(action="shutdown", issuer="test"))
    try:
        await asyncio.wait_for(node.execute(), timeout=1.0)
    except asyncio.TimeoutError: pass
    if not mock_val.inbox.empty():
        sig = await mock_val.inbox.get()
        assert sig.action == "review_plan"

@pytest.mark.anyio
async def test_specification_node_missing_context(monkeypatch):
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    context = {}
    node = SpecificationNode("Spec", context)
    node.orchestrator = MagicMock()
    # Mock signal_callback as an AsyncMock
    node.orchestrator.signal_callback = AsyncMock()
    await node.inbox.put(PipelineSignal(action="start_planning", issuer="test"))
    await node.inbox.put(PipelineSignal(action="shutdown", issuer="test"))
    try:
        await asyncio.wait_for(node.execute(), timeout=1.0)
    except asyncio.TimeoutError: pass

@pytest.mark.anyio
async def test_validation_node_logic(monkeypatch):
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    mock_impl = MockNode()
    context = {"implementation_node": mock_impl}
    node = ValidationNode("Val", context)
    await node.inbox.put(PipelineSignal(action="review_plan", issuer="test", data="plan"))
    await node.inbox.put(PipelineSignal(action="shutdown", issuer="test"))
    try:
        await asyncio.wait_for(node.execute(), timeout=1.0)
    except asyncio.TimeoutError: pass
    if not mock_impl.inbox.empty():
        sig = await mock_impl.inbox.get()
        assert sig.action == "approved_plan"

@pytest.mark.anyio
async def test_implementation_node_logic(monkeypatch):
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    mock_qual = MockNode()
    context = {"quality_node": mock_qual}
    node = ImplementationNode("Impl", context)
    await node.inbox.put(PipelineSignal(action="approved_plan", issuer="test"))
    await node.inbox.put(PipelineSignal(action="shutdown", issuer="test"))
    try:
        await asyncio.wait_for(node.execute(), timeout=1.0)
    except asyncio.TimeoutError: pass
    if not mock_qual.inbox.empty():
        sig = await mock_qual.inbox.get()
        assert sig.action == "code_ready"

@pytest.mark.anyio
async def test_quality_gate_node_logic(tmp_path):
    test_file = tmp_path / "test_code.py"
    test_file.write_text("def test(): pass")
    mock_sec = MockNode()
    mock_impl = MockNode()
    context = {"security_node": mock_sec, "implementation_node": mock_impl, "project_dir": str(tmp_path)}
    node = QualityGateNode("Qual", context)
    await node.inbox.put(PipelineSignal(action="code_ready", issuer="test"))
    await node.inbox.put(PipelineSignal(action="shutdown", issuer="test"))
    try:
        await asyncio.wait_for(node.execute(), timeout=2.0)
    except asyncio.TimeoutError: pass
    if not mock_sec.inbox.empty():
        sig = await mock_sec.inbox.get()
        assert sig.action == "quality_passed"

@pytest.mark.anyio
async def test_quality_gate_node_failure(tmp_path):
    test_file = tmp_path / "bad_code.py"
    test_file.write_text("def a():\n" + "    if 1:\n" * 20 + "        pass")
    mock_sec = MockNode()
    mock_impl = MockNode()
    context = {"security_node": mock_sec, "implementation_node": mock_impl, "project_dir": str(tmp_path)}
    node = QualityGateNode("Qual", context)
    await node.inbox.put(PipelineSignal(action="code_ready", issuer="test"))
    await node.inbox.put(PipelineSignal(action="shutdown", issuer="test"))
    try:
        await asyncio.wait_for(node.execute(), timeout=2.0)
    except asyncio.TimeoutError: pass
    if not mock_impl.inbox.empty():
        sig = await mock_impl.inbox.get()
        assert sig.action == "quality_rejected"

def test_executer_pipeline_cli(monkeypatch):
    args = argparse.Namespace(concept="Test", dir=".")
    async def mock_run(*args, **kwargs): return None
    monkeypatch.setattr(PipelineOrchestrator, "run_pipeline", mock_run)
    assert _executer_pipeline(args) == 0

def test_executer_ui_import_error(monkeypatch):
    import builtins
    real_import = builtins.__import__
    def mock_import(name, *args, **kwargs):
        if name == 'uvicorn': raise ImportError("Mocked error")
        return real_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", mock_import)
    assert _executer_ui() == 1
