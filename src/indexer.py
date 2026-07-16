"""
Ingests course material: PDF/text extraction (with OCR fallback for scanned
pages), chunking, embedding, and FAISS index construction.
"""

import pdfplumber
from sentence_transformers import SentenceTransformer
import faiss
from pdf2image import convert_from_path
import pytesseract

_model = None


def get_embedding_model():
    """Lazy-loads the sentence-transformers model once and reuses it."""
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def extract_pages(pdf_path, ocr_dpi=200):
    """
    Extracts text per page from a PDF. Tries native text extraction first;
    falls back to OCR for pages that come back empty (scanned/image PDFs).
    Returns: list of {"page_num": int, "text": str}
    """
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            pages.append({"page_num": i + 1, "text": text.strip()})

    needs_ocr = [p["page_num"] for p in pages if len(p["text"]) < 5]

    if needs_ocr:
        print(f"{len(needs_ocr)}/{len(pages)} page(s) need OCR — running pytesseract...")
        images = convert_from_path(pdf_path, dpi=ocr_dpi)
        for i, img in enumerate(images):
            page_num = i + 1
            if page_num in needs_ocr:
                pages[i]["text"] = pytesseract.image_to_string(img).strip()

    return pages


def chunk_pages(pages, source_file, min_words=15, max_words=100, overlap_words=20):
    """
    Converts pages into chunks with metadata.
    - Merges pages under min_words into the next page.
    - Splits pages over max_words using a sliding window.
    Defaults (100 words) are tuned for dense lecture notes; raise max_words
    for material that's mostly short bullet-point slides.
    """
    chunks = []
    buffer_text = ""
    buffer_pages = []

    for page in pages:
        words = page["text"].split()

        if len(words) < min_words:
            buffer_text += " " + page["text"]
            buffer_pages.append(page["page_num"])
            continue

        combined_text = (buffer_text + " " + page["text"]).strip()
        combined_pages = buffer_pages + [page["page_num"]]
        buffer_text, buffer_pages = "", []

        combined_words = combined_text.split()

        if len(combined_words) <= max_words:
            chunks.append({"source_file": source_file, "pages": combined_pages, "text": combined_text})
        else:
            start = 0
            while start < len(combined_words):
                end = start + max_words
                window_text = " ".join(combined_words[start:end])
                chunks.append({"source_file": source_file, "pages": combined_pages, "text": window_text})
                start += (max_words - overlap_words)

    if buffer_text.strip():
        chunks.append({"source_file": source_file, "pages": buffer_pages, "text": buffer_text.strip()})

    return chunks


def build_index(chunks):
    """Embeds chunks and builds a FAISS index. Returns (index, chunks)."""
    model = get_embedding_model()
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings.astype('float32'))

    return index, chunks


def index_course_material(pdf_paths):
    """Takes a list of PDF paths, returns a built FAISS index + chunk metadata."""
    all_chunks = []
    for path in pdf_paths:
        pages = extract_pages(path)
        chunks = chunk_pages(pages, source_file=path)
        all_chunks.extend(chunks)

    return build_index(all_chunks)