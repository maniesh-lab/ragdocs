from pypdf import PdfReader


def extract_text_by_page(filepath:str) -> list[tuple[int,str]]:
    reader = PdfReader(filepath)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or "" # extract text ,if emtpy use empty string: ""
        pages.append((i+1, text))
    return pages


def chunk_text(text:str, chunk_size:int = 200, overlap:int = 40) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):     # keep going until we've moved past the end of the word list
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)

        # move the window forward, but LESS than a full chunk_size —
        # that's what makes the next window overlap with this one.
        # e.g. chunk_size=200, overlap=40 -> we only advance 160 words each time,
        # so the last 40 words of this chunk are also the first 40 of the next one.
        start += chunk_size - overlap 
    return chunks


def process_document(file_path:str) -> list[dict]:

    pages = extract_text_by_page(file_path)

    all_chunks = []  # final output: every chunk from every page; into one list

    for page_num, page_text in pages:
        # skip pages with no real text (blank pages, scanned images pypdf can't read)
        # .strip() removes whitespace, so a page of just spaces/newlines counts as empty too
        if not page_text.strip():
            continue

        for chunk in chunk_text(page_text):
            all_chunks.append({
                "text": chunk,
                "source": file_path,
                "page": page_num
            })

    return all_chunks