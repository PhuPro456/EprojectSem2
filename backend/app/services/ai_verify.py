from app.core.ai_providers import get_provider

MIN_KEY_LENGTH = 20


def verify_key_format(provider: str, api_key: str) -> tuple[bool, str]:
    """Validate the shape of a provider key without calling an external API.

    The demo has no outbound network guarantee, so this is a local sanity check:
    it catches pasted placeholders and obviously wrong providers before a key is
    stored. Live verification can be layered on later with the decrypted value.
    """
    info = get_provider(provider)
    if info is None:
        return False, "Unknown AI provider."

    key = api_key.strip()
    if len(key) < MIN_KEY_LENGTH:
        return False, f"{info.name} keys are longer than {MIN_KEY_LENGTH} characters."
    if not key.startswith(info.key_prefix):
        return False, f"{info.name} keys usually start with {info.key_prefix!r}."
    lowered = key.casefold()
    if any(token in lowered for token in ("example", "your-key", "replace", "xxxx")):
        return False, "That looks like a placeholder, not a real key."

    return True, f"{info.name} key format looks valid."
