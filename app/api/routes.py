import os
import uuid
from fastapi import APIRouter, UploadFile, HTTPException
from app.services.ingestion import process_document
from app.services.embeddings import embed_chunks
from app.services.vectorstore import add_chunks, query_chunks
from app.services.llm import get_answer
from app.core.config import settings

router = APIRouter()


@router.post("/upload")
async def upload_document(file: UploadFile):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    document_id = str(uuid.uuid4())
    file_path = os.path.join(settings.upload_dir, file.filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    chunks = process_document(file_path)

    if len(chunks) == 0:
        raise HTTPException(
            status_code=400,
            detail="No readable text found in this PDF. It may be scanned/image-only.",
        )

    chunks = embed_chunks(chunks)
    add_chunks(chunks, document_id)

    return {"document_id": document_id, "filename": file.filename, "chunks_added": len(chunks)}


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