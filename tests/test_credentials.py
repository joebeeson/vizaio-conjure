from pathlib import Path

import keyring
import pytest

from vizaio_conjure.credentials import SERVICE_NAME, DeviceProfile, ProfileStore


class FakeCredentials:
    def __init__(self) -> None:
        self.values: dict[tuple[str, str], str] = {}

    def get_password(self, service_name: str, username: str) -> str | None:
        return self.values.get((service_name, username))

    def set_password(self, service_name: str, username: str, password: str) -> None:
        self.values[(service_name, username)] = password

    def delete_password(self, service_name: str, username: str) -> None:
        try:
            del self.values[(service_name, username)]
        except KeyError as exc:
            raise keyring.errors.PasswordDeleteError(str(exc)) from exc


def _profile() -> DeviceProfile:
    return DeviceProfile(
        name="living-room",
        host="tv-living-room.beeson.lan:7345",
        device_id="vizaio-conjure:test:living-room",
        device_name="vizaio-conjure",
    )


def test_profile_store_keeps_token_out_of_metadata(tmp_path: Path) -> None:
    credentials = FakeCredentials()
    store = ProfileStore(tmp_path / "profiles.json", credentials=credentials)

    store.save(_profile(), "AUTH:secret-token")

    assert credentials.values[(SERVICE_NAME, "living-room")] == "AUTH:secret-token"
    assert "AUTH:secret-token" not in (tmp_path / "profiles.json").read_text(encoding="utf-8")
    assert store.get("living-room") == _profile()
    assert store.token("living-room") == "AUTH:secret-token"


def test_device_id_is_stable_and_persisted(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "profiles.json", credentials=FakeCredentials())

    first = store.device_id("living-room")
    second = store.device_id("living-room")

    assert first == second
    assert first.startswith("vizaio-conjure:")
    assert "living-room" in first


def test_delete_removes_metadata_and_token(tmp_path: Path) -> None:
    credentials = FakeCredentials()
    store = ProfileStore(tmp_path / "profiles.json", credentials=credentials)
    store.save(_profile(), "AUTH:secret-token")

    store.delete("living-room")

    assert store.profiles() == ()
    assert credentials.values == {}


@pytest.mark.parametrize("name", ["", "has space", "-starts-with-dash", "a/b"])
def test_profile_name_is_restricted(name: str) -> None:
    with pytest.raises(ValueError):
        DeviceProfile(
            name=name,
            host="tv.example:7345",
            device_id="device-id",
            device_name="vizaio-conjure",
        )
