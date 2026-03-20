from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, f1_score
from textblob import TextBlob
import joblib, json
from config.logging_config import get_logger

logger = get_logger('train')


def _make_weak_labels(texts: list[str]) -> list[int]:
    """Use TextBlob polarity as weak supervision — no manual labelling needed."""
    return [1 if TextBlob(t).sentiment.polarity > 0 else 0 for t in texts]


def train_sentiment_model(
    texts: list[str] = None,
    labels: list[int] = None,
    data_path: str = None,
    model_path: str = 'models/sentiment_model.pkl',
) -> dict:
    # Accept either pre-loaded data or a JSON file path
    if texts is None and data_path:
        with open(data_path) as f:
            articles = json.load(f)
        texts = [a['title'] + ' ' + (a.get('description') or '') for a in articles]

    if labels is None:
        labels = _make_weak_labels(texts)

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42
    )

    model = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
        ('clf',   LogisticRegression(max_iter=200, C=1.0)),
    ])
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    metrics = {
        'accuracy': round(accuracy_score(y_test, preds), 4),
        'f1_score': round(f1_score(y_test, preds, average='weighted'), 4),
        'train_size': len(X_train),
        'test_size':  len(X_test),
    }
    logger.info(f'Training complete: {metrics}')
    logger.info('\n' + classification_report(y_test, preds))

    joblib.dump(model, model_path)
    logger.info(f'Model saved to {model_path}')
    return metrics
