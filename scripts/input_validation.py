from __future__ import annotations

from collections.abc import Mapping, Sequence

_ALLOWED_CONTROL_CHARS = {"\n", "\r", "\t"}


class InputValidationError(ValueError):
    pass


def _contains_disallowed_control_chars(value: str) -> bool:
    for char in value:
        if ord(char) < 32 and char not in _ALLOWED_CONTROL_CHARS:
            return True
    return False


def validate_strings(value, path: str = "<root>") -> None:
    if isinstance(value, str):
        if _contains_disallowed_control_chars(value):
            raise InputValidationError(f"invalid control character in {path}")
        return

    if isinstance(value, Mapping):
        for key, item in value.items():
            validate_strings(item, f"{path}.{key}")
        return

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            validate_strings(item, f"{path}[{index}]")
