from fpdf import FPDF


def make_pdf(pages):
    """Build a small PDF in memory; each item in `pages` is one page's text ("" = blank page)."""
    pdf = FPDF()
    pdf.set_font("Helvetica", size=11)
    for text in pages:
        pdf.add_page()
        if text:
            pdf.multi_cell(0, 6, text)
    return bytes(pdf.output())
