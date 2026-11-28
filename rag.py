"""
rag.py - Session 3: from documents to a searchable index.

    documents  ->  chunks  ->  embeddings (vectors)  ->  index  ->  search

    import rag
    store = rag.build_store()            # load, chunk, embed and index the corpus
    for hit in rag.search(store, "What share of absences leads to a DN grade?"):
        print(round(hit["score"], 2), hit["id"], hit["text"][:80])

Later sessions call rag.get_store(), which builds the store once and reuses it.
"""
import re
from pathlib import Path

import numpy as np

import config

try:
    import faiss  # FAISS: a fast library for searching vectors
except ImportError:  # no faiss for this computer (e.g. an older Mac): plain numpy below does the same job
    faiss = None

_embedders = {}  # embedding models we already loaded, by name
_store = None    # the store get_store() built last


# ---------------------------------------------------------------- 1. load
def read_file(path):
    """The text of one document, or None if we cannot read this kind of file."""
    if path.suffix.lower() in (".txt", ".md"):
        return path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    return None


def load_documents(corpus_dir=None):
    """Read every document in the corpus folder (config.CORPUS_DIR) that read_file() understands (.txt, .md, .pdf).
    Returns a list of {"source": file name, "text": the whole text}."""
    folder = corpus_dir or config.CORPUS_DIR
    documents, skipped = [], []
    for path in sorted(folder.iterdir()):
        text = read_file(path)
        if text is None:
            skipped.append(path.name)
        else:
            documents.append({"source": path.name, "text": text})
    print(f"Loaded {len(documents)} documents from {folder}")
    if skipped:
        print(f"Skipped {len(skipped)} file(s) this loader cannot read: {', '.join(skipped)}")
    return documents


# ---------------------------------------------------------------- 2. chunk
def chunk_text(text, size=None, overlap=None):
    """Cut text into pieces of `size` characters. Each piece starts `overlap` characters
    before the previous one ended, so a sentence cut at a border is still whole somewhere."""
    size = size or config.CHUNK_SIZE
    overlap = config.CHUNK_OVERLAP if overlap is None else overlap
    if overlap >= size:
        raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
    # SOLUTION START: TODO (Session 3): cut `text` into chunks of `size` characters that overlap by `overlap`
    chunks = []
    start = 0
    while True:
        chunks.append(text[start:start + size].strip())
        if start + size >= len(text):
            break
        start += size - overlap
    return [chunk for chunk in chunks if chunk]
    # SOLUTION END


HEADING = re.compile(r"^\s*(?:#{1,6}\s+(.+?)|=+\s*(.+?)\s*=+)\s*$")  # "## Refunds" or "== Refunds =="


def split_sections(text):
    """Split a text at its headings: [(heading, body), ...]. Text before the first heading has heading None."""
    sections, heading, lines = [], None, []
    for line in text.splitlines():
        match = HEADING.match(line)
        if match:
            sections.append((heading, "\n".join(lines)))
            heading, lines = (match.group(1) or match.group(2)).strip(), []
        else:
            lines.append(line)
    sections.append((heading, "\n".join(lines)))
    return [(heading, body) for heading, body in sections if body.strip()]


def chunk_by_section(doc):
    """One chunk per section, each starting with its address, e.g. "01-05 attendance and withdrawal > Article nine: ...".
    A section longer than CHUNK_SIZE characters is cut with chunk_text(), and every piece keeps the label."""
    title = Path(doc["source"]).stem.replace("_", " ").capitalize()  # "01-05_Attendance_And_Withdrawal.md" -> "01-05 attendance and withdrawal"
    chunks = []
    for heading, body in split_sections(doc["text"]):
        label = f"{title} > {heading}" if heading else title
        chunks += [f"{label}: {piece}" for piece in chunk_text(body)]
    return chunks


def make_chunks(documents):
    """Chunk every document. Each chunk remembers where it came from, e.g. id '01-05_Attendance_And_Withdrawal.md#3'."""
    # PLAY WITH THE CHUNKING: change these in config.py, then search again (get_store() rebuilds by itself).
    #   CHUNK_BY_SECTION  False = a character window that ignores the document's structure (chunk_text)
    #                     True  = one chunk per "## heading" section, with the heading in front (chunk_by_section)
    #   CHUNK_SIZE        characters per window. With CHUNK_BY_SECTION = True, a section longer than this is
    #                     cut into pieces. In data/kfupm_structured, 191 of 253 sections fit in 500 characters and
    #                     the longest has 995, so CHUNK_SIZE = 1000 keeps every rule whole in one chunk.
    #                     Mind the limit: the embedding model reads only the first 256 tokens of a chunk, about
    #                     1000 characters of this text (the longest section is 227 tokens), so in a bigger
    #                     window the characters past the limit are never searched.
    #   CHUNK_OVERLAP     characters two neighbouring windows share, so a sentence cut at a border survives.
    #   CORPUS_DIR        data/kfupm_structured (sections) or data/kfupm_raw (one plain dump of the same text).
    # Try: raw + windows, structured + windows, structured + sections; then CHUNK_SIZE 100 vs 2000.
    # Compare which chunk search() puts first for the same question.
    chunks = []
    for doc in documents:
        pieces = chunk_by_section(doc) if config.CHUNK_BY_SECTION else chunk_text(doc["text"])
        for number, text in enumerate(pieces, start=1):
            chunks.append({"id": f"{doc['source']}#{number}", "source": doc["source"], "text": text})
    return chunks


# ---------------------------------------------------------------- 3. embed
def embed(texts):
    """Turn texts into vectors, one row per text. Texts with similar meaning get similar vectors.
    The first call downloads the embedding model (about 90 MB)."""
    name = config.EMBEDDING_MODEL
    if name not in _embedders:
        from huggingface_hub.utils import logging as hf_logging
        from sentence_transformers import SentenceTransformer
        hf_logging.set_verbosity_error()  # hides a harmless "Please set a HF_TOKEN" warning (no key is needed)
        _embedders[name] = SentenceTransformer(name)
    # normalize: every vector gets length 1, so "dot product" = cosine similarity (1 = same meaning)
    vectors = _embedders[name].encode(texts, normalize_embeddings=True)
    return np.asarray(vectors, dtype="float32")


# ---------------------------------------------------------------- 4. index
class NumpyIndex:
    """The same job as faiss.IndexFlatIP, in plain numpy. Used only when faiss is missing."""

    def __init__(self, vectors):
        self.vectors = vectors

    def search(self, queries, k):
        scores = queries @ self.vectors.T                    # similarity to every chunk
        rows = np.argsort(-scores, axis=1)[:, :k]           # positions of the k best
        return np.take_along_axis(scores, rows, axis=1), rows


def build_store(documents=None):
    """Load, chunk, embed and index the corpus. Returns the 'store' that search() needs."""
    documents = load_documents() if documents is None else documents
    chunks = make_chunks(documents)
    vectors = embed([chunk["text"] for chunk in chunks])
    if faiss is not None:
        index = faiss.IndexFlatIP(vectors.shape[1])  # IP = inner product (cosine for normalized vectors)
        index.add(vectors)
    else:
        print("faiss is not installed: using plain numpy search instead (same results)")
        index = NumpyIndex(vectors)
    print(f"Indexed {len(chunks)} chunks (CHUNK_SIZE={config.CHUNK_SIZE}, CHUNK_OVERLAP={config.CHUNK_OVERLAP}, "
          f"CHUNK_BY_SECTION={config.CHUNK_BY_SECTION})")
    return {"index": index, "chunks": chunks, "settings": _settings()}


def _settings():
    return (config.CHUNK_SIZE, config.CHUNK_OVERLAP, config.CHUNK_BY_SECTION,
            config.EMBEDDING_MODEL, str(config.CORPUS_DIR))


def get_store(rebuild=False):
    """The store for the corpus in config.py: built the first time, then reused.
    It is rebuilt automatically if you change CHUNK_SIZE, CHUNK_OVERLAP, CHUNK_BY_SECTION, EMBEDDING_MODEL or CORPUS_DIR,
    and when you ask for it with rebuild=True (e.g. after changing the documents)."""
    global _store
    if rebuild or _store is None or _store["settings"] != _settings():
        _store = build_store()
    return _store


# ---------------------------------------------------------------- 5. search
def search(store, query, k=None):
    """Return the k chunks most similar to the query, best first.
    Each result is a chunk plus its "score" (higher = closer in meaning)."""
    k = k or config.TOP_K
    if store["settings"] != _settings():
        print("Warning: chunk/model/corpus settings changed since build_store(). Run build_store() again.")
    # SOLUTION START: TODO (Session 3): embed the query, ask store["index"] for the k best rows, return those chunks with their scores
    scores, rows = store["index"].search(embed([query]), k)
    results = []
    for score, row in zip(scores[0], rows[0]):
        if row == -1:  # FAISS fills with -1 when there are fewer than k chunks
            continue
        results.append({**store["chunks"][row], "score": float(score)})
    return results
    # SOLUTION END
