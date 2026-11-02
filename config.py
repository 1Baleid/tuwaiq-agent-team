# config.py
# Every setting for the workshop lives in this one file.
# Change a value, run your code again, and watch what happens.

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
