# ruff: noqa: E402
import pytest

# Skip this entire module if web dependencies are missing (minimal core matrix)
pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient
from phi_complexity.web.server import app, active_websockets

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_websockets():
    """Garantit l'isolation des tests en purgeant les sockets actifs (Suture bot review)."""
    active_websockets.clear()
    yield
    active_websockets.clear()


def test_read_main():
    """Vérifie que la page d'accueil de l'IDE est servie."""
    response = client.get("/")
    assert response.status_code == 200
    assert "PHIDÉLIA // STATION" in response.text


def test_websocket_connection():
    """Vérifie la connexion et le cycle de vie de base du WebSocket."""
    with client.websocket_connect("/ws/pipeline") as websocket:
        # Vérifie que le socket est enregistré
        assert len(active_websockets) > 0

        # Test de l'audit (Mode Pipeline ou Fallback selon l'environnement)
        websocket.send_json(
            {"command": "audit_code", "code": "def hello():\n    return 42"}
        )

        # On s'attend à recevoir des logs d'audit
        messages = []
        for _ in range(20):
            data = websocket.receive_json()
            messages.append(data.get("message", ""))
            if data.get("type") == "status" and data.get("ready"):
                break

        full_log = "\n".join(messages)
        # On vérifie qu'on a bien eu une trace d'analyse (Radiance ou Phase)
        assert "Radiance" in full_log or "Phase" in full_log
        assert "Initialisation" in full_log

    # Après déconnexion, il doit être retiré
    assert len(active_websockets) == 0


def test_websocket_error_handling():
    """Vérifie que le serveur gère les commandes invalides."""
    with client.websocket_connect("/ws/pipeline") as websocket:
        websocket.send_json({"command": "unknown"})
        # Pas de crash attendu, le socket reste ouvert pour d'autres commandes
        # On vérifie qu'on peut toujours envoyer des données
        websocket.send_json({"command": "audit_code", "code": "pass"})
        data = websocket.receive_json()
        assert data["type"] == "log"
