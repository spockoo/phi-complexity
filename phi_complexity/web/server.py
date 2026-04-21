import asyncio
import logging
from typing import Set, Any
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

# On essaie d'importer l'Orchestrateur Phidélia
try:
    from phi_complexity.pipeline.orchestrator import PipelineOrchestrator
except ImportError:
    PipelineOrchestrator = None

app = FastAPI(title="Phidélia IDE local", version="0.2.2")

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
# Crée le dossier templates s'il n'existe pas
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

active_websockets: Set[WebSocket] = set()

# Handler personnalisé pour capturer les logs du pipeline asynchrone et les envoyer au Frontend
class WebsocketLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        # La conversion en liste (GIL thread-safe) prévient "Set changed size during iteration"
        for ws in list(active_websockets):
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(ws.send_json({"type": "log", "message": msg}))
            except Exception:
                pass

# Injection du Handler dans le logger commun de l'orchestrateur
logger = logging.getLogger("phi_pipeline")
ws_handler = WebsocketLogHandler()
ws_handler.setFormatter(logging.Formatter("%(asctime)s | %(name)s | %(message)s"))
logger.addHandler(ws_handler)


@app.get("/", response_class=HTMLResponse)
async def get_ide(request: Request) -> Any:
    """Sert l'interface Frontend de développement."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.websocket("/ws/pipeline")
async def websocket_pipeline(websocket: WebSocket) -> None:
    """Trie les messages de code envoyés par le Frontend et démarre l'Orchestrateur."""
    await websocket.accept()
    active_websockets.add(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            command = data.get("command")
            if command == "audit_code":
                code_content = data.get("code", "")
                await websocket.send_json({"type": "log", "message": "[FastAPI System] Initialisation de la Station Phidélia..."})
                
                if PipelineOrchestrator is not None:
                    # Exécution asynchrone absolue de l'orchestrateur
                    orchestrator = PipelineOrchestrator()
                    await orchestrator.run_pipeline("Analyse Cybersécuritaire en ligne", "/tmp/phidelia_web_session")
                else:
                    # Failover magistral si le Pipeline n'est pas encore mergé dans ce dossier
                    await websocket.send_json({"type": "log", "message": "⚠ Orchestrateur asynchrone V2 introuvable."})
                    await websocket.send_json({"type": "log", "message": "◈ Activation de l'Hologramme d'Audit de secours..."})
                    
                    import tempfile
                    import os
                    from phi_complexity import auditer
                    
                    with tempfile.NamedTemporaryFile("w+", suffix=".py", delete=False, encoding="utf-8") as f:
                        f.write(code_content)
                        tmp_path = f.name
                        
                    try:
                        await asyncio.sleep(0.5) # Effet visuel scanning
                        metrics = auditer(tmp_path)
                        await websocket.send_json({"type": "log", "message": f"-> Radiance mathématique : {metrics.get('radiance', 0):.1f}"})
                        await websocket.send_json({"type": "log", "message": f"-> Divergence φ (Lilith) : {metrics.get('lilith_variance', 0):.2f}"})
                        await websocket.send_json({"type": "log", "message": f"-> Entropie structurale  : {metrics.get('shannon_entropy', 0):.2f}"})
                        
                        if metrics.get("radiance", 0) > 70:
                            await websocket.send_json({"type": "log", "message": "[APPROBATION] Validation Gnostique Réussie."})
                        else:
                            await websocket.send_json({"type": "log", "message": "[REJET] La structure du code génère de la friction."})
                    except Exception as e:
                        await websocket.send_json({"type": "log", "message": f"[ERROR] Fracture mathématique lors de l'audit : {e}"})
                    finally:
                        os.unlink(tmp_path)
                
                await websocket.send_json({"type": "status", "ready": True})
                
    except WebSocketDisconnect:
        active_websockets.remove(websocket)
