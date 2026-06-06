# WhatsApp Smart Bot (MVP)

This repository provides a production-oriented scaffold for a WhatsApp bot that can run locally or in containerized/cloud environments. It supports multiple WhatsApp providers, short-lived conversational memory, an urgency classifier (rule-based by default, optional ML), and an OpenAI-powered reply generator (optional).

Key features

- Provider-agnostic messaging: works with Twilio (default) and Meta WhatsApp Business Cloud (select via `WHATSAPP_PROVIDER`).
- Urgency classification: rule-based classifier by default (low/medium/high). Optional ML classifier (TF‑IDF + LogisticRegression) available in branch `ml-and-openai` and enabled via `CLASSIFIER_MODE=ml`.
- Conversation store: Redis-backed, short-lived session history (default TTL 24h).
- Reply generation: OpenAI ChatCompletion integration (gpt-3.5-turbo by default) with fallback if `OPENAI_API_KEY` is not set.
- Provider payload normalization: Twilio and Meta payloads are normalized into a single internal shape so downstream code is provider-agnostic.
- Containerization: Dockerfile + docker-compose for local development. Nginx reverse-proxy and certbot compose override available in `add-nginx-infra` branch and `docker-compose.nginx.yml`.
- Kubernetes manifests: example Deployment/Service/Ingress in `k8s/deployment.yaml` (branch `add-nginx-infra`).
- CI: basic pytest workflow and optional GHCR publish workflow (see `.github/workflows/`).

Quick start — local (minimal)

1. Copy environment vars:

   ```bash
   cp .env.example .env
   # edit .env and fill TWILIO_* or META_* credentials, REDIS_URL, OPENAI_API_KEY (optional)
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start Redis (local or hosted). For local dev, easiest is docker:

   ```bash
   docker run -p 6379:6379 -d redis:7-alpine
   ```

4. Run the app:

   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. Configure your WhatsApp provider webhook to point to:

   ```text
   https://<your-host>/webhook
   ```

   - For Twilio: set the WhatsApp sandbox inbound webhook to `https://<your-host>/webhook`
   - For Meta: use the WhatsApp Cloud webhook endpoint (the webhook verify GET is supported at `/webhook`)

Quick start — with Docker Compose

1. Build & run (app + Redis):

   ```bash
   docker-compose up --build
   ```

2. Optional: run Nginx + certbot reverse-proxy (compose override included in the repo on the `add-nginx-infra` branch):

   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.nginx.yml up --build -d
   ```

Health check

- The app exposes a lightweight health endpoint: `GET /health`.
- Nginx config proxies `/health` — useful for readiness/liveness checks.

Configuration & env vars

- `WHATSAPP_PROVIDER`: `twilio` (default) or `meta`
- `TWILIO_SID`, `TWILIO_AUTH`, `TWILIO_WHATSAPP_NUMBER` — Twilio credentials
- `META_TOKEN`, `META_PHONE_NUMBER_ID`, `META_APP_SECRET`, `META_VERIFY_TOKEN` — Meta/WhatsApp Cloud credentials
- `REDIS_URL` — Redis connection string (default `redis://localhost:6379/0`)
- `OPENAI_API_KEY` — Optional for LLM-powered replies
- `CLASSIFIER_MODE` — `rule` (default) or `ml` to enable the scikit-learn classifier
- `MODEL_PATH` — path to a trained model when `CLASSIFIER_MODE=ml` (default `models/urgency_model.joblib`)
- `WEBHOOK_PUBLIC_URL` — set to the external webhook URL (useful when behind a proxy/ngrok)

Provider payloads & normalization

Incoming provider payloads (Twilio form posts, Meta JSON) are normalized into a single internal message shape by `app.parse_message.normalize_message()` with the fields:

- `provider`, `message_id`, `from`, `type` (`text` / `media` / `interactive` / `unknown`), `text`, `media` (list), `interactive`, `raw`.

This allows classification, storage, and reply generation to be provider-agnostic and reduces runtime parsing errors for different message types.

ML classifier

- The repo includes a TF‑IDF + LogisticRegression trainer and wrapper in the `ml-and-openai` branch.
- Train a model locally using:

  ```bash
  python app/train_classifier.py --input data/sample_labeled.csv --output models/urgency_model.joblib
  ```

- Enable ML at runtime with:

  ```bash
  export CLASSIFIER_MODE=ml
  export MODEL_PATH=models/urgency_model.joblib
  ```

Durable model management (recommended)

- For production, use the model-management scripts (train -> validate -> promote) so models are versioned and validated before activation. The workflow is:
  1. Train and save a candidate model artifact (joblib) including metadata.
  2. Validate the model on a holdout/test set with `app/validate_model.py` (thresholds configurable).
  3. Promote the validated model (atomic copy/pointer) to the runtime path, e.g. `models/active.joblib`.

Batch classification (classify historical chats)

You can export historical chat data (CSV/JSON) and run a batch classification job locally. Example CSV required columns: `message_id,from,timestamp,text`.

Example script (tools/batch_classify.py):

```python
# tools/batch_classify.py
import csv, joblib, sys
from pathlib import Path

MODEL_PATH = Path(sys.argv[1])  # e.g. models/urgency_model.joblib
INPUT_CSV = Path(sys.argv[2])   # export.csv
OUTPUT_CSV = Path(sys.argv[3])  # output.csv

model = joblib.load(MODEL_PATH)

with INPUT_CSV.open(newline='', encoding='utf-8') as inf, OUTPUT_CSV.open('w', newline='', encoding='utf-8') as outf:
    reader = csv.DictReader(inf)
    fieldnames = reader.fieldnames + ['predicted_label', 'confidence']
    writer = csv.DictWriter(outf, fieldnames=fieldnames)
    writer.writeheader()
    for row in reader:
        text = row.get('text','')
        if not text:
            row['predicted_label'] = ''
            row['confidence'] = ''
        else:
            probs = model.predict_proba([text])[0]
            idx = probs.argmax()
            label = model.classes_[idx]
            conf = float(probs[idx])
            row['predicted_label'] = label
            row['confidence'] = f"{conf:.4f}"
        writer.writerow(row)

print("Wrote", OUTPUT_CSV)
```

How to run:

```bash
python tools/batch_classify.py models/urgency_model.joblib export.csv export_scored.csv
```

OpenAI reply generator

- To enable contextual LLM replies set `OPENAI_API_KEY` in your environment or `.env` file.
- The reply generator uses a concise system prompt and recent conversation history (capped). LLM calls are rate-limited and timeboxed; on failures the system falls back to a short canned reply.

Webhook & security notes

- Signature validation: Meta HMAC (`X-Hub-Signature-256`) is validated using the raw request body. Twilio signatures are validated using the public webhook URL. Set `WEBHOOK_PUBLIC_URL` when behind a proxy/ngrok.
- Idempotency: Provider message IDs (Twilio `MessageSid`, Meta message id) are stored in Redis to avoid duplicate processing of re-delivered webhooks.
- Rate limiting: The app includes an observability scaffold and a plan for per-sender and global rate limiting to prevent abuse / runaway LLM costs. Configure and enable the Redis-backed rate-limiter in production.

Testing

- Unit tests live in `tests/`. Run all tests with:

  ```bash
  pytest -q
  ```

- Provider parsing tests:

  ```bash
  pytest tests/test_provider_parsing.py -q
  ```

- Signature validation tests:

  ```bash
  pytest tests/test_signature_validation.py -q
  ```

Observability & metrics

- Request-ID middleware, structured JSON logs, and Prometheus metrics are available on the `feature/observability` branch and integrated into the main app in later branches.
- Metrics endpoint: `GET /metrics` (Prometheus format).

Privacy, compliance & operational notes

- Consent & retention: Ensure you have the user's consent to process and store messages. Implement a configurable retention policy for conversation data.
- PII handling: Protect phone numbers and message content as personal data. Use cloud secrets managers or KMS to store credentials.
- Production deployment: Use HTTPS, validate webhooks, add readiness/liveness probes, resource requests/limits, and proper monitoring/alerting before exposing to real users.

Development branches of interest

- `add-nginx-infra` — Nginx config, `docker-compose.nginx.yml`, k8s example manifests and docs
- `ml-and-openai` — ML classifier, training script, sample data, and improved OpenAI reply generator
- `fix/webhook-verification`, `fix/background-worker`, `feature/observability`, `feature/llm-hardening`, `feature/provider-parsing` — recent fixes and features in progress

Need help?

If you want I can:
- Add `tools/batch_classify.py` into the repo and a `/classify` API endpoint (for ad-hoc classification),
- Add a Twilio export helper to fetch message history and build export CSVs,
- Implement the Redis-backed per-sender rate limiter and delivery retry logic,
- Help train a production-quality classifier from a labeled dataset you provide.

How to commit changes locally

1. Fetch and checkout a new branch:

   ```bash
   git checkout -b update-readme
   ```

2. Replace README.md with the content above (edit or paste), then:

   ```bash
   git add README.md
   git commit -m "Update README: provider parsing, batch classification, model management and usage"
   git push origin update-readme
   ```

3. Open a PR:
   - Web: https://github.com/FredTechDev/Whatsapp-smart-bot/pull/new/update-readme
   - Or CLI:

     ```bash
     gh pr create --base main --head update-readme --title "Update README: project status & features" --body "Updates README to document provider parsing, batch classification, model management, and usage."
     ```

