from app.services.ingestion import chunk_text, process_document
from helpers import make_pdf


def words(n, start=0):
    return " ".join(f"w{i}" for i in range(start, start + n))


def test_chunks_overlap_by_40_words():
    chunks = chunk_text(words(450))
    assert len(chunks) == 3  # windows start at word 0, 160 and 320
    first, second = chunks[0].split(), chunks[1].split()
    assert len(first) == 200
    assert first[-40:] == second[:40]
    assert chunks[-1].split()[-1] == "w449"  # nothing lost at the end


def test_short_and_empty_text():
    assert chunk_text("just a few words") == ["just a few words"]
    assert chunk_text("") == []
    assert chunk_text("   \n  ") == []


def test_custom_size_and_overlap():
    assert chunk_text(words(10), chunk_size=4, overlap=1) == [
        "w0 w1 w2 w3", "w3 w4 w5 w6", "w6 w7 w8 w9", "w9",
    ]


def test_process_document_keeps_page_numbers_and_skips_blank_pages(tmp_path):
    path = tmp_path / "doc.pdf"
    path.write_bytes(make_pdf(["Refunds take seven days.", "", "Shipping is free over fifty dollars."]))

    chunks = process_document(str(path), display_name="handbook.pdf")

    assert [c["page"] for c in chunks] == [1, 3]
    assert all(c["source"] == "handbook.pdf" for c in chunks)
    assert "Refunds take seven days." in chunks[0]["text"]
