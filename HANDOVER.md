# Handover: Group 2 technical work (starter repo, LLM access, Session 5)

From Abdullah (Group 2 technical lead) to the new owner, 2026-11-02. Start here.

## The two repos

| Repo | Who uses it | What is in it |
|---|---|---|
| **Team repo** (this one): https://github.com/1Baleid/tuwaiq-agent-team | The team: you, and Groups 4 and 5 for their notebooks | Branches `solutions` (the real code) and `main` (generated with TODOs), plus internal docs: `HANDOVER.md`, `docs/handover/`, `docs/s5_instructor_notes.md`, `docs/dry_run_log_template.md` |
| **Student repo**: https://github.com/1Baleid/tuwaiq-agent-workshop | Participants, through the Colab link | The same two branches **without** those internal files. Never edit it by hand |

**Updating what students get:**
1. Edit and commit on `solutions`.
2. Run `python scripts/make_main.py`, which rebuilds `main`.
3. Run `python scripts/publish_students.py`, which copies both branches to the student repo.

## Status of the work (tickets T1–T7)

| Ticket | Status | What is left | Details |
|---|---|---|---|
| T1 LLM options | Done | Real API latency (needs keys) | `docs/llm_options.md` |
| T2 Access decision | Partly done | Run the 4 load-test commands with real keys; approve the provider | `docs/llm_decision.md` |
| T3 Starter repo | Done on a laptop | Check it once on a fresh Colab | `README.md`, `docs/handover/T3.md` |
| T4 Session 5 pack | Done | Re-run on the chosen provider | `docs/s5_instructor_notes.md` |
| T5 Pre-work | Done | Fill in 3 placeholders, test one new Google key, send by Day 7 | `docs/prework.md` |
| T6 Known errors | Done | Add what the dry runs find | `docs/known_errors.md` |
| T7 Dry-run fixes | Not started (waits for the dry runs) | Collect the logs, fix, mark fixed/accepted/open | `docs/dry_run_log_template.md` |

Each `docs/handover/T<n>.md` has the details: what was built, how to check it, decisions and risks.

## Your first steps

1. **Set up:** clone the team repo, then follow "On a laptop" in `README.md`, using a short folder path on Windows.
2. **Keys:** copy `.env.example` to `.env` and add your own `GROQ_API_KEY` and `GEMINI_API_KEY`.
3. **Finish T2:** run the 4 commands at the end of `docs/llm_decision.md` and put the results in its table.
4. **Re-test on Groq:**
   - `python scripts/smoke_test.py` (expect 9 PASS).
   - `notebooks/s5_evaluate.ipynb` (expect 7/10 before the fixes, 10/10 after).
5. **Colab:** open `notebooks/00_setup.ipynb` from the student repo in a fresh Colab and run it. Expect "All good!" and "Backup key works.". Then run Plan B on a T4 GPU.
6. **Pre-work:** give `docs/prework.md` to Group 6 with the placeholders filled in (deadline, contact, Colab link).
7. **Dry runs (Days 5–6):** testers fill in `docs/dry_run_log_template.md`. Fix each item, and add new errors to `docs/known_errors.md`.

## Decisions already made (with reasons in the docs)

- **Provider:** Groq `openai/gpt-oss-20b`, one free key per student, plus a Gemini backup key (still needs the program leads' OK).
  - **Fallback:** a local model, `qwen3:4b-instruct`, through Ollama in each student's own Colab GPU runtime. The one switch is `LLM_PROVIDER` in `config.py`.
- **Tool calls are plain JSON in the model's reply,** not native tool calling. That works on every provider and on the local model.
- **Document search is a tool** (`search_docs`). **Citations look like `[file.txt#3]`.**
- **FAISS, not ChromaDB.**
- **Laptop versions are pinned to Colab's** (Python 3.13). In Colab, only `faiss-cpu` and `pypdf` are installed.

## Risks to watch

- **Every free LLM API is 18+ only.** Under-18 students use Plan B. The sign-up form needs an age question.
- **Groq free tier:** 8,000 tokens per minute per student, so a Session 5 evaluation run takes a few minutes.
- **Free Colab does not promise a GPU.** Ask the venue IT to allow `*.prod.r.colab.dev`.
- **Model names change monthly.** If a provider retires a model, update `PROVIDERS` in `config.py`.
- **Both repos are public.** Never commit `.env` or keys; `.gitignore` already blocks `.env`. The team repo contains the Session 5 answers, so share only the student repo with participants.

## Nothing secret is stored here

There are no keys in the repo or its history. Everyone uses their own keys: Colab Secrets in Colab, `.env` on a laptop.
