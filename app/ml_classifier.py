import joblib
from typing import Tuple
from sklearn.pipeline import Pipeline

_model = None


def load_model(path: str) -> Pipeline:
    global _model
    if _model is None:
        _model = joblib.load(path)
    return _model


def predict_text(model: Pipeline, text: str) -> Tuple[str, float]:
    """Return (label, confidence)"""
    if not text:
        return "low", 0.0
    probs = model.predict_proba([text])[0]
    idx = probs.argmax()
    label = model.classes_[idx]
    confidence = float(probs[idx])
    return label, confidence
