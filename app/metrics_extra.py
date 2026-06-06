from prometheus_client import Counter, Gauge

# LLM token usage (best-effort approximation)
LLM_TOKEN_USAGE = Counter("llm_token_usage_total", "Estimated LLM token usage (best-effort)", ["model", "success"])
# LLM call success/failure
LLM_CALLS = Counter("llm_calls_total", "Number of LLM calls", ["success"])
# Worker queue depth
WORKER_QUEUE_DEPTH = Gauge("worker_queue_depth", "Background worker queue depth")
# Rate limit events (global / per_sender)
RATE_LIMIT_EVENTS = Counter("rate_limit_events_total", "Rate limit events", ["type"])
# Message send retries
MESSAGES_SEND_RETRIES = Counter("messages_send_retries_total", "Outbound message send retries", ["provider"])


def inc_llm_calls(success: bool):
    LLM_CALLS.labels(success=str(success).lower()).inc()


def inc_llm_tokens(model: str, tokens: int, success: bool):
    try:
        LLM_TOKEN_USAGE.labels(model=model, success=str(success).lower()).inc(tokens)
    except Exception:
        # metrics client may not accept large floats; ignore errors
        pass


def set_worker_queue_depth(n: int):
    try:
        WORKER_QUEUE_DEPTH.set(n)
    except Exception:
        pass


def inc_rate_limit_event(kind: str = "global"):
    RATE_LIMIT_EVENTS.labels(type=kind).inc()


def inc_message_retry(provider: str = "twilio"):
    MESSAGES_SEND_RETRIES.labels(provider=provider).inc()
