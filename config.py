# config.py
# Every setting for the workshop lives in this one file.
# Change a value, run your code again, and watch what happens.
from pathlib import Path

ROOT = Path(__file__).resolve().parent  # the project folder (where this file is)

# ------------------------------------------------------------
# 1. Which LLM to use  (the ONE switch)
# ------------------------------------------------------------
# "groq", "gemini", "openrouter" or "local" (a small open model run by Ollama)
LLM_PROVIDER = "groq"

# All providers speak the same "OpenAI-compatible" API, so switching provider
# only changes the address (base_url), the model name and which key to use.
# "options" are extra settings sent with every request to that provider.
PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "openai/gpt-oss-20b",              # or "openai/gpt-oss-120b" (smarter, slower)
        "key_name": "GROQ_API_KEY",
        "options": {"temperature": 0, "reasoning_effort": "low"},  # gpt-oss thinks first; "low" = think briefly
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-3.5-flash-lite",
        "key_name": "GEMINI_API_KEY",
        "options": {},                              # Gemini 3 ignores temperature, so we send none
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "google/gemma-4-26b-a4b-it:free",
        "key_name": "OPENROUTER_API_KEY",
        "options": {"temperature": 0},
    },
    "local": {
        "base_url": "http://localhost:11434/v1",    # Ollama running on this machine / Colab VM
        "model": "qwen3:4b-instruct",
        "key_name": None,                           # no key needed
        "options": {"temperature": 0},
    },
}

LLM_TIMEOUT_SECONDS = 60     # give up on ONE LLM call after this many seconds
LLM_MAX_RETRIES = 3          # Session 2: how many times to retry a failed call (429, timeout, ...)
MAX_OUTPUT_TOKENS = 800      # longest reply we accept (models that "think" first need room)

# ------------------------------------------------------------
# 2. Documents and search  (Session 3)
# ------------------------------------------------------------
# The same 34 KFUPM documents come in three folders (see data/README.md). Pick one:
#   data/kfupm_raw         the default, used in the slides: one plain-text dump, no headings, lists or paragraphs
#   data/kfupm_structured  the same information as Markdown: one "## heading" section per complete rule
#                          (best with CHUNK_BY_SECTION = True)
#   data/kfupm_pdf         the original PDFs
# Or set the CORPUS_DIR environment variable, e.g. CORPUS_DIR=data/kfupm_structured, without editing this file.
import os
CORPUS_DIR = ROOT / os.environ.get("CORPUS_DIR", "data/kfupm_raw")
DEADLINES_FILE = ROOT / "data" / "deadlines.csv"   # the table behind the get_deadline tool

# Small (90 MB) and fast, English only. It reads at most 256 tokens per chunk (about 1000 characters of our
# documents); the rest of a longer chunk is not searched.
# For Arabic documents use "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2" (470 MB).
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 500             # characters per chunk
CHUNK_OVERLAP = 100          # characters shared by two neighbouring chunks
CHUNK_BY_SECTION = False     # True = one chunk per "## heading" section, labelled with its heading (see rag.make_chunks)
TOP_K = 4                    # how many chunks one search returns
MIN_SCORE = 0.40             # Session 3: if no chunk scores this high, answer "I don't know"

# ------------------------------------------------------------
# 3. The agent  (Sessions 1-2)
# ------------------------------------------------------------
MAX_STEPS = 5                # most LLM calls the agent may make for ONE question
AGENT_TIMEOUT_SECONDS = 120  # most time the agent may spend on ONE question
MAX_HISTORY_TURNS = 3        # earlier questions + answers the agent remembers in a conversation
VERBOSE = True               # print every step the agent takes
LOG_FILE = ROOT / "logs" / "agent_log.jsonl"   # Session 2: one line per agent event

# ------------------------------------------------------------
# 4. Evaluation  (Session 5)
# ------------------------------------------------------------
EVAL_FILE = ROOT / "eval" / "questions.json"
