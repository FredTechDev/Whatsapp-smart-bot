import os
import joblib
from app.config import settings
from typing import Tuple

# lazy load to avoid startup cost
_model = None


def classify_urgency_ml(text: str) -> Tuple[str, float]:
    global _model
    model_path = os.getenv("MODEL_PATH") or settings.MODEL_PATH
    if _model is None:
        try:
            _model = joblib.load(model_path)
        except Exception:
            # If model not available, fall back to rule-based
            from app.classifier_rule import classify_urgency_rule
            return classify_urgency_rule(text)
    try:
        probs = _model.predict_proba([text])[0]
        idx = probs.argmax()
        label = _model.classes_[idx]
        confidence = float(probs[idx])
        return label, confidence
    except Exception:
        from app.classifier_rule import classify_urgency_rule
        return classify_urgency_rule(text)
