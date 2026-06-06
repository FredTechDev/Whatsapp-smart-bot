Update README: add provider parsing notes and how to run provider parsing tests

Added files:
- app/parse_message.py: normalizes Twilio and Meta payloads into a common internal shape.
- tests/test_provider_parsing.py: unit tests for Twilio and Meta sample payloads.

Run tests:
  pytest tests/test_provider_parsing.py -q
