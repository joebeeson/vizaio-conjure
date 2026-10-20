"""Local device profiles and OS-backed VIZIO credentials."""

from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

import keyring
from platformdirs import user_config_path

SERVICE_NAME = "vizaio-conjure"
CONFIG_VERSION = 1
_DEFAULT_CONFIG_PATH = user_config_path("vizaio-conjure") / "profiles.json"
_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


class CredentialBackend(Protocol):
    """Small keyring surface that keeps profile storage testable."""

    def get_password(self, service_name: str, username: str) -> str | None:
        """Return a stored secret, if one exists."""

    def set_password(self, service_name: str, username: str, password: str) -> None:
        """Store a secret."""

    def delete_password(self, service_name: str, username: str) -> None:
        """Delete a secret."""


@dataclass(frozen=True, slots=True)
class DeviceProfile:
    """Non-secret metadata needed to reconnect to a paired TV."""

    name: str
    host: str
    device_id: str
    device_name: str

    def __post_init__(self) -> None:
        name = self.name.strip()
        host = self.host.strip()
        device_id = self.device_id.strip()
        device_name = self.device_name.strip()
        if not _NAME_PATTERN.fullmatch(name):
            raise ValueError(
                "profile name must start with a letter or number and contain only "
                "letters, numbers, '.', '_' or '-'"
            )
        if not host or any(character.isspace() for character in host):
            raise ValueError("profile host must be a non-empty host without whitespace")
        if not device_id:
            raise ValueError("profile device_id must not be empty")
        if not device_name:
            raise ValueError("profile device_name must not be empty")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "host", host)
        object.__setattr__(self, "device_id", device_id)
        object.__setattr__(self, "device_name", device_name)


class ProfileStore:
    """Persist profiles on disk and their auth tokens in the OS keyring."""

    def __init__(
        self,
        path: Path | None = None,
        *,
        credentials: CredentialBackend | None = None,
    ) -> None:
        self.path = path or _DEFAULT_CONFIG_PATH
        self._credentials = credentials or keyring

    def profiles(self) -> tuple[DeviceProfile, ...]:
        """Return profiles without reading or exposing their auth tokens."""

        document = self._read()
        raw_profiles = document.get("profiles", {})
        if not isinstance(raw_profiles, dict):
            raise ValueError(f"profile file {self.path} has an invalid profiles object")
        result: list[DeviceProfile] = []
        for name, raw_profile in raw_profiles.items():
            if not isinstance(raw_profile, dict):
                raise ValueError(f"profile {name!r} is not an object")
            result.append(
                DeviceProfile(
                    name=str(name),
                    host=str(raw_profile.get("host", "")),
                    device_id=str(raw_profile.get("device_id", "")),
                    device_name=str(raw_profile.get("device_name", "")),
                )
            )
        return tuple(sorted(result, key=lambda profile: profile.name.lower()))

    def get(self, name: str) -> DeviceProfile:
        """Return one profile by alias."""

        normalized = _normalize_name(name)
        for profile in self.profiles():
            if profile.name == normalized:
                return profile
        raise KeyError(f"no vizaio-conjure profile named {normalized!r}")

    def token(self, name: str) -> str | None:
        """Read a profile token from the configured keyring backend."""

        return self._credentials.get_password(SERVICE_NAME, _normalize_name(name))

    def save(self, profile: DeviceProfile, token: str) -> None:
        """Store the token first, then atomically update non-secret metadata."""

        if not token or not token.strip():
            raise ValueError("auth token must not be empty")
        document = self._read()
        raw_profiles = document.setdefault("profiles", {})
        if not isinstance(raw_profiles, dict):
            raise ValueError(f"profile file {self.path} has an invalid profiles object")
        self._credentials.set_password(SERVICE_NAME, profile.name, token)
        raw_profiles[profile.name] = asdict(profile)
        self._write(document)

    def delete(self, name: str) -> None:
        """Delete a profile and its keyring token."""

        normalized = _normalize_name(name)
        try:
            self._credentials.delete_password(SERVICE_NAME, normalized)
        except keyring.errors.PasswordDeleteError:
            pass
        document = self._read()
        raw_profiles = document.get("profiles", {})
        if isinstance(raw_profiles, dict):
            raw_profiles.pop(normalized, None)
        self._write(document)

    def device_id(self, name: str) -> str:
        """Return a stable unique pairing identity for a profile alias."""

        normalized = _normalize_name(name)
        document = self._read()
        installation_id = document.get("installation_id")
        if not isinstance(installation_id, str) or not installation_id:
            installation_id = str(uuid.uuid4())
            document["installation_id"] = installation_id
            self._write(document)
        return f"vizaio-conjure:{installation_id}:{normalized}"

    def _read(self) -> dict[str, object]:
        if not self.path.exists():
            return {"version": CONFIG_VERSION, "profiles": {}}
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"profile file {self.path} is not valid JSON") from exc
        if not isinstance(document, dict):
            raise ValueError(f"profile file {self.path} must contain a JSON object")
        return document

    def _write(self, document: dict[str, object]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        document["version"] = CONFIG_VERSION
        temporary = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if os.name != "nt":
            os.chmod(temporary, 0o600)
        temporary.replace(self.path)
        if os.name != "nt":
            os.chmod(self.path, 0o600)


def _normalize_name(name: str) -> str:
    normalized = name.strip()
    if not _NAME_PATTERN.fullmatch(normalized):
        raise ValueError("profile name contains unsupported characters")
    return normalized
