# ML & OpenAI usage

This document explains how to train the TF-IDF + LogisticRegression urgency classifier and how to enable OpenAI replies.

Training the classifier
1. Install requirements: pip install -r requirements.txt
2. Train using the sample data or your own labeled CSV (columns: text,label):
   python app/train_classifier.py --input data/sample_labeled.csv --output models/urgency_model.joblib
3. The output model will be saved to models/urgency_model.joblib. Commit it if you want it in the repo (optional).

Using the ML classifier at runtime
- Set environment variable to use the ML classifier:
  export CLASSIFIER_MODE=ml
- Ensure MODEL_PATH (or settings.MODEL_PATH) points to the trained model file.

OpenAI reply generator
- Set OPENAI_API_KEY in your .env file or environment variables.
- The reply generator will call OpenAI ChatCompletion (gpt-3.5-turbo by default). If the key is missing or OpenAI fails, the system falls back to a short canned reply.

Notes
- The app defaults to the rule-based classifier if CLASSIFIER_MODE is not set to 'ml' or if the model fails to load.
- Keep model files out of source control for larger models; store in an artifacts bucket or volume for production.
