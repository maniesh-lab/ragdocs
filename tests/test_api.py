import os

import pytest
from fastapi.testclient import TestClient

from app.api import routes
from app.core.config import settings
from app.main import app
from app.services.llm import build_prompt
from helpers import make_pdf

client = TestClient(app)


@pytest.fixture(autouse=True)
def fake_services(tmp_path, monkeypatch):
    """Point uploads at a temp folder and swap the slow/external steps for fakes."""
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    stored = {}

    def fake_embed(chunks):
        return [dict(c, embedding=[0.0]) for c in chunks]

    def fake_add(chunks, document_id):
        stored[document_id] = chunks

    monkeypatch.setattr(routes, "embed_chunks", fake_embed)
    monkeypatch.setattr(routes, "add_chunks", fake_add)
    return stored


def upload(name, data):
    return client.post("/upload", files={"file": (name, data, "application/pdf")})


def saved_files():
    folder = settings.upload_dir
    return os.listdir(folder) if os.path.isdir(folder) else []


def test_health():
    assert client.get("/health").json() == {"status": "ok", "gemini_key_loaded": True}


def test_upload_stores_chunks_under_a_new_id(fake_services):
    response = upload("Handbook.PDF", make_pdf(["Refunds take seven days."]))
    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "Handbook.PDF"
    assert body["chunks_added"] == 1
    assert fake_services[body["document_id"]][0]["source"] == "Handbook.PDF"
    assert saved_files() == [f"{body['document_id']}.pdf"]


def test_upload_name_cannot_escape_the_uploads_folder():
    response = upload("../../app/main.pdf", make_pdf(["Hello there."]))
    assert response.status_code == 200
    assert response.json()["filename"] == "main.pdf"
    assert saved_files() == [f"{response.json()['document_id']}.pdf"]


def test_only_pdfs_are_accepted():
    response = upload("notes.txt", b"hello")
    assert response.status_code == 400
    assert saved_files() == []


def test_too_big_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "max_upload_mb", 0)
    assert upload("big.pdf", make_pdf(["x"])).status_code == 413


def test_broken_pdf_is_rejected_and_deleted():
    response = upload("broken.pdf", b"%PDF-1.4 this is not really a pdf")
    assert response.status_code == 400
    assert "corrupted" in response.json()["detail"]
    assert saved_files() == []


def test_pdf_without_text_is_rejected_and_deleted():
    response = upload("scan.pdf", make_pdf(["", ""]))
    assert response.status_code == 400
    assert "No readable text" in response.json()["detail"]
    assert saved_files() == []


def test_chat_with_unknown_document_is_404(monkeypatch):
    monkeypatch.setattr(routes, "query_chunks", lambda question, document_id: [])
    response = client.post("/chat", params={"question": "hi", "document_id": "nope"})
    assert response.status_code == 404


def test_chat_answers_from_the_matches(monkeypatch):
    matches = [{"text": "Refunds take 7 days.", "source": "faq.pdf", "page": 2, "distance": 0.1}]
    monkeypatch.setattr(routes, "query_chunks", lambda question, document_id: matches)
    monkeypatch.setattr(routes, "get_answer", lambda question, found: f"7 days ({len(found)} source)")

    response = client.post("/chat", params={"question": "How long do refunds take?", "document_id": "abc"})

    assert response.status_code == 200
    assert response.json() == {"answer": "7 days (1 source)", "sources": matches}


def test_prompt_lists_each_source_and_page():
    prompt = build_prompt("How long?", [
        {"text": "Refunds take 7 days.", "source": "faq.pdf", "page": 2},
        {"text": "Shipping is free.", "source": "faq.pdf", "page": 5},
    ])
    assert "[Source: faq.pdf, page 2]\nRefunds take 7 days." in prompt
    assert "[Source: faq.pdf, page 5]" in prompt
    assert prompt.rstrip().endswith("Question: How long?\nAnswer:")
