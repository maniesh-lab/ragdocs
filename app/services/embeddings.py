from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_chunks(chunks: list[dict]) -> list[dict]:

    texts = [chunk["text"] for chunk in chunks]     # Pull just the text out of every chunk dict into one flat list of strings.

    vectors = model.encode(texts) # turning list above into vector


    # zip() puts two lists together by position; first chunk with first vector, second chunk with second vector, etc.
    for chunk, vector in zip(chunks, vectors):  # we are pairing them here
        chunk["embedding"] = vector

    return chunks