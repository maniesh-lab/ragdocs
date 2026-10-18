import os
import uuid

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.services.embeddings import embed_chunks
from app.services.ingestion import process_document
from app.services.llm import get_answer
from app.services.vectorstore import add_chunks, query_chunks

router = APIRouter()


def _remove_quietly(path):
    try:
        os.remove(path)
    except OSError:
        pass


@router.post("/upload")
async def upload_document(file: UploadFile):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"PDF is larger than {settings.max_upload_mb} MB.")

    document_id = str(uuid.uuid4())

    # Save under the generated ID, never under the filename the client sent.
    # A client-chosen name like "../../app/main.py" could otherwise write
    # outside the uploads folder, and two uploads with the same name would
    # overwrite each other. The original name is kept only for display.
    display_name = os.path.basename(file.filename)
    os.makedirs(settings.upload_dir, exist_ok=True)
    file_path = os.path.join(settings.upload_dir, f"{document_id}.pdf")
    with open(file_path, "wb") as f:
        f.write(content)

    # Parsing and embedding are slow, CPU-heavy steps. run_in_threadpool
    # runs them off the event loop so other requests aren't stuck waiting.
    try:
        chunks = await run_in_threadpool(process_document, file_path, display_name)
    except Exception:
        # pypdf raises many different error types for broken files
        _remove_quietly(file_path)
        raise HTTPException(
            status_code=400,
            detail="Couldn't read this PDF. It may be corrupted or password-protected.",
        )

    if len(chunks) == 0:
        _remove_quietly(file_path)
        raise HTTPException(
            status_code=400,
            detail="No readable text found in this PDF. It may be scanned/image-only.",
        )

    chunks = await run_in_threadpool(embed_chunks, chunks)
    await run_in_threadpool(add_chunks, chunks, document_id)

    return {"document_id": document_id, "filename": display_name, "chunks_added": len(chunks)}


@router.post("/chat")
def chat(question: str, document_id: str):
    matches = query_chunks(question, document_id)

    if len(matches) == 0:
        raise HTTPException(
            status_code=404,
            detail="No document found for this document_id. Please upload a document first.",
        )

    answer = get_answer(question, matches)
    return {"answer": answer, "sources": matches}
