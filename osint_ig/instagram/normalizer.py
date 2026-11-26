"""Payload normalization helpers for Instagram GraphQL and REST responses."""
import re

_TYPED_KEY_PREFIX = re.compile(r"^1[a-z](?=[a-z_])")


def normalize_payload(value):
    """Normalize typed GraphQL field prefixes and derive ``pk`` when only ``id`` exists."""
    if isinstance(value, list):
        return [normalize_payload(v) for v in value]
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            plain = _TYPED_KEY_PREFIX.sub("", key)
            item = normalize_payload(item)
            if plain in out and out[plain] is not None and item is None:
                continue
            out[plain] = item
        if "pk" not in out and "id" in out and "username" in out:
            out["pk"] = out["id"]
        return out
    return value
