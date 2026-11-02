from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    """Testuje, či úvodný endpoint vracia HTTP 200 a správny stav."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_health_check():
    """Testuje health endpoint pre kontajnery a orchestráciu."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_analyze_validation_error():
    """Testuje Pydantic validáciu - odoslanie neplatného prázdneho logu musí vrátiť 422."""
    response = client.post("/analyze", json={"log_text": "err"})
    assert response.status_code == 422
