# WhatsApp Smart Bot (MVP)

This repository provides a production-oriented scaffold for a WhatsApp bot that can run locally or in containerized/cloud environments. It supports multiple WhatsApp providers, short-lived conversational memory, an urgency classifier (rule-based by default, optional ML), and an OpenAI-powered reply generator (optional).

Key features

- Provider-agnostic messaging: works with Twilio (default) and Meta WhatsApp Business Cloud (select via WHATSAPP_PROVIDER).
- Urgency classification: rule-based classifier by default (low/medium/high). Optional ML classifier (TF‑IDF + LogisticRegression) available in branch `ml-and-openai` and enabled via CLASSIFIER_MODE=ml.
- Conversation store: Redis-backed, short-lived session history (default TTL 24h).
- Reply generation: OpenAI ChatCompletion integration (gpt-3.5-turbo by default) with fallback if OPENAI_API_KEY is not set.
- Containerization: Dockerfile + docker-compose for local development. Nginx reverse-proxy and certbot compose override available in `add-nginx-infra` branch and `docker-compose.nginx.yml`.
- Kubernetes manifests: example Deployment/Service/Ingress in `k8s/deployment.yaml` (branch `add-nginx-infra`).
- CI: basic pytest workflow and optional GHCR publish workflow (see `.github/workflows/`).

Quick start — local (minimal)

1. Copy environment vars:

   cp .env.example .env
   # edit .env and fill TWILIO_* or META_* credentials, REDIS_URL, OPENAI_API_KEY (optional)

2. Install dependencies:

   pip install -r requirements.txt

3. Start Redis (local or hosted). For local dev, easiest is docker:

   docker run -p 6379:6379 -d redis:7-alpine

4. Run the app:

   uvicorn app.main:app --reload --port 8000

5. Configure your WhatsApp provider webhook to point to:

   https://<your-host>/webhook

   - For Twilio: set the WhatsApp sandbox inbound webhook to https://<your-host>/webhook
   - For Meta: use the WhatsApp Cloud webhook endpoint (the webhook verify GET is supported at /webhook)

Quick start — with Docker Compose

1. Build & run (app + Redis):

   docker-compose up --build

2. Optional: run Nginx + certbot reverse-proxy (compose override included in the repo on the `add-nginx-infra` branch):

   docker-compose -f docker-compose.yml -f docker-compose.nginx.yml up --build -d

Health check

- The app exposes a lightweight health endpoint: GET /health
- Nginx config proxies /health — useful for readiness/liveness checks

Configuration & env vars

- WHATSAPP_PROVIDER: `twilio` (default) or `meta`
- TWILIO_SID, TWILIO_AUTH, TWILIO_WHATSAPP_NUMBER — Twilio credentials
- META_TOKEN, META_PHONE_NUMBER_ID, META_APP_SECRET, META_VERIFY_TOKEN — Meta/WhatsApp Cloud credentials
- REDIS_URL — Redis connection string (default redis://localhost:6379/0)
- OPENAI_API_KEY — Optional for LLM-powered replies
- CLASSIFIER_MODE — `rule` (default) or `ml` to enable the scikit-learn classifier
- MODEL_PATH — path to a trained model when CLASSIFIER_MODE=ml (default models/urgency_model.joblib)

ML classifier

- The repo includes a TF‑IDF + LogisticRegression trainer and wrapper in the `ml-and-openai` branch.
- Train a model locally using:

  python app/train_classifier.py --input data/sample_labeled.csv --output models/urgency_model.joblib

- Enable ML at runtime with:

  export CLASSIFIER_MODE=ml
  export MODEL_PATH=models/urgency_model.joblib

OpenAI reply generator

- To enable contextual LLM replies set OPENAI_API_KEY in your environment or .env file.
- The reply generator will use a concise system prompt and include recent conversation history. If the OpenAI call fails, the app falls back to a short canned reply.

Docker image publishing

- A GitHub Actions workflow can be configured to build and push the container image to GHCR. See `.github/workflows/publish-ghcr.yml` and `docs/GHCR_PUBLISH.md` for details (may be present on a branch if not on main).

Testing

- Unit tests live in `tests/` and can be run with pytest:

  pytest -q

Security & production notes

- Validate incoming webhooks. The app contains provider-specific request validation hooks for Twilio and Meta; configure secrets and verify signatures before enabling in production.
- Keep credentials out of source control. Use your cloud provider secrets manager or Kubernetes Secrets in production.
- For production deployments:
  - Terminate TLS at your ingress/load balancer or inside the Nginx reverse proxy (cert-manager or certbot).
  - Add readiness & liveness probes, resource requests/limits, and proper monitoring/logging.
  - Use a managed Redis (recommended) and persist the model in a secure artifact store or bake into the image.

Development branches of interest

- add-nginx-infra — Nginx config, docker-compose.nginx.yml, k8s example manifests and docs
- ml-and-openai — ML classifier, training script, sample data, and improved OpenAI reply generator

Need help?

If you want I can:
- Open a PR to merge infra or ML changes into main
- Help train a production-quality classifier from a labeled dataset you provide
- Tune the OpenAI prompts and add rate-limiting / cost controls
- Help wire up GHCR publishing and CI for automated image builds

