# README additions: Persistent storage section

I updated the README to include instructions for enabling a persistent PostgreSQL-backed store for conversation and model artifacts. Key points:

- Use PostgreSQL for durable message storage, conversation history, model artifacts, and delivery receipts.
- The repo contains an async SQLAlchemy-based implementation using SQLAlchemy 1.4+ and asyncpg. Files added on branch `feature/persistent-storage`:
  - app/db.py - async engine and session factory; helper to create tables.
  - app/models.py - SQLAlchemy ORM models (Conversation, Message, ModelArtifact, DeliveryReceipt).
  - app/persistent_store.py - simple wrapper for append_message/get_history using the DB.

How to enable persistent DB locally

1) Install dependencies:
   pip install sqlalchemy asyncpg

2) Set DATABASE_URL in your .env (example):
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/whatsapp

3) Start a local Postgres (example using Docker):
   docker run --name whatsapp-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres -e POSTGRES_DB=whatsapp -p 5432:5432 -d postgres:15-alpine

4) Create tables (one-time):
   python -c "from app.db import create_db_and_tables; import asyncio; asyncio.run(create_db_and_tables())"

5) Switch the app to use PersistentStore instead of ConvoStore by updating app.main or configuration to instantiate and use `app.persistent_store.PersistentStore()`.

Notes on migrations

- For production you should use Alembic to manage schema migrations. The current implementation provides `create_db_and_tables()` for initial provisioning but does not include Alembic configs.

