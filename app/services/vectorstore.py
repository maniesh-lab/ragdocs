import chromadb
from app.core.config import settings
from app.services.embeddings import model

# A persistent client writes to disk (in the folder from settings), so our
# stored embeddings survive between runs — we don't have to re-embed every
# document each time we restart the app.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
client = chromadb.PersistentClient(path=settings.chroma_persist_dir)

# a "collection" is like a table.
def get_collection_for_document(document_id: str):
    return client.get_or_create_collection(name=document_id)



def add_chunks(chunks: list[dict], document_id: str):

    collection = get_collection_for_document(document_id)

    # Chroma needs a unique string ID per entry. We build one from the
    # source filename + page number + position in the list, so IDs never collide.
    # PTR: source is just file_path - look in ingestion
    ids = [f"{document_id}-{i}" for i in range(len(chunks))]

    # Chroma wants plain lists, not numpy arrays — .tolist() converts each
    # embedding vector into a normal Python list of numbers.
    embeddings = [c["embedding"].tolist() for c in chunks]

    documents = [c["text"] for c in chunks]

    # Metadata is anything we want attached to a result when we search later —
    # here, so we can tell the user which file/page an answer came from.
    metadatas = [{"source": c["source"], "page": c["page"]} for c in chunks]

    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)




def query_chunks(question: str,document_id:str, n_results: int = 5) -> list[dict]:

    collection = get_collection_for_document(document_id)
    question_embedding = model.encode([question])[0].tolist()

    #.query is a function used to search for the closest vectors stored in collection above
    # n_results mean give 5 matches by default or what user sets
    results = collection.query(query_embeddings=[question_embedding], n_results=n_results)

    matches = []
    for doc, meta, dist in zip(
        results["documents"][0], #inside [0] slot is a list of all 5 matched chunk texts, ordered from closest to least close
        results["metadatas"][0],
        results["distances"][0],
    ):
        matches.append({"text": doc, "source": meta["source"], "page": meta["page"], "distance": dist})

    return matches

