from fastapi.testclient import TestClient

from app.main import app


def test_saude_e_bncc():
    cliente = TestClient(app)
    assert cliente.get("/saude").json()["base"]["total"] == 93
    assert cliente.get("/bncc").status_code == 200
