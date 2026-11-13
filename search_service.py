
import re
import requests

from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urljoin
from xml.etree import ElementTree


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
    )
}

GOOGLE_NEWS_URL = "https://news.google.com/rss/search"

BBC_CRICKET_RSS = (
    "https://feeds.bbci.co.uk/sport/cricket/rss.xml"
)

GENERIC_TITLE_PHRASES = [
    "breaking headlines and video reports",
    "latest news and breaking news",
    "official website",
    "home page",
    "homepage"
]


# English, Hindi and Marathi news keywords.
NEWS_KEYWORDS = [
    # English
    "news", "breaking", "headlines", "latest updates",
    "today's news", "current affairs",

    # Hindi
    "आज", "आज की", "ताजा", "ताज़ा", "समाचार",
    "खबर", "खबरें", "न्यूज", "ब्रेकिंग",
    "अपडेट", "आज के समाचार",

    # Marathi
    "आजच्या", "आजचे", "आजचा", "ताज्या",
    "बातमी", "बातम्या", "वृत्त", "न्यूज",
    "ताजे", "नवीन बातम्या"
]


IGNORED_INDIAN_WORDS = {
    "आज", "आजच्या", "आजचे", "आजचा", "आजकी",
    "ताजा", "ताज़ा", "ताज्या", "ताजे",
    "बातमी", "बातम्या", "खबर", "खबरें",
    "समाचार", "न्यूज", "ब्रेकिंग", "अपडेट",
    "सांगा", "बताओ", "बताइए", "द्या",
    "मला", "के", "की", "का", "में", "और",
    "है", "हैं", "बताइये", "बातें"
}


# Hindi and Marathi words mapped to English search terms.
HINDI_TO_ENGLISH = {

    # Cricket
    "क्रिकेट": "cricket",
    "क्रिकेटच्या": "cricket",
    "क्रिकेटचे": "cricket",
    "क्रिकेटचा": "cricket",
    "क्रिकेटमध्ये": "cricket",
    "क्रिकेटची": "cricket",

    # Sports
    "खेल": "sports",
    "खेळ": "sports",
    "खेळाच्या": "sports",
    "क्रीडा": "sports",
    "सामना": "match",
    "सामन्याच्या": "match",
    "मैच": "match",
    "मैचों": "matches",

    # India
    "भारत": "India",
    "भारतीय": "India",
    "भारताच्या": "India",
    "भारतातील": "India",
    "भारताचे": "India",
    "भारताची": "India",

    # Cricket teams and players
    "टीम": "team",
    "संघ": "team",
    "खिलाड़ी": "player",
    "खिलाडी": "player",
    "खेळाडू": "player",
    "खेळाडूंच्या": "players",
    "विराट": "Virat",
    "कोहली": "Kohli",
    "रोहित": "Rohit",
    "शर्मा": "Sharma",
    "धोनी": "Dhoni",

    # Cricket formats
    "विश्व": "world",
    "जग": "world",
    "कप": "cup",
    "टेस्ट": "test",
    "वनडे": "ODI",
    "टी20": "T20",
    "आयपीएल": "IPL",
    "आईपीएल": "IPL",

    # Other subjects
    "फुटबॉल": "football",
    "हॉकी": "hockey",
    "निवडणूक": "election",
    "निवडणुकीच्या": "election",
    "चुनाव": "election",
    "सरकार": "government",
    "शिक्षण": "education",
    "तंत्रज्ञान": "technology",
    "विज्ञान": "science",
    "अर्थव्यवस्था": "economy"
}


def resolve_news_url(url):
    return url


def is_hindi_query(query):
    """Detect Hindi or Marathi Devanagari text."""
    return bool(
        re.search(r"[\u0900-\u097F]", query or "")
    )


def is_marathi_query(query):
    """Detect common Marathi words in a query."""

    marathi_words = [
        "आजच्या", "आजचे", "आजचा",
        "बातम्या", "बातमी", "सांगा",
        "ताज्या", "महाराष्ट्र", "मधील",
        "क्रीडा", "खेळाडू"
    ]

    query = query or ""

    return any(
        word in query
        for word in marathi_words
    )


def is_cricket_query(query):
    """Detect cricket queries in English, Hindi and Marathi."""

    if not isinstance(query, str):
        return False

    if re.search(
        r"cricket|क्रिकेट",
        query,
        re.IGNORECASE
    ):
        return True

    translated = translate_hindi_query(query)

    return bool(
        re.search(
            r"\bcricket\b",
            translated,
            re.IGNORECASE
        )
    )


def translate_hindi_query(query):
    """
    Convert supported Hindi/Marathi words into English.
    English words in mixed-language queries are preserved.
    """

    if not isinstance(query, str):
        return ""

    words = re.findall(
        r"[A-Za-z0-9]+|[\u0900-\u097F]+",
        query
    )

    translated = []

    dictionary_words = sorted(
        HINDI_TO_ENGLISH.keys(),
        key=len,
        reverse=True
    )

    for word in words:

        if re.fullmatch(r"[A-Za-z0-9]+", word):
            translated.append(word)
            continue

        if word in IGNORED_INDIAN_WORDS:
            continue

        replacement = HINDI_TO_ENGLISH.get(word)

        if replacement:
            translated.append(replacement)
            continue

        # Handle common Marathi/Hindi suffixes.
        matched = False

        for dictionary_word in dictionary_words:

            if word.startswith(dictionary_word):

                translated.append(
                    HINDI_TO_ENGLISH[dictionary_word]
                )

                matched = True
                break

        if not matched:
            continue

    return " ".join(translated).strip()


def clean_search_query(query):

    if not isinstance(query, str):
        return ""

    cleaned = query.lower().strip()

    cleaned = re.sub(
        r"\b(give me|show me|find me|tell me|please)\b",
        " ",
        cleaned
    )

    cleaned = re.sub(
        r"\b(the|latest|recent|current|today|breaking|news|"
        r"headlines|headline|updates|update|sources|source|"
        r"publication|publications|dates|date|with|and|for|"
        r"in|of|what|are|is)\b",
        " ",
        cleaned
    )

    cleaned = re.sub(r"\b\d+\b", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)

    return cleaned.strip()


def get_relevance_terms(query):

    cleaned = clean_search_query(query)

    if not cleaned:
        return set()

    return set(
        re.findall(r"[a-zA-Z]{2,}", cleaned)
    )


def is_relevant_news(query, result):

    title = result.get("title", "").lower()
    snippet = result.get("snippet", "").lower()

    content = f"{title} {snippet}"

    search_query = (
        translate_hindi_query(query)
        if is_hindi_query(query)
        else query
    )

    terms = get_relevance_terms(search_query)

    if not terms:
        return True

    if "india" in terms:
        if not re.search(r"\bindia\b|\bindian\b", content):
            return False

    specific_terms = terms - {"india", "indian"}

    if not specific_terms:
        return True

    return any(
        re.search(
            r"\b" + re.escape(term) + r"\b",
            content
        )
        for term in specific_terms
    )


def is_generic_result(title):

    title = title.lower().strip()

    return any(
        phrase in title
        for phrase in GENERIC_TITLE_PHRASES
    )


def is_news_query(query):
    """Detect news requests in English, Hindi and Marathi."""

    if not isinstance(query, str):
        return False

    query_lower = query.lower()

    if any(
        keyword in query_lower
        for keyword in NEWS_KEYWORDS
    ):
        return True

    patterns = [
        r"what.{0,20}happening",
        r"what.{0,20}happened",
        r"news.{0,20}today",
        r"latest.{0,20}news",
        r"आज.{0,30}(बातमी|बातम्या|खबर|समाचार)",
        r"(बातमी|बातम्या|खबर|समाचार).{0,20}आज",
        r"(ताज्या|नवीनतम).{0,30}(बातम्या|खबरें|समाचार)"
    ]

    return any(
        re.search(pattern, query_lower)
        for pattern in patterns
    )


def parse_rss_results(root, query, default_source):

    results = []
    seen_urls = set()
    seen_titles = set()

    for item in root.findall(".//item"):

        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        description = item.findtext("description", "").strip()
        published = item.findtext("pubDate", "").strip()

        source_element = item.find("source")

        source = (
            source_element.text.strip()
            if source_element is not None
            and source_element.text
            else default_source
        )

        if not title or not link:
            continue

        if not link.startswith(("http://", "https://")):
            continue

        normalized_title = re.sub(
            r"\s+",
            " ",
            title.lower().strip()
        )

        if normalized_title in seen_titles:
            continue

        if is_generic_result(title):
            continue

        snippet = BeautifulSoup(
            description,
            "html.parser"
        ).get_text(" ", strip=True)

        article_url = resolve_news_url(link)

        result = {
            "title": title,
            "snippet": snippet[:700],
            "url": article_url,
            "published": published,
            "source": source
        }

        # BBC's dedicated cricket feed is already topic-specific.
        # Google News results still need query relevance filtering.
        if (
            default_source != "BBC Sport"
            and not is_relevant_news(query, result)
        ):
            continue

        if article_url in seen_urls:
            continue

        results.append(result)

        seen_urls.add(article_url)
        seen_titles.add(normalized_title)

        if len(results) >= 10:
            break

    return results


def search_google_news(query):

    if not isinstance(query, str) or not query.strip():
        return []

    hindi = is_hindi_query(query)
    marathi = is_marathi_query(query)

    if hindi:
        cleaned_query = translate_hindi_query(query)
    else:
        cleaned_query = clean_search_query(query)

    if not cleaned_query:
        cleaned_query = query.strip()

    search_query = f"{cleaned_query} when:7d"

    if marathi:
        language = "mr"
    elif hindi:
        language = "hi"
    else:
        language = "en-IN"

    params = {
        "q": search_query,
        "hl": language,
        "gl": "IN",
        "ceid": f"IN:{language.split('-')[0]}"
    }

    try:

        response = requests.get(
            GOOGLE_NEWS_URL,
            params=params,
            headers=HEADERS,
            timeout=20
        )

        response.raise_for_status()

        root = ElementTree.fromstring(response.content)

        return parse_rss_results(
            root,
            query,
            "Google News"
        )

    except requests.RequestException as error:

        print("Google News connection error:", error)
        return []

    except ElementTree.ParseError as error:

        print("Google News RSS parsing error:", error)
        return []

    except Exception as error:

        print("Google News processing error:", error)
        return []


def search_bbc_cricket(query):

    if not is_cricket_query(query):
        return []

    try:

        response = requests.get(
            BBC_CRICKET_RSS,
            headers=HEADERS,
            timeout=20
        )

        response.raise_for_status()

        root = ElementTree.fromstring(response.content)

        return parse_rss_results(
            root,
            query,
            "BBC Sport"
        )

    except requests.RequestException as error:

        print("BBC Cricket connection error:", error)
        return []

    except ElementTree.ParseError as error:

        print("BBC Cricket RSS parsing error:", error)
        return []

    except Exception as error:

        print("BBC Cricket processing error:", error)
        return []


def search_duckduckgo(query):

    if not isinstance(query, str) or not query.strip():
        return []

    url = "https://html.duckduckgo.com/html/"

    try:

        response = requests.get(
            url,
            params={"q": query.strip()},
            headers=HEADERS,
            timeout=20
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        results = []
        seen_urls = set()

        for result in soup.select(".result"):

            link = result.select_one(".result__a")

            snippet_element = result.select_one(
                ".result__snippet"
            )

            if not link:
                continue

            title = link.get_text(" ", strip=True)
            href = link.get("href", "")

            if not title or not href:
                continue

            href = urljoin(url, href)

            parsed = urlparse(href)

            if "duckduckgo.com" in parsed.netloc:
                params = parse_qs(parsed.query)
                href = params.get("uddg", [""])[0]

            if not href:
                continue

            parsed_url = urlparse(href)

            if parsed_url.scheme not in ("http", "https"):
                continue

            if href in seen_urls:
                continue

            snippet = (
                snippet_element.get_text(" ", strip=True)
                if snippet_element else ""
            )

            seen_urls.add(href)

            results.append({
                "title": title,
                "snippet": snippet,
                "url": href,
                "published": "",
                "source": parsed_url.netloc
            })

            if len(results) >= 8:
                break

        return results

    except requests.RequestException as error:

        print("DuckDuckGo connection error:", error)
        return []

    except Exception as error:

        print("DuckDuckGo processing error:", error)
        return []


def merge_news_results(*result_groups, limit=20):
    """
    Combine multiple news sources.
    Remove duplicate URLs and duplicate headlines.
    Preserve original publisher, date and article URL.
    """

    combined = []
    seen_urls = set()
    seen_titles = set()

    for group in result_groups:

        for item in group:

            url = (item.get("url") or "").strip()

            title = (item.get("title") or "").strip()

            if not url or not title:
                continue

            normalized_url = url.rstrip("/").lower()

            normalized_title = re.sub(
                r"[^a-z0-9]+",
                " ",
                title.lower()
            ).strip()

            if normalized_url in seen_urls:
                continue

            if normalized_title in seen_titles:
                continue

            seen_urls.add(normalized_url)
            seen_titles.add(normalized_title)

            combined.append(item)

            if len(combined) >= limit:
                return combined

    return combined


def search_web(query):

    if not isinstance(query, str) or not query.strip():
        return []

    if is_news_query(query):

        # First source: Google News.
        google_results = search_google_news(query)

        # Second source: BBC Sport Cricket.
        # Combine BBC even when Google News already returned results.
        if is_cricket_query(query):

            bbc_results = search_bbc_cricket(query)

            combined_results = merge_news_results(
                google_results,
                bbc_results,
                limit=20
            )

            print(
                "News sources combined:",
                "Google News =", len(google_results),
                "| BBC Sport =", len(bbc_results),
                "| Combined =", len(combined_results)
            )

            return combined_results

        return merge_news_results(
            google_results,
            limit=20
        )

    # Ordinary web searches use DuckDuckGo.
    return search_duckduckgo(query)
