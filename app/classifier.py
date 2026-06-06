from app.config import settings
from typing import Tuple

# Wrapper that delegates to rule-based or ML classifier depending on settings.CLASSIFIER_MODE

def classify_urgency(text: str) -> Tuple[str, float]:
    mode = (settings.CLASSIFIER_MODE or "rule").lower()
    if mode == "ml":
        try:
            from app.classifier_ml_wrapper import classify_urgency_ml
            return classify_urgency_ml(text)
        except Exception:
            # fallback to rule-based
            from app.classifier_rule import classify_urgency_rule
            return classify_urgency_rule(text)
    else:
        from app.classifier_rule import classify_urgency_rule
        return classify_urgency_rule(text)
