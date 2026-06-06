import pytest
import asyncio
from unittest.mock import patch, MagicMock
from app.reply_generator import generate_reply


@pytest.mark.asyncio
async def test_generate_reply_with_mocked_openai(monkeypatch):
    # Mock the sync OpenAI call used inside reply_generator
    mocked = MagicMock()
    class Choice:
        def __init__(self, text):
            self.text = text
            self.message = type('M', (), {'content': text})
    mocked.return_value = type('R', (), {'choices': [Choice('Mocked reply')]})

    monkeypatch.setattr('app.reply_generator._call_openai_sync', mocked)

    reply = await generate_reply('Hello', [{'text': 'previous message'}])
    assert 'Mocked reply' in reply
