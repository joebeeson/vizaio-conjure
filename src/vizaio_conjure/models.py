"""Immutable launch models and known SmartCast constants."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from urllib.parse import urlsplit

DEFAULT_CONJURE_APP_ID = "17"


class VizioNamespace(IntEnum):
    """Known SmartCast application namespaces.

    ``CONJURE`` is the namespace used by the established Conjure launcher.
    Other namespaces can still be supplied as raw integers while their names
    remain undocumented.
    """

    CONJURE = 4

    @classmethod
    def coerce(cls, value: VizioNamespace | int | str) -> int:
        """Resolve an enum member, friendly name, or numeric namespace."""

        if isinstance(value, cls):
            return int(value)
        if isinstance(value, int):
            if value < 0:
                raise ValueError("name_space must be non-negative")
            return value
        text = value.strip()
        if not text:
            raise ValueError("name_space must not be empty")
        try:
            return int(cls[text.upper()])
        except KeyError:
            try:
                numeric = int(text, 10)
            except ValueError as exc:
                known = ", ".join(member.name for member in cls)
                raise ValueError(
                    f"unknown namespace {value!r}; use a known name ({known}) or an integer"
                ) from exc
            if numeric < 0:
                raise ValueError("name_space must be non-negative")
            return numeric


DEFAULT_CONJURE_NAMESPACE = VizioNamespace.CONJURE


def _validate_url(url: str) -> str:
    if not isinstance(url, str) or not url.strip():
        raise ValueError("url must be a non-empty string")
    normalized = url.strip()
    parsed = urlsplit(normalized)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        raise ValueError("url must be an absolute http or https URL")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("url must not contain embedded credentials")
    return normalized


@dataclass(frozen=True, slots=True)
class ConjureTarget:
    """A URL and SmartCast app configuration for a Conjure launch."""

    url: str
    app_id: str = DEFAULT_CONJURE_APP_ID
    name_space: VizioNamespace | int | str = DEFAULT_CONJURE_NAMESPACE

    def __post_init__(self) -> None:
        object.__setattr__(self, "url", _validate_url(self.url))
        if not str(self.app_id).strip():
            raise ValueError("app_id must be a non-empty string")
        object.__setattr__(self, "app_id", str(self.app_id).strip())
        object.__setattr__(self, "name_space", VizioNamespace.coerce(self.name_space))

    @property
    def namespace(self) -> int:
        """The normalized numeric namespace sent to the TV."""

        return int(self.name_space)
