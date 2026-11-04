import re

from typing import Literal

POSITIVE = {
    "love",
    "loved",
    "loving",
    "brilliant",
    "wonderful",
    "great",
    "excellent",
    "enjoyed",
    "enjoy",
    "beautiful",
    "compelling",
    "satisfying",
    "favourite",
    "favorite",
    "delightful",
    "gripping",
    "perfect",
    "recommend",
    "recommended",
    "amazing",
    "charming",
    "vivid",
    "superb",
    "moving",
    "best",
    "masterful",
    "unputdownable",
    "refreshing",
    "thoughtful",
    "heartwarming",
    "thrilling",
    "immersive",
    "memorable",
    "gorgeous",
    "clever",
    "riveting",
    "outstanding",
    "cozy",
    "fun",
    "fast-paced",
    "page-turner",
}

NEGATIVE = {
    "boring",
    "dull",
    "slow",
    "disappointing",
    "disappointed",
    "bad",
    "terrible",
    "awful",
    "hate",
    "hated",
    "predictable",
    "flat",
    "tedious",
    "confusing",
    "weak",
    "poor",
    "waste",
    "worst",
    "annoying",
    "frustrating",
    "overrated",
    "bland",
    "forgettable",
    "clunky",
    "messy",
    "repetitive",
    "shallow",
    "unconvincing",
    "mediocre",
    "tiresome",
    "dragged",
    "slow-paced",
}

NEGATIONS = {
    "not",
    "no",
    "never",
    "hardly",
    "barely",
    "scarcely",
    "isn't",
    "wasn't",
    "aren't",
    "weren't",
    "don't",
    "didn't",
    "doesn't",
    "couldn't",
    "wouldn't",
    "can't",
    "cannot",
    "without",
}

INTENSIFIERS = {"very", "really", "absolutely", "totally", "so", "quite", "extremely", "truly"}

TOKEN_RE = re.compile(r"[a-z][a-z'-]*")

Sentiment = Literal["positive", "neutral", "negative"]


def analyze_sentiment(text: str, rating: int | None = None) -> tuple[Sentiment, list[str]]:
    """Score review text with a small lexicon; no external API is required."""
    words = TOKEN_RE.findall(text.lower())
    score = 0
    keywords: list[str] = []

    for index, word in enumerate(words):
        polarity = 1 if word in POSITIVE else -1 if word in NEGATIVE else 0
        if polarity == 0:
            continue
        if any(token in NEGATIONS for token in words[max(0, index - 3) : index]):
            polarity *= -1
        if index > 0 and words[index - 1] in INTENSIFIERS:
            score += polarity * 2
        else:
            score += polarity
        if word not in keywords:
            keywords.append(word)

    if rating is not None:
        if rating >= 4:
            score += 1
        elif rating <= 2:
            score -= 1

    if score > 0:
        sentiment: Sentiment = "positive"
    elif score < 0:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return sentiment, keywords[:6]
