"""Local, predictable conversation titles without another model call."""


def title_from_message(message: str) -> str:
    return " ".join(message.split())[:60] or "New chat"
