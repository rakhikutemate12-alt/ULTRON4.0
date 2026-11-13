import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

from backend.core.ai_engine import generate_response, generate_response_stream
from backend.services.search_service import search_web


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

INDIA_TIMEZONE = timezone(timedelta(hours=5, minutes=30))

STOP_WORDS = {
    "the", "is", "are", "was", "were", "what", "when", "where",
    "who", "why", "how", "tell", "me", "about", "latest", "today",
    "news", "please", "give", "show", "current", "recent",
    "à¤•à¥‡", "à¤•à¥€", "à¤•à¤¾", "à¤®à¥‡à¤‚", "à¤¹à¥ˆ", "à¤”à¤°", "à¤¬à¤¤à¤¾à¤“", "à¤¬à¤¤à¤¾à¤‡à¤",
    "à¤†à¤œ", "à¤•à¥€", "à¤•à¥‡", "à¤²à¤¿à¤",
    "à¤†à¤£à¤¿", "à¤®à¤§à¥à¤¯à¥‡", "à¤†à¤¹à¥‡", "à¤¸à¤¾à¤‚à¤—à¤¾", "à¤¬à¤¾à¤¤à¤®à¥à¤¯à¤¾", "à¤†à¤œà¤šà¥à¤¯à¤¾"
}

GENERIC_TERMS = {
    "news", "latest", "today", "current", "recent", "updates",
    "à¤¬à¤¾à¤¤à¤®à¥à¤¯à¤¾", "à¤†à¤œà¤šà¥à¤¯à¤¾", "à¤¤à¤¾à¤œà¥à¤¯à¤¾", "à¤–à¤¬à¤°à¥‡à¤‚", "à¤†à¤œ"
}

HINDI_TO_ENGLISH = {
    "à¤•à¥à¤°à¤¿à¤•à¥‡à¤Ÿ": "cricket",
    "à¤–à¥‡à¤²": "sports",
    "à¤¶à¤¿à¤•à¥à¤·à¤¾": "education",
    "à¤¤à¤•à¤¨à¥€à¤•": "technology",
    "à¤µà¤¿à¤œà¥à¤žà¤¾à¤¨": "science",
    "à¤µà¥à¤¯à¤¾à¤ªà¤¾à¤°": "business",
    "à¤®à¥Œà¤¸à¤®": "weather",
    "à¤­à¤¾à¤°à¤¤": "India",
    "à¤®à¤¹à¤¾à¤°à¤¾à¤·à¥à¤Ÿà¥à¤°": "Maharashtra",
    "à¤µà¤¿à¤¶à¥à¤µ": "world",
    "à¤¦à¥à¤¨à¤¿à¤¯à¤¾": "world",
    "à¤¸à¤®à¤¾à¤šà¤¾à¤°": "news",
    "à¤–à¤¬à¤°": "news",
    "à¤†à¤œ": "today"
}

MARATHI_TO_ENGLISH = {
    "à¤•à¥à¤°à¤¿à¤•à¥‡à¤Ÿ": "cricket",
    "à¤•à¥à¤°à¥€à¤¡à¤¾": "sports",
    "à¤¶à¤¿à¤•à¥à¤·à¤£": "education",
    "à¤¤à¤‚à¤¤à¥à¤°à¤œà¥à¤žà¤¾à¤¨": "technology",
    "à¤µà¤¿à¤œà¥à¤žà¤¾à¤¨": "science",
    "à¤µà¥à¤¯à¤µà¤¸à¤¾à¤¯": "business",
    "à¤¹à¤µà¤¾à¤®à¤¾à¤¨": "weather",
    "à¤­à¤¾à¤°à¤¤": "India",
    "à¤®à¤¹à¤¾à¤°à¤¾à¤·à¥à¤Ÿà¥à¤°": "Maharashtra",
    "à¤œà¤—": "world",
    "à¤¬à¤¾à¤¤à¤®à¥à¤¯à¤¾": "news",
    "à¤†à¤œà¤šà¥à¤¯à¤¾": "today"
}

TOPIC_KEYWORDS = {
    "cricket": {
        "cricket", "test match", "odi", "t20", "wicket",
        "batter", "bowler", "innings", "world cup", "ipl",
        "wbb l", "bcci", "icc"
    },
    "sports": {
        "sports", "football", "soccer", "hockey", "tennis",
        "badminton", "basketball", "olympics", "athlete",
        "tournament", "championship"
    },
    "education": {
        "education", "university", "college", "admission",
        "exam", "examination", "result", "student", "ugc",
        "aicte", "nta", "scholarship", "academic"
    },
    "technology": {
        "technology", "artificial intelligence", "ai",
        "computer", "software", "internet", "cyber",
        "robotics", "digital", "smartphone"
    },
    "science": {
        "science", "research", "scientific", "space",
        "nasa", "isro", "discovery", "experiment",
        "astronomy", "biology"
    },
    "business": {
        "business", "economy", "economic", "market",
        "finance", "banking", "company", "industry",
        "investment", "stock", "trade"
    },
    "weather": {
        "weather", "rain", "temperature", "forecast",
        "monsoon", "cyclone", "storm", "humidity",
        "à¤¹à¤µà¤¾à¤®à¤¾à¤¨", "à¤ªà¤¾à¤Šà¤¸", "à¤®à¥Œà¤¸à¤®", "à¤¬à¤¾à¤°à¤¿à¤¶"
    }
}

REFERENCE_DOMAINS = {
    "britannica.com",
    "wikipedia.org",
    "encyclopedia.com"
}

GENERIC_TITLES = {
    "home", "latest news", "news", "top stories",
    "search results", "breaking news"
}

EXCLUDED_TITLE_TERMS = {
    "podcast", "scorecard", "live commentary",
    "live blog", "match centre"
}


# ---------------------------------------------------------
# LANGUAGE AND TEXT HELPERS
# ---------------------------------------------------------

def translate_words(text):
    if not isinstance(text, str):
        return ""

    words = text.split()
    translated = []

    for word in words:
        clean = word.strip(".,!?;:()[]{}\"'").lower()
        replacement = HINDI_TO_ENGLISH.get(
            clean,
            MARATHI_TO_ENGLISH.get(clean, word)
        )
        translated.append(replacement)

    return " ".join(translated)


def normalize_text(text):
    if not isinstance(text, str):
        return ""

    text = text.lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def get_query_terms(query):
    translated = translate_words(query)
    normalized = normalize_text(translated)

    return {
        word for word in normalized.split()
        if word not in STOP_WORDS
        and word not in GENERIC_TERMS
        and len(word) > 1
    }


def should_search(message):
    if not isinstance(message, str):
        return False

    text = normalize_text(message)

    search_indicators = [
        "latest", "today", "current", "recent", "breaking",
        "news", "search", "weather", "score", "live",
        "à¤†à¤œ", "à¤¤à¤¾à¤œà¤¾", "à¤–à¤¬à¤°", "à¤¸à¤®à¤¾à¤šà¤¾à¤°", "à¤¬à¤¾à¤¤à¤®à¥à¤¯à¤¾",
        "à¤†à¤œà¤šà¥à¤¯à¤¾", "à¤¶à¥‹à¤§à¤¾", "à¤¸à¤§à¥à¤¯à¤¾à¤šà¥à¤¯à¤¾"
    ]

    return any(term in text for term in search_indicators)


def detect_response_language(text):
    if not isinstance(text, str):
        return "English"

    # Detect Hindi and Marathi written in English letters.
    normalized = re.sub(r"[^a-z\s]", " ", text.lower())
    words = set(normalized.split())

    hindi_roman = {
        "hai", "hain", "ho", "kaise", "kaisa", "kesa",
        "kaisi", "kese", "kya", "aap", "ap", "mera",
        "meri", "mujhe", "tum", "tumhara", "batao",
        "bataye", "kyun", "kahan", "namaste", "hain",
        "rahe", "raha", "rahi", "nahi", "chahiye"
    }

    marathi_roman = {
        "aahe", "ahe", "ahet", "kay", "kasa", "kashi",
        "kase", "sanga", "mala", "tumhi", "majha",
        "majhi", "maza", "majhe", "aajchya", "batmya",
        "pahije", "aahet", "karayche", "mhanje"
    }

    hindi_score = sum(1 for word in hindi_roman if word in words)
    marathi_score = sum(1 for word in marathi_roman if word in words)

    if hindi_score > marathi_score:
        return "Hindi"
    if marathi_score > hindi_score:
        return "Marathi"

    # Detect Hindi and Marathi written in Devanagari.
    if not re.search(r"[\u0900-\u097F]", text):
        return "English"

    marathi_terms = [
        "\u0906\u0939\u0947", "\u0906\u0939\u0947\u0924",
        "\u0906\u0923\u093f", "\u092e\u094d\u0939\u0923\u091c\u0947",
        "\u0938\u093e\u0902\u0917\u093e", "\u0906\u091c\u091a\u094d\u092f\u093e",
        "\u092c\u093e\u0924\u092e\u094d\u092f\u093e", "\u092e\u0939\u093e\u0930\u093e\u0937\u094d\u091f\u094d\u0930",
        "\u092e\u093e\u0939\u093f\u0924\u0940", "\u092a\u093e\u0939\u093f\u091c\u0947",
        "\u0924\u0941\u092e\u094d\u0939\u0940", "\u092e\u0932\u093e",
        "\u0915\u0930\u093e", "\u092f\u093e\u092c\u0926\u094d\u0926\u0932"
    ]

    hindi_terms = [
        "\u0915\u094d\u092f\u093e", "\u0939\u0948", "\u0939\u0948\u0902",
        "\u0914\u0930", "\u092c\u0924\u093e\u0907\u090f",
        "\u092c\u0924\u093e\u0913", "\u0938\u092e\u093e\u091a\u093e\u0930",
        "\u092e\u0941\u091d\u0947", "\u0906\u092a", "\u0915\u0948\u0938\u0947",
        "\u0915\u094d\u092f\u094b\u0902", "\u091c\u093e\u0928\u0915\u093e\u0930\u0940",
        "\u091a\u093e\u0939\u093f\u090f", "\u0928\u0939\u0940\u0902"
    ]

    marathi_score = sum(1 for term in marathi_terms if term in text)
    hindi_score = sum(1 for term in hindi_terms if term in text)

    return "Marathi" if marathi_score > hindi_score else "Hindi"




# ---------------------------------------------------------
# FIXED ULTRON INTRODUCTION
# ---------------------------------------------------------

def get_fixed_introduction(message):
    if not isinstance(message, str):
        return None

    text = message.lower().strip()
    normalized = re.sub(r"[^a-z\s]", " ", text)
    words = set(normalized.split())

    intro_phrases = {
        "who are you", "introduce yourself", "tell me about yourself",
        "what are you", "your introduction", "about yourself",
        "apna parichay", "apna intro", "tum kaun ho",
        "aap kaun hain", "kesa hai ultron", "kaise ho ultron"
    }

    roman_intro = any(phrase in text for phrase in intro_phrases)

    devanagari_intro = any(term in text for term in [
        "\u092a\u0930\u093f\u091a\u092f",
        "\u0915\u094c\u0928 \u0939\u094b",
        "\u0905\u092a\u0928\u0947 \u092c\u093e\u0930\u0947",
        "\u0928\u092e\u0938\u094d\u0924\u0947"
    ])

    if not (roman_intro or devanagari_intro):
        return None

    if "\u0924\u0941\u092e\u091a\u093e" in message or "\u0926\u094d\u092f\u093e" in message:
        language = "Marathi"
    else:
        language = detect_response_language(message)

    responses = {
        "English": (
            "Hello! I am ULTRON AI 4.0, your AI assistant. "
            "I can help you learn, understand topics, write, solve problems, "
            "and explore information. You can communicate with me in English, "
            "Hindi, or Marathi. How can I help you today?"
        ),
        "Hindi": (
            "\u0928\u092e\u0938\u094d\u0924\u0947! \u092e\u0948\u0902 ULTRON AI 4.0 \u0939\u0942\u0901\u0964 "
            "\u092e\u0948\u0902 \u0906\u092a\u0915\u093e AI \u0938\u0939\u093e\u092f\u0915 \u0939\u0942\u0901\u0964 "
            "\u092e\u0948\u0902 \u0906\u092a\u0915\u0940 \u092a\u0922\u093c\u093e\u0908, \u0932\u0947\u0916\u0928, "
            "\u0938\u0935\u093e\u0932\u094b\u0902 \u0915\u0947 \u091c\u0935\u093e\u092c \u0914\u0930 "
            "\u0935\u093f\u0937\u092f\u094b\u0902 \u0915\u094b \u0938\u092e\u091d\u0928\u0947 \u092e\u0947\u0902 "
            "\u092e\u0926\u0926 \u0915\u0930 \u0938\u0915\u0924\u093e \u0939\u0942\u0901\u0964 "
            "\u0906\u092a \u092e\u0941\u091d\u0938\u0947 \u0939\u093f\u0902\u0926\u0940, \u0905\u0902\u0917\u094d\u0930\u0947\u091c\u093c\u0940 "
            "\u092f\u093e \u092e\u0930\u093e\u0920\u0940 \u092e\u0947\u0902 \u092c\u093e\u0924 \u0915\u0930 \u0938\u0915\u0924\u0947 \u0939\u0948\u0902\u0964 "
            "\u092c\u0924\u093e\u0907\u090f, \u092e\u0948\u0902 \u0906\u092a\u0915\u0940 \u0915\u094d\u092f\u093e \u092e\u0926\u0926 \u0915\u0930\u0942\u0901?"
        ),
        "Marathi": (
            "\u0928\u092e\u0938\u094d\u0915\u093e\u0930! \u092e\u0940 ULTRON AI 4.0 \u0906\u0939\u0947\u0964 "
            "\u092e\u0940 \u0924\u0941\u092e\u091a\u093e AI \u0938\u0939\u093e\u092f\u094d\u092f\u0915 \u0906\u0939\u0947\u0964 "
            "\u092e\u0940 \u0924\u0941\u092e\u094d\u0939\u093e\u0932\u093e \u0905\u092d\u094d\u092f\u093e\u0938, "
            "\u0932\u0947\u0916\u0928, \u092a\u094d\u0930\u0936\u094d\u0928\u093e\u0902\u091a\u0940 \u0909\u0924\u094d\u0924\u0930\u0947 "
            "\u0906\u0923\u093f \u0935\u093f\u0935\u093f\u0927 \u0935\u093f\u0937\u092f \u0938\u092e\u091c\u0942\u0928 "
            "\u0918\u0947\u0923\u094d\u092f\u093e\u0938 \u092e\u0926\u0924 \u0915\u0930\u0942 \u0936\u0915\u0924\u094b\u0964 "
            "\u0924\u0941\u092e\u094d\u0939\u0940 \u092e\u093e\u091d\u094d\u092f\u093e\u0936\u0940 \u092e\u0930\u093e\u0920\u0940, "
            "\u0939\u093f\u0902\u0926\u0940 \u0915\u093f\u0902\u0935\u093e \u0907\u0902\u0917\u094d\u0930\u091c\u0940\u0924 "
            "\u092c\u094b\u0932\u0942 \u0936\u0915\u0924\u093e\u0964 \u0938\u093e\u0902\u0917\u093e, \u092e\u0940 "
            "\u0924\u0941\u092e\u091a\u0940 \u0915\u0936\u0940 \u092e\u0926\u0924 \u0915\u0930\u0942?"
        )
    }

    return responses.get(language, responses["English"])

# ---------------------------------------------------------
# DATE HELPERS
# ---------------------------------------------------------

def parse_published_date(value):
    if not value:
        return None

    try:
        parsed = parsedate_to_datetime(str(value))

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(INDIA_TIMEZONE)

    except (TypeError, ValueError, OverflowError):
        return None


def is_recent(item, days=7):
    published = parse_published_date(item.get("published"))

    if published is None:
        return False

    now = datetime.now(INDIA_TIMEZONE)
    return now - timedelta(days=days) <= published <= now + timedelta(hours=1)


def is_today(item):
    published = parse_published_date(item.get("published"))

    if published is None:
        return False

    today = datetime.now(INDIA_TIMEZONE).date()
    return published.date() == today


def wants_today_news(query):
    text = normalize_text(query)

    today_terms = [
        "today", "this morning", "à¤†à¤œ", "à¤†à¤œà¤šà¥à¤¯à¤¾",
        "à¤†à¤œ à¤•à¥€", "à¤†à¤œ à¤•à¥‡", "à¤†à¤œ à¤•à¤¾"
    ]

    return any(term in text for term in today_terms)


def is_historical(query):
    text = normalize_text(query)

    historical_terms = [
        "history", "historical", "in 2020", "in 2021",
        "in 2022", "in 2023", "in 2024",
        "à¤‡à¤¤à¤¿à¤¹à¤¾à¤¸", "à¤‡à¤¤à¤¿à¤¹à¤¾à¤¸à¤¾à¤¤"
    ]

    return any(term in text for term in historical_terms)


# ---------------------------------------------------------
# RESULT FILTERING
# ---------------------------------------------------------

def get_article_headline(item):
    title = str(item.get("title", "")).strip()
    snippet = str(item.get("snippet", "")).strip()

    if title:
        return title

    return snippet


def is_generic_title(title):
    normalized = normalize_text(title)

    if not normalized:
        return True

    if normalized in GENERIC_TITLES:
        return True

    return False


def is_reference_content(item):
    source = normalize_text(item.get("source", ""))
    url = str(item.get("url", "")).lower()

    try:
        domain = urlparse(url).netloc.lower()
    except Exception:
        domain = ""

    if any(domain.endswith(x) for x in REFERENCE_DOMAINS):
        return True

    if "britannica" in source or "wikipedia" in source:
        return True

    return False


def is_cricket_news_headline(title):
    text = normalize_text(title)

    cricket_terms = [
        "cricket", "test match", "odi", "t20", "wicket",
        "batter", "bowler", "innings", "world cup",
        "ashes", "bcci", "icc", "wbb l"
    ]

    return any(term in text for term in cricket_terms)


def get_topic(query):
    text = normalize_text(translate_words(query))

    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(normalize_text(word) in text for word in keywords):
            return topic

    return None


def calculate_relevance(query, item):
    title = normalize_text(get_article_headline(item))
    snippet = normalize_text(item.get("snippet", ""))
    source = normalize_text(item.get("source", ""))

    combined = f"{title} {snippet} {source}"
    query_terms = get_query_terms(query)

    matched = {
        term for term in query_terms
        if term in combined
    }

    score = len(matched) * 3

    topic = get_topic(query)

    if topic:
        topic_matches = TOPIC_KEYWORDS.get(topic, set())

        if any(normalize_text(word) in combined for word in topic_matches):
            score += 3

    if is_recent(item):
        score += 1

    if is_today(item):
        score += 2

    return score, matched


def _filter_results_by_period(results, days=7):
    return [
        item for item in results
        if isinstance(item, dict) and is_recent(item, days)
    ]



def filter_relevant_results(query, results):
    if not isinstance(results, list):
        return []

    topic = get_topic(query)
    query_terms = get_query_terms(query)
    normalized_query = normalize_text(query)

    news_request = any(
        term in normalized_query
        for term in ("news", "latest", "breaking", "today")
    )

    news_exclusions = {
        "science": (
            "science quiz",
            "science objectives",
            "seven ways nuclear science",
            "doe explains",
        ),
        "business": (
            "business trip",
            "business of travel",
            "business education",
            "revenue and usage statistics",
            "business of keeping things fresh",
        ),
        "technology": (
            "deepfake meaning",
            "technology industry in",
            "doe explains",
        ),
    }

    filtered = []
    seen = set()

    for item in results:
        if not isinstance(item, dict):
            continue

        title = get_article_headline(item)

        if is_generic_title(title) or is_reference_content(item):
            continue

        normalized_title = normalize_text(title)
        snippet = normalize_text(item.get("snippet", ""))
        combined = f"{normalized_title} {snippet}"

        if any(
            term in normalized_title
            for term in EXCLUDED_TITLE_TERMS
        ):
            continue

        if news_request and topic in news_exclusions:
            if any(
                phrase in normalized_title
                for phrase in news_exclusions[topic]
            ):
                continue

        if topic == "cricket":
            if not is_cricket_news_headline(title):
                continue

        elif topic:
            topic_words = TOPIC_KEYWORDS.get(topic, set())
            topic_matches = [
                normalize_text(word)
                for word in topic_words
                if len(normalize_text(word)) > 2
            ]

            if not any(word in combined for word in topic_matches):
                continue

        score, matched = calculate_relevance(query, item)

        if query_terms and not matched and not topic:
            continue

        if topic and score < 1:
            continue

        url = str(item.get("url", "")).strip()
        dedupe_key = url.lower() if url else normalized_title

        if not dedupe_key or dedupe_key in seen:
            continue

        seen.add(dedupe_key)

        result = dict(item)
        result["relevance_score"] = score
        result["fallback_recent"] = False
        filtered.append(result)

    filtered.sort(
        key=lambda item: (
            is_today(item),
            item.get("relevance_score", 0)
        ),
        reverse=True
    )

    if wants_today_news(query):
        today_results = [
            item for item in filtered if is_today(item)
        ]

        recent_results = _filter_results_by_period(filtered, 7)

        today_keys = {
            str(item.get("url", "")).strip().lower()
            or normalize_text(get_article_headline(item))
            for item in today_results
        }

        supplemental_results = []

        for item in recent_results:
            key = (
                str(item.get("url", "")).strip().lower()
                or normalize_text(get_article_headline(item))
            )

            if key in today_keys:
                continue

            result = dict(item)
            result["fallback_recent"] = True
            supplemental_results.append(result)

        combined_results = today_results[:8]
        remaining_slots = max(0, 8 - len(combined_results))
        combined_results.extend(supplemental_results[:remaining_slots])

        return combined_results

    return filtered[:8]


# ---------------------------------------------------------
# NEWS RESPONSE FORMATTING
# ---------------------------------------------------------

def format_news_response(query, results):
    if not results:
        return (
            "I could not find sufficiently relevant news results. "
            "Please try a more specific search query."
        )

    language = detect_response_language(query)

    fallback = any(
        item.get("fallback_recent", False)
        for item in results
    )

    if language == "Hindi":
        heading = "à¤†à¤œ à¤•à¥€ à¤¤à¤¾à¤œà¤¼à¤¾ à¤œà¤¾à¤¨à¤•à¤¾à¤°à¥€" if not fallback else "à¤ªà¤¿à¤›à¤²à¥‡ 7 à¤¦à¤¿à¤¨à¥‹à¤‚ à¤•à¥€ à¤‰à¤ªà¤²à¤¬à¥à¤§ à¤œà¤¾à¤¨à¤•à¤¾à¤°à¥€"
        source_label = "à¤¸à¥à¤°à¥‹à¤¤"
        date_label = "à¤ªà¥à¤°à¤•à¤¾à¤¶à¤¿à¤¤"
        note = "à¤†à¤œ à¤•à¥€ à¤–à¤¬à¤° à¤‰à¤ªà¤²à¤¬à¥à¤§ à¤¨à¤¹à¥€à¤‚ à¤¥à¥€, à¤‡à¤¸à¤²à¤¿à¤ à¤ªà¤¿à¤›à¤²à¥‡ 7 à¤¦à¤¿à¤¨à¥‹à¤‚ à¤•à¥‡ à¤ªà¤°à¤¿à¤£à¤¾à¤® à¤¦à¤¿à¤–à¤¾à¤ à¤—à¤ à¤¹à¥ˆà¤‚à¥¤" if fallback else ""

    elif language == "Marathi":
        heading = "à¤†à¤œà¤šà¥à¤¯à¤¾ à¤¤à¤¾à¤œà¥à¤¯à¤¾ à¤¬à¤¾à¤¤à¤®à¥à¤¯à¤¾" if not fallback else "à¤®à¤¾à¤—à¥€à¤² 7 à¤¦à¤¿à¤µà¤¸à¤¾à¤‚à¤¤à¥€à¤² à¤‰à¤ªà¤²à¤¬à¥à¤§ à¤¬à¤¾à¤¤à¤®à¥à¤¯à¤¾"
        source_label = "à¤¸à¥à¤°à¥‹à¤¤"
        date_label = "à¤ªà¥à¤°à¤•à¤¾à¤¶à¤¿à¤¤"
        note = "à¤†à¤œà¤šà¥€ à¤¬à¤¾à¤¤à¤®à¥€ à¤‰à¤ªà¤²à¤¬à¥à¤§ à¤¨à¤¸à¤²à¥à¤¯à¤¾à¤®à¥à¤³à¥‡ à¤®à¤¾à¤—à¥€à¤² 7 à¤¦à¤¿à¤µà¤¸à¤¾à¤‚à¤¤à¥€à¤² à¤¬à¤¾à¤¤à¤®à¥à¤¯à¤¾ à¤¦à¤¾à¤–à¤µà¤²à¥à¤¯à¤¾ à¤†à¤¹à¥‡à¤¤." if fallback else ""

    else:
        heading = "Latest News" if not fallback else "Available News from the Last 7 Days"
        source_label = "Source"
        date_label = "Published"
        note = "No matching news from today was found, so results from the last 7 days are shown." if fallback else ""

    lines = [f"## {heading}", ""]

    if note:
        lines.extend([note, ""])

    for index, item in enumerate(results, 1):
        title = get_article_headline(item)
        source = item.get("source", "Unknown source")
        published = item.get("published", "Date unavailable")
        url = item.get("url", "")

        lines.append(f"**{index}. {title}**")
        lines.append(f"- {source_label}: {source}")
        lines.append(f"- {date_label}: {published}")

        if url:
            lines.append(f"- Link: {url}")

        lines.append("")

    lines.append(
        "Note: Results are based on the available search sources."
    )

    return "\n".join(lines)


# ---------------------------------------------------------
# MESSAGE PREPARATION
# ---------------------------------------------------------

def prepare_messages(messages, web_context=None):
    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]

    if not isinstance(messages, list):
        return []

    prepared = []

    for message in messages[-20:]:
        if not isinstance(message, dict):
            continue

        role = message.get("role")
        content = message.get("content")

        if role not in ("user", "assistant", "system"):
            continue

        if not isinstance(content, str):
            continue

        prepared.append({
            "role": role,
            "content": content[:12000]
        })

    # Explicitly instruct the model to answer in the latest user's language.
    latest_user = next(
        (item["content"] for item in reversed(prepared)
         if item["role"] == "user"),
        ""
    )

    if latest_user:
        language = detect_response_language(latest_user)

        language_instruction = {
            "Hindi": (
                "LANGUAGE REQUIREMENT: Reply ONLY in natural, grammatically "
                "correct Hindi using Devanagari script. Do not use Marathi "
                "words or Marathi grammar. Introduce yourself naturally "
                "in Hindi as ULTRON AI 4.0."
            ),
            "Marathi": (
                "LANGUAGE REQUIREMENT: Reply ONLY in natural, grammatically "
                "correct Marathi using Devanagari script. Do not use Hindi "
                "words or Hindi grammar."
            ),
            "English": (
                "LANGUAGE REQUIREMENT: Reply ONLY in clear, natural English."
            )
        }.get(language, "Reply in clear English.")

        prepared.insert(0, {
            "role": "system",
            "content": language_instruction
        })

    if web_context and prepared:
        for index in range(len(prepared) - 1, -1, -1):
            if prepared[index]["role"] == "user":
                prepared[index]["content"] += (
                    "\n\nUse the following current web information "
                    "when answering. Do not invent facts.\n\n"
                    + str(web_context)[:12000]
                )
                break

    return prepared


# ---------------------------------------------------------
# DIRECT SEARCH RESPONSE
# ---------------------------------------------------------

def get_direct_search_response(query):
    try:
        raw_results = search_web(query)
        results = filter_relevant_results(query, raw_results)
        return format_news_response(query, results)

    except Exception as error:
        return (
            "Search is temporarily unavailable. "
            f"Please try again later. ({type(error).__name__})"
        )


# ---------------------------------------------------------
# MAIN CHAT PROCESSING
# ---------------------------------------------------------

def process_chat(messages, web_context=None):
    prepared = prepare_messages(messages, web_context)

    if not prepared:
        return "Please enter a valid message."

    latest_message = prepared[-1]["content"]

    fixed_intro = get_fixed_introduction(latest_message)
    if fixed_intro:
        return fixed_intro

    if should_search(latest_message) and not web_context:
        search_response = get_direct_search_response(latest_message)

        if search_response:
            return search_response

    try:
        return generate_response(prepared)

    except Exception as error:
        return (
            "I am unable to generate a response right now. "
            f"Please try again. ({type(error).__name__})"
        )


def process_chat_stream(messages, web_context=None):
    prepared = prepare_messages(messages, web_context)

    if not prepared:
        yield "Please enter a valid message."
        return

    latest_message = prepared[-1]["content"]

    fixed_intro = get_fixed_introduction(latest_message)
    if fixed_intro:
        yield fixed_intro
        return

    if should_search(latest_message) and not web_context:
        yield get_direct_search_response(latest_message)
        return

    try:
        for chunk in generate_response_stream(prepared):
            if chunk:
                yield chunk

    except Exception as error:
        yield (
            "I am unable to generate a response right now. "
            f"Please try again. ({type(error).__name__})"
        )


