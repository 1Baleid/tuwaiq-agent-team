"""
rag.py - Session 3: from documents to a searchable index.

    documents  ->  chunks  ->  embeddings (vectors)  ->  index  ->  search

On `main` the functions are EMPTY: students build them with the coding harness (harness.py). Each one has
a docstring (what it returns) and numbered comments (how): the specification the harness follows.
Here, on `solutions`, the reference code sits inside the SOLUTION blocks.

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
    """Return the text of one document, or None if this kind of file cannot be read.

    path: a pathlib.Path. Returns: str, or None.
    """
    # 1. If path.suffix (lower case) is ".txt" or ".md": return path.read_text(encoding="utf-8").
    # 2. If it is ".pdf": from pypdf import PdfReader, and return the text of every page joined with "\n"
    #    (page.extract_text() or "" for each page).
    # 3. Any other suffix: return None (load_documents() then reports the file as skipped).
    # SOLUTION START: TODO (Session 3): write read_file(): follow the docstring and the numbered comments above
    if path.suffix.lower() in (".txt", ".md"):
        return path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    return None
    # SOLUTION END


def load_documents(corpus_dir=None):
    """Read every document in the corpus folder that read_file() understands.

    corpus_dir: a Path, or None for config.CORPUS_DIR (e.g. data/kfupm_raw; the files are directly in it).
    Returns: a list of dicts in file-name order, one per readable file:
        [{"source": "01-05_Attendance_And_Withdrawal.txt", "text": "Article Nine: ..."}, ...]
    "source" is the file name only (path.name).
    """
    # 1. folder = corpus_dir or config.CORPUS_DIR
    # 2. For path in sorted(folder.iterdir()): text = read_file(path). None -> remember path.name as skipped.
    #    Otherwise append {"source": path.name, "text": text}.
    # 3. Print f"Loaded {len(documents)} documents from {folder}", and the skipped file names if any.
    # 4. Return the list.
    # SOLUTION START: TODO (Session 3): write load_documents(): follow the docstring and the numbered comments above
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
    # SOLUTION END


# ---------------------------------------------------------------- 2. chunk
def chunk_text(text, size=None, overlap=None):
    """Cut text into pieces of `size` CHARACTERS. Each piece starts `overlap` characters before the previous
    one ended, so a sentence cut at a border is still whole somewhere.

    size: characters per piece (None = config.CHUNK_SIZE). overlap: None = config.CHUNK_OVERLAP (may be 0).
    Returns: a list of str, each piece stripped of spaces at both ends, empty pieces left out.
        chunk_text("abcdefghij", 4, 1) -> ["abcd", "defg", "ghij"]
    """
    # 1. Fill in the defaults (test "overlap is None", because 0 is a valid overlap).
    # 2. If overlap >= size: raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE").
    # 3. start = 0; repeat: add text[start:start + size].strip(); stop after the piece that reaches the end
    #    (start + size >= len(text)); otherwise start += size - overlap.
    # 4. Return the pieces that are not empty.
    # SOLUTION START: TODO (Session 3): write chunk_text(): follow the docstring and the numbered comments above
    size = size or config.CHUNK_SIZE
    overlap = config.CHUNK_OVERLAP if overlap is None else overlap
    if overlap >= size:
        raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
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
    """Split a text at its headings (lines that match HEADING, e.g. "## Refunds" or "== Refunds ==").

    Returns: a list of (heading, body) tuples in order; heading without the marks, stripped; text before the
    first heading gets heading None; sections with an empty body are left out.
        split_sections("intro\n## A\nfirst\n## B\nsecond") -> [(None, "intro"), ("A", "first"), ("B", "second")]
    """
    # 1. Walk text.splitlines(), keeping the current heading (start: None) and its lines.
    # 2. On a HEADING match: save (heading, "\n".join(lines)); the new heading is (match.group(1) or match.group(2)).strip().
    # 3. Save the last section after the loop; return only those whose body.strip() is not empty.
    # SOLUTION START: TODO (Session 3): write split_sections(): follow the docstring and the numbered comments above
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
    # SOLUTION END


def chunk_by_section(doc):
    """One chunk per section, each starting with its address (label), for CHUNK_BY_SECTION = True.

    doc: one dict from load_documents().
    Returns: a list of str (NOT dicts: make_chunks() adds id and source), e.g.
        ["01-05 attendance and withdrawal > Unexcused absences over 20% give a DN grade: If the number ...", ...]
    """
    # 1. title = Path(doc["source"]).stem.replace("_", " ").capitalize()
    #      "01-05_Attendance_And_Withdrawal.md" -> "01-05 attendance and withdrawal"
    # 2. For each (heading, body) in split_sections(doc["text"]): label = f"{title} > {heading}" if heading else title;
    #    cut the body with chunk_text(body) and add f"{label}: {piece}" for every piece (each piece keeps the label).
    # 3. Return the list of strings.
    # SOLUTION START: TODO (Session 3): write chunk_by_section(): follow the docstring and the numbered comments above
    title = Path(doc["source"]).stem.replace("_", " ").capitalize()
    chunks = []
    for heading, body in split_sections(doc["text"]):
        label = f"{title} > {heading}" if heading else title
        chunks += [f"{label}: {piece}" for piece in chunk_text(body)]
    return chunks
    # SOLUTION END


def make_chunks(documents):
    """Chunk every document. Each chunk remembers where it came from.

    Returns: a list of dicts, numbered from 1 inside each document:
        {"id": "01-05_Attendance_And_Withdrawal.txt#1", "source": "01-05_Attendance_And_Withdrawal.txt", "text": "..."}
    The id MUST be exactly f"{source}#{number}" with a plain integer: answer.cited_sources() only accepts ids
    like "file.txt#3" (never "file.txt#3-1").
    """
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
    #
    # How to write this function:
    # 1. pieces = chunk_by_section(doc) if config.CHUNK_BY_SECTION else chunk_text(doc["text"])
    #    (read config.CHUNK_BY_SECTION here, every call: students change it while the program runs).
    # 2. For number, text in enumerate(pieces, start=1): append the dict above.
    # 3. Return the chunks of all documents in one list.
    # SOLUTION START: TODO (Session 3): write make_chunks(): follow the docstring and the numbered comments above
    chunks = []
    for doc in documents:
        pieces = chunk_by_section(doc) if config.CHUNK_BY_SECTION else chunk_text(doc["text"])
        for number, text in enumerate(pieces, start=1):
            chunks.append({"id": f"{doc['source']}#{number}", "source": doc["source"], "text": text})
    return chunks
    # SOLUTION END


# ---------------------------------------------------------------- 3. embed
def embed(texts):
    """Turn texts into vectors: a float32 numpy array, one row per text, every row of length 1 (normalized),
    so a dot product of two rows is their cosine similarity. The first call downloads the model (about 90 MB).

    Returns: np.ndarray of shape (len(texts), 384) for all-MiniLM-L6-v2.
    """
    # 1. name = config.EMBEDDING_MODEL; load SentenceTransformer(name) only once, keeping it in _embedders.
    #    Before loading: from huggingface_hub.utils import logging as hf_logging; hf_logging.set_verbosity_error()
    # 2. vectors = model.encode(texts, normalize_embeddings=True); return np.asarray(vectors, dtype="float32").
    # SOLUTION START: TODO (Session 3): write embed(): follow the docstring and the numbered comments above
    name = config.EMBEDDING_MODEL
    if name not in _embedders:
        from huggingface_hub.utils import logging as hf_logging
        from sentence_transformers import SentenceTransformer
        hf_logging.set_verbosity_error()  # hides a harmless "Please set a HF_TOKEN" warning (no key is needed)
        _embedders[name] = SentenceTransformer(name)
    vectors = _embedders[name].encode(texts, normalize_embeddings=True)
    return np.asarray(vectors, dtype="float32")
    # SOLUTION END


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
    """Load, chunk, embed and index the corpus.

    documents: a list from load_documents(), or None to load config.CORPUS_DIR.
    Returns: {"index": <the index>, "chunks": <the chunks>, "settings": _settings()} (get_store() and search() use it).
    """
    # 1. documents = load_documents() if documents is None else documents; chunks = make_chunks(documents)
    # 2. vectors = embed([chunk["text"] for chunk in chunks])
    # 3. If faiss is not None: index = faiss.IndexFlatIP(vectors.shape[1]); index.add(vectors)
    #    (IP = inner product = cosine, because the vectors are normalized). Otherwise print
    #    "faiss is not installed: using plain numpy search instead (same results)" and index = NumpyIndex(vectors).
    # 4. Print f"Indexed {len(chunks)} chunks (CHUNK_SIZE=..., CHUNK_OVERLAP=..., CHUNK_BY_SECTION=...)" and return the dict.
    # SOLUTION START: TODO (Session 3): write build_store(): follow the docstring and the numbered comments above
    documents = load_documents() if documents is None else documents
    chunks = make_chunks(documents)
    vectors = embed([chunk["text"] for chunk in chunks])
    if faiss is not None:
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
    else:
        print("faiss is not installed: using plain numpy search instead (same results)")
        index = NumpyIndex(vectors)
    print(f"Indexed {len(chunks)} chunks (CHUNK_SIZE={config.CHUNK_SIZE}, CHUNK_OVERLAP={config.CHUNK_OVERLAP}, "
          f"CHUNK_BY_SECTION={config.CHUNK_BY_SECTION})")
    return {"index": index, "chunks": chunks, "settings": _settings()}
    # SOLUTION END


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

    store: the dict from build_store() / get_store(). k: None = config.TOP_K.
    Returns: a list of copies of the chunk dicts, each plus "score" (a Python float, higher = closer in meaning):
        [{"id": "x.txt#3", "source": "x.txt", "text": "...", "score": 0.68}, ...]
    """
    # 1. k = k or config.TOP_K. If store["settings"] != _settings(): print a warning to run build_store() again.
    # 2. scores, rows = store["index"].search(embed([query]), k)     (FAISS and NumpyIndex answer the same way)
    # 3. For score, row in zip(scores[0], rows[0]): skip row == -1 (FAISS pads with -1 when there are fewer
    #    than k chunks); otherwise append {**store["chunks"][row], "score": float(score)}.
    # 4. Return the list.
    # SOLUTION START: TODO (Session 3): write search(): follow the docstring and the numbered comments above
    k = k or config.TOP_K
    if store["settings"] != _settings():
        print("Warning: chunk/model/corpus settings changed since build_store(). Run build_store() again.")
    scores, rows = store["index"].search(embed([query]), k)
    results = []
    for score, row in zip(scores[0], rows[0]):
        if row == -1:
            continue
        results.append({**store["chunks"][row], "score": float(score)})
    return results
    # SOLUTION END
