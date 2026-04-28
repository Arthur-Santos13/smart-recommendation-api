"""
TF-IDF vectorizer for item content.

Builds a feature matrix from a combination of item title, description and
tags. Tags receive higher weight by repeating them in the text corpus so the
vectorizer naturally boosts their TF score without needing custom tokenisation.
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from app.models.item import Item


def build_item_corpus(items: list[Item]) -> list[str]:
    """
    Combine title + description + tags into a single text string per item.
    Tags are repeated to give them higher TF weight in the final matrix.
    """
    corpus: list[str] = []
    for item in items:
        title = item.title or ""
        description = item.description or ""
        # Replace comma-separated tags with spaces and repeat them 3×
        raw_tags = item.tags or ""
        tags_tokens = " ".join(raw_tags.replace(",", " ").split())
        tags_boosted = " ".join([tags_tokens] * 3)

        text = f"{title} {description} {tags_boosted}".strip()
        corpus.append(text)
    return corpus


def build_tfidf_matrix(items: list[Item]):
    """
    Fit a TF-IDF vectorizer on the item corpus and return
    (vectorizer, tfidf_matrix) where tfidf_matrix has shape (n_items, n_features).
    """
    corpus = build_item_corpus(items)
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=5_000,
        sublinear_tf=True,
    )
    tfidf_matrix = vectorizer.fit_transform(corpus)
    return vectorizer, tfidf_matrix
