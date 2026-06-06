import pytest
from app.train_classifier import train
from sklearn.pipeline import Pipeline
import joblib
import os


def test_train_and_predict(tmp_path):
    # train on sample data and ensure model saves and can predict
    input_csv = os.path.join(os.getcwd(), "data", "sample_labeled.csv")
    output = tmp_path / "model.joblib"
    train(input_csv, str(output))
    assert output.exists()
    model = joblib.load(str(output))
    assert isinstance(model, Pipeline)
    # quick prediction checks
    pred = model.predict(["This is urgent, please help now"])[0]
    assert pred in {"high", "medium", "low"}
