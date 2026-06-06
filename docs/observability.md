# Observability notes

This doc explains how observability is wired into the app and how to run metrics locally.

What was added

- RequestIDMiddleware (app.middleware.RequestIDMiddleware): generates or forwards X-Request-Id and logs request completion with duration.
- Structured JSON logging (app.logging_config.configure_logging) with a simple JSON formatter.
- Prometheus metrics (app.metrics) exposing basic counters and a /metrics endpoint.

How to enable and run locally

1. Install extra requirements:
   pip install prometheus_client

2. Start the app (example):
   uvicorn app.main:app --reload --port 8000

3. Hit /metrics to see counters:
   curl http://localhost:8000/metrics

Instrumentation points

- WEBHOOK_REQUESTS.labels(provider, status).inc()
- SIGNATURE_FAILURES.labels(provider).inc()
- LLM_CALLS.labels(success="true"/"false").inc()
- MESSAGES_SENT.labels(success="true"/"false").inc()

Notes

- This is a lightweight observability scaffold. For production consider:
  - Using OpenTelemetry for distributed tracing
  - Pushing metrics to a pushgateway or remote write pipeline
  - Adding logs correlation in external systems (e.g., linking Sentry events to request_id)
