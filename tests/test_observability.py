import pytest
from starlette.testclient import TestClient
from app.main import app


@pytest.fixture()
def client():
    return TestClient(app)


def test_metrics_endpoint(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "webhook_requests_total" in r.text
