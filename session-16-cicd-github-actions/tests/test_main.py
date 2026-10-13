import pytest

from app.main import app, notes


@pytest.fixture
def client():
    notes.clear()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.get_json()["message"] == "Notes API is running"


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "healthy"}


def test_add_and_list_notes(client):
    res = client.post("/notes", json={"text": "learn github actions"})
    assert res.status_code == 201
    assert res.get_json()["id"] == 1

    res = client.get("/notes")
    assert res.get_json()["notes"][0]["text"] == "learn github actions"


def test_add_note_without_text(client):
    res = client.post("/notes", json={})
    assert res.status_code == 400


def test_delete_note(client):
    client.post("/notes", json={"text": "temp"})
    res = client.delete("/notes/1")
    assert res.status_code == 200
    assert client.get("/").get_json()["count"] == 0


def test_delete_missing_note(client):
    res = client.delete("/notes/99")
    assert res.status_code == 404
