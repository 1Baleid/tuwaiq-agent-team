# Sample corpus (placeholder)

Public placeholder documents, used until Group 3 delivers the real corpus.

| File | What it is |
|---|---|
| `docs/` | The documents the agent searches: `.txt`, `.md` and `.pdf` files. Every file in here is indexed. |
| `sources.csv` | One row per document: title, URL, date retrieved, licence, and what we changed. |
| `deadlines.csv` | The table behind the `get_deadline` tool (`name,date,note`, dates as `YYYY-MM-DD`). **The dates here are invented** for testing. |

The documents are Wikipedia articles (CC BY-SA 4.0), fixed to the revisions linked in `sources.csv`.

## Swapping in the real corpus

1. Make a new folder with the same layout, e.g. `data/campus/` containing `docs/`, `sources.csv` and `deadlines.csv`.
2. In `config.py`, set `CORPUS_DIR = ROOT / "data" / "campus"`.
3. Replace `eval/questions.json` with the real evaluation questions.
4. Run `python scripts/smoke_test.py`.

Keep personal or private data out of `docs/`: free LLM tiers may log what you send them.
