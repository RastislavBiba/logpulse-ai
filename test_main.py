from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    """Overí, že úvodné HTML UI sa načíta s kódom 200 a obsahuje brand NOTIX."""
    response = client.get("/")
    assert response.status_code == 200
    assert "NOTIX" in response.text

def test_health_check():
    """Overí health endpoint pre orchestráciu kontajnera."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_analyze_validation_error():
    """Overí Pydantic validáciu krátkeho vstupu (očakáva 422)."""
    response = client.post("/analyze", json={"log_text": "err"})
    assert response.status_code == 422
