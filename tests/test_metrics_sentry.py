import pytest
from unittest.mock import patch


def test_metrics_registration():
    # Import module to ensure metrics are registered
    import app.metrics_extra as me
    assert hasattr(me, 'LLM_CALLS')
    assert hasattr(me, 'WORKER_QUEUE_DEPTH')


def test_sentry_init(monkeypatch):
    # Ensure sentry init is called when DSN is present
    import app.sentry_init as si
    called = {}
    def fake_init(*args, **kwargs):
        called['ok'] = True
    monkeypatch.setattr('sentry_sdk.init', fake_init)
    # monkeypatch settings
    import app.config as cfg
    old = cfg.settings.SENTRY_DSN
    cfg.settings.SENTRY_DSN = 'http://example.com'
    try:
        si.init_sentry()
        assert called.get('ok')
    finally:
        cfg.settings.SENTRY_DSN = old
