import secrets
import hashlib


def generate_token(length=32):
    return secrets.token_urlsafe(length)


def hash_text(value):
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def verify_hash(value, hashed_value):
    return secrets.compare_digest(
        hash_text(value),
        hashed_value
    )


def validate_message(message):
    if not isinstance(message, str):
        return False

    if not message.strip():
        return False

    if len(message) > 4000:
        return False

    return True