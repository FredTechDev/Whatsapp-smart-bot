# Simple rule-based urgency classifier kept as a fallback and default implementation.
KEYWORDS_HIGH = {"emergency", "urgent", "help now", "asap", "please help", "immediately", "can't", "cant", "cannot", "can't breathe", "911"}
KEYWORDS_MED = {"issue", "problem", "not working", "error", "fail", "unable", "bug", "crash"}


def classify_urgency_rule(text: str):
    t = (text or "").lower()
    for k in KEYWORDS_HIGH:
        if k in t:
            return "high", 0.99
    for k in KEYWORDS_MED:
        if k in t:
            return "medium", 0.75
    return "low", 0.3
