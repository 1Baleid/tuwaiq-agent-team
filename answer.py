"""
answer.py - Session 3: answers you can trust.

Find the best chunks, give them to the LLM labelled with their id, and get back an answer that
cites them, like "Unexcused absences over 20% give a DN grade [01-05_Attendance_And_Withdrawal.md#3]", or "I don't know"
when the documents do not contain the answer.

    import rag, answer
    store = rag.build_store()
    result = answer.answer_question(store, "What share of absences leads to a DN grade?")
    print(result["answer"], result["sources"])
"""
import re

import config
import llm
import rag

I_DONT_KNOW = "I don't know based on the documents."

SYSTEM_PROMPT = f"""You answer questions using ONLY the sources you are given.
After each fact, cite its source exactly as it is labelled, like [01-05_Attendance_And_Withdrawal.md#3].
If the sources do not contain the answer, reply exactly: {I_DONT_KNOW}"""


def format_sources(hits):
    """Label each chunk with its id, so the LLM can cite it.

    hits: the list from rag.search(). Returns: ONE str, the blocks joined with a blank line ("\n\n");
    each block is "[<id>]", a new line, then the chunk text:
        [01-05_Attendance_And_Withdrawal.txt#3]
        If the number of unexcused absences ...
    """
    # 1. Return "\n\n".join(f"[{hit['id']}]\n{hit['text']}" for hit in hits).
    # SOLUTION START: TODO (Session 3): write format_sources(): follow the docstring and the numbered comments above
    return "\n\n".join(f"[{hit['id']}]\n{hit['text']}" for hit in hits)
    # SOLUTION END


def build_messages(question, hits):
    """The chat messages for the LLM.

    Returns: a list of exactly two dicts:
        [{"role": "system", "content": SYSTEM_PROMPT},
         {"role": "user", "content": "Sources:\n<format_sources(hits)>\n\nQuestion: <question>"}]
    """
    # 1. Build the user text as f"Sources:\n{format_sources(hits)}\n\nQuestion: {question}".
    # 2. Return the two messages above.
    # SOLUTION START: TODO (Session 3): write build_messages(): follow the docstring and the numbered comments above
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Sources:\n{format_sources(hits)}\n\nQuestion: {question}"},
    ]
    # SOLUTION END


def cited_sources(reply, known_ids):
    """Which chunks does the reply cite? Only ids that really exist count.

    reply: the LLM's answer. known_ids: a set of real chunk ids.
    Returns: a list of ids in the order they first appear, each once, e.g. ["x.txt#3", "y.md#1"].
    Footnote marks like [4] in the documents are not chunk ids ("#" + number is required), so they are ignored.
    """
    # 1. cited = re.findall(r"\[([^\[\]]+?#\d+)\]", reply)
    # 2. Return list(dict.fromkeys(chunk_id for chunk_id in cited if chunk_id in known_ids)).
    # SOLUTION START: TODO (Session 3): write cited_sources(): follow the docstring and the numbered comments above
    cited = re.findall(r"\[([^\[\]]+?#\d+)\]", reply)
    return list(dict.fromkeys(chunk_id for chunk_id in cited if chunk_id in known_ids))
    # SOLUTION END


def answer_question(store, question):
    """Answer a question from the documents, with two layers of "I don't know".

    Returns: a dict with exactly these keys: {"answer": str, "sources": [cited chunk ids], "hits": [the search results]}
    """
    # 1. hits = rag.search(store, question)
    # 2. Layer 1 (code): if there are no hits, or hits[0]["score"] < config.MIN_SCORE (read it every call), return
    #    {"answer": I_DONT_KNOW, "sources": [], "hits": hits} WITHOUT calling the LLM.
    # 3. Layer 2 (prompt): reply = llm.chat(build_messages(question, hits)); SYSTEM_PROMPT tells the LLM to say
    #    I_DONT_KNOW when the sources lack the answer.
    # 4. Return {"answer": reply, "sources": cited_sources(reply, {hit["id"] for hit in hits}), "hits": hits}.
    # SOLUTION START: TODO (Session 3): write answer_question(): follow the docstring and the numbered comments above
    hits = rag.search(store, question)
    if not hits or hits[0]["score"] < config.MIN_SCORE:
        return {"answer": I_DONT_KNOW, "sources": [], "hits": hits}
    reply = llm.chat(build_messages(question, hits))
    return {"answer": reply, "sources": cited_sources(reply, {hit["id"] for hit in hits}), "hits": hits}
    # SOLUTION END
