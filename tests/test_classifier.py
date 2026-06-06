from app.classifier import classify_urgency


def test_classify_high():
    text = "This is urgent I need help now!"
    urgency, score = classify_urgency(text)
    assert urgency == "high"


def test_classify_medium():
    text = "I'm seeing an error when I try to login"
    urgency, score = classify_urgency(text)
    assert urgency == "medium"


def test_classify_low():
    text = "Hello, I wanted to ask about pricing"
    urgency, score = classify_urgency(text)
    assert urgency == "low"
