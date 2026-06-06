import json
from app.parse_message import normalize_message


def make_twilio_form():
    return {
        "Body": "Hello from Twilio",
        "From": "whatsapp:+14155551234",
        "MessageSid": "SM12345",
        "NumMedia": "1",
        "MediaUrl0": "https://example.com/image.jpg",
        "MediaContentType0": "image/jpeg"
    }


def make_meta_payload():
    return {
      "entry": [
        {
          "changes": [
            {
              "value": {
                "messages": [
                  {
                    "from": "14155551234",
                    "id": "wamid.HBgM...",
                    "text": {"body": "Hello from Meta"},
                    "type": "text"
                  }
                ]
              }
            }
          ]
        }
      ]
    }


def test_twilio_normalize():
    form = make_twilio_form()
    norm = normalize_message("twilio", form)
    assert norm["provider"] == "twilio"
    assert norm["message_id"] == "SM12345"
    assert norm["from"] == "whatsapp:+14155551234"
    assert norm["text"] == "Hello from Twilio"
    assert len(norm["media"]) == 1


def test_meta_normalize():
    payload = make_meta_payload()
    norm = normalize_message("meta", payload)
    assert norm["provider"] == "meta"
    assert norm["message_id"] == "wamid.HBgM..."
    assert norm["from"] == "whatsapp:14155551234"
    assert norm["text"] == "Hello from Meta"
