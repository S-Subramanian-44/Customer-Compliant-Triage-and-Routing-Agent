from textblob import TextBlob
from .llm_utils import call_llm
from .config import LLM_MODEL
import logging

logger = logging.getLogger(__name__)


def analyze_sentiment(text: str):
    # Try LLM first (if available)
    try:
        prompt = "Detect sentiment of the following text as Positive, Neutral, or Negative. Return only the label.\nText:\n" + text
        resp = call_llm(prompt)
        if resp:
            label = resp.strip().splitlines()[0]
            if label.lower() in ["positive", "neutral", "negative"]:
                return label.capitalize()
    except Exception:
        logger.exception("LLM sentiment failed, falling back to TextBlob")

    # Fallback to TextBlob
    try:
        tb = TextBlob(text)
        polarity = tb.sentiment.polarity
        if polarity > 0.1:
            return "Positive"
        if polarity < -0.1:
            return "Negative"
        return "Neutral"
    except Exception:
        logger.exception("TextBlob sentiment failed")
        return "Neutral"
