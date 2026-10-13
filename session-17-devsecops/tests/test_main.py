import pytest
from fastapi.testclient import TestClient

from app.main import app, tasks

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_tasks():
    tasks.clear()


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_create_and_list():
    res = client.post("/tasks", json={"title": "scan the image"})
    assert res.status_code == 201
    assert res.json()["id"] == 1
    assert len(client.get("/tasks").json()) == 1


def test_validation():
    assert client.post("/tasks", json={"title": ""}).status_code == 422


def test_update():
    client.post("/tasks", json={"title": "write tests"})
    res = client.put("/tasks/1", json={"title": "write tests", "done": True})
    assert res.json()["done"] is True


def test_update_missing():
    assert client.put("/tasks/5", json={"title": "x"}).status_code == 404


def test_delete():
    client.post("/tasks", json={"title": "temp"})
    assert client.delete("/tasks/1").status_code == 200
    assert client.delete("/tasks/1").status_code == 404


def test_config_defaults(tmp_path):
    from app.config import load_config
    assert load_config(str(tmp_path / "missing.yaml"))["max_tasks"] == 100
    cfg = tmp_path / "config.yaml"
    cfg.write_text("max_tasks: 5\n")
    assert load_config(str(cfg))["max_tasks"] == 5
