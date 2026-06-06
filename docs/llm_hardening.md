LLM hardening notes

This change implements safer OpenAI/LLM usage:

- Rate limiting: a simple per-process rate limiter using aiolimiter (optional). Configure LLM_RATE_LIMIT_RPS in the .env.
- Timeouts: OpenAI calls are wrapped with asyncio.wait_for and will timeout after LLM_TIMEOUT_SECONDS (default 10s).
- History caps: only the most recent LLM_MAX_HISTORY_MESSAGES are sent to the model to avoid unbounded prompts.
- Retries: network/SDK errors are retried with exponential backoff via tenacity.
- Fallback: if OpenAI is unavailable or the request times out, a short canned reply is used.

Environment variables (defaults set in app/config.py):
- LLM_MODEL (default: gpt-3.5-turbo)
- LLM_RATE_LIMIT_RPS (default: 1.0)
- LLM_MAX_HISTORY_MESSAGES (default: 8)
- LLM_TIMEOUT_SECONDS (default: 10)
- LLM_MAX_TOKENS (default: 200)

Install extra requirements:
  pip install aiolimiter tenacity

