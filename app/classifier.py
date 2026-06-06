# Simple rule-based urgency classifier. Replace with sklearn/transformer later.
KEYWORDS_HIGH = {"emergency", "urgent", "help now", "asap", "please help", "immediately", "can't", "cant", "cannot", "can't breathe"}
KEYWORDS_MED = {"issue", "problem", "not working", "error", "fail", "unable"}


def classify_urgency(text: str):
    t = (text or "").lower()
    for k in KEYWORDS_HIGH:
        if k in t:
            return "high", 0.99
    for k in KEYWORDS_MED:
        if k in t:
            return "medium", 0.75
    return "low", 0.3
