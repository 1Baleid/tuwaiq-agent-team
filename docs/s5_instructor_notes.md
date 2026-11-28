# Session 5: instructor notes (technical pack)

Notebook: `notebooks/s5_evaluate.ipynb`. On `main` the three fix cells are TODOs; on `solutions` they hold
working fixes. The demo format and rubric are handled separately.

## What students see

`eval/questions.json` has 9 questions (the KFUPM set). With working Sessions 1–3 code, the first run should give
**6 of 9**: the failing rows are the three **planted** questions below. After the three fixes it should give
**9 of 9**. Not re-tested yet with the KFUPM documents and OpenRouter + DeepSeek: run it before the session.
q9 can also pass early, because the real calendar (`07_Academic_Calendar_Current_Semester`) is in the documents
and the agent may find the date with `search_docs` instead of `get_deadline`.

| Question | What fails | The clue students should find | Fix (cell) | Skill |
|---|---|---|---|---|
| **q8** "How much does one transcript cost when requested from outside Dhahran?" | Answer "I don't know", no source | Building the index prints `Skipped 1 file(s) this loader cannot read: 32_Transcripts_From_Outside_Dhahran.html` | **Fix 1:** `rag.read_file` also reads `.html` (drop the tags), then `rag.get_store(rebuild=True)` | S3: loading documents |
| **q9** "What is the last day to drop a course without a permanent record?" | Answer "I don't know" | `explain("q9")` shows `get_deadline` called with a name like "add/drop deadline", and the tool answering `No deadline called …` | **Fix 2:** `tools.find_deadline` picks the deadline sharing the most words with the asked name | S1: tools |
| **q10** "When is the course withdrawal deadline?" | Answer "I don't know" or "date not valid" | `explain("q10")` shows the tool answering `The date of 'Course withdrawal deadline' … is not a valid YYYY-MM-DD date`; the CSV row says `03/12/2026` | **Fix 3:** `tools.parse_date` accepts `03/12/2026` as well as `2026-12-03` | S2: errors and messy data |

Why these three: they fail **whatever LLM is used**, because the information is missing or unreadable rather
than the model being weak. Each one is discovered by reading the agent's steps (`explain()`), not by guessing.

## Running it in the room

* The fixes change functions in memory only; no project file is modified. To show "before" again,
  use **Runtime → Restart session** and run from the top.
* A non-planted question can also fail, because LLM answers vary between runs and providers. That is a good
  discussion too: run `explain()` on it.
* Each question takes about 1–5 s with Groq or a GPU local model. A full run of 9 questions makes about 20–30
  LLM calls, roughly 25–40K tokens (our estimate). Groq's free tier allows **8K tokens per minute** and
  200K per day per student. So on Groq expect a run to be slowed by 429 "rate limit" waits (the agent
  retries automatically) to **about 4–5 minutes**, and plan **at most 2–3 full runs per student**. This is
  an estimate until the keyed load test (T2) is run; the local model has no such limits.
* Results are saved to `results/eval_before_*.csv` and `results/eval_after_*.csv` for the demo.

## When the real evaluation set arrives (Group 3)

Replace `eval/questions.json`. Keep the same fields (`id`, `question`, `expected_answer`, `source`,
`keywords`), where `source` is a file name, `tool:<name>`, or `null` for "I don't know". Then plant 2–3
failures the same way:
1. Leave one document in a format the loader does not read (e.g. `.html` or `.docx`).
2. Ask about one deadline with different words than its name in `deadlines.csv`.
3. Type one date in the wrong format.

Re-test before the dry run: the first run must fail **only** on the planted questions.
