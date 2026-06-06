from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# Counters
WEBHOOK_REQUESTS = Counter("webhook_requests_total", "Webhook requests received", ["provider", "status"])
SIGNATURE_FAILURES = Counter("signature_validation_failures_total", "Signature validation failures", ["provider"])
LLM_CALLS = Counter("llm_calls_total", "OpenAI/LLM calls", ["success"])
MESSAGES_SENT = Counter("messages_sent_total", "Messages sent via provider", ["success"])

WEBHOOK_LATENCY = Histogram("webhook_latency_seconds", "Webhook processing latency")


def metrics_endpoint() -> Response:
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
