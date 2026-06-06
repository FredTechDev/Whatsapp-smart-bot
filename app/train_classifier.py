import argparse
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib


def train(input_csv: str, output_path: str, test_size: float = 0.2, random_state: int = 42):
    df = pd.read_csv(input_csv)
    if "text" not in df.columns or "label" not in df.columns:
        raise SystemExit("Input CSV must contain 'text' and 'label' columns")
    X = df["text"].astype(str)
    y = df["label"].astype(str)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1,2), max_features=10000)),
        ("clf", LogisticRegression(max_iter=1000, class_weight='balanced'))
    ])

    pipeline.fit(X_train, y_train)

    preds = pipeline.predict(X_test)
    print(classification_report(y_test, preds))

    joblib.dump(pipeline, output_path)
    print(f"Saved model to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train urgency classifier")
    parser.add_argument("--input", required=True, help="Path to labeled CSV (columns: text,label)")
    parser.add_argument("--output", required=True, help="Output path for model joblib")
    args = parser.parse_args()
    train(args.input, args.output)
