from pathlib import Path

import pytest

from vizaio_conjure import onboarding
from vizaio_conjure.credentials import ProfileStore


class FakeCredentials:
    def __init__(self) -> None:
        self.values: dict[tuple[str, str], str] = {}

    def get_password(self, service_name: str, username: str) -> str | None:
        return self.values.get((service_name, username))

    def set_password(self, service_name: str, username: str, password: str) -> None:
        self.values[(service_name, username)] = password

    def delete_password(self, service_name: str, username: str) -> None:
        self.values.pop((service_name, username), None)


class FakePairSession:
    async def __aenter__(self) -> "FakePairSession":
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def complete(self, *, pin: str) -> str:
        assert pin == "1234"
        return "AUTH:token"


class FakeVizio:
    def __init__(self, host: str, *, device_type: object) -> None:
        assert host == "tv.example:7345"
        assert device_type is not None

    async def __aenter__(self) -> "FakeVizio":
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    def pair_session(self, *, device_id: str, device_name: str) -> FakePairSession:
        assert device_id == "device-id"
        assert device_name == "vizaio-conjure"
        return FakePairSession()


@pytest.mark.asyncio
async def test_pairing_stores_only_resulting_token(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setattr(onboarding, "Vizio", FakeVizio)
    credentials = FakeCredentials()
    store = ProfileStore(tmp_path / "profiles.json", credentials=credentials)

    profile = await onboarding.pair_device(
        "tv.example:7345",
        name="living-room",
        device_name="vizaio-conjure",
        device_id="device-id",
        store=store,
        pin_reader=lambda prompt: "1234",
    )

    assert profile.name == "living-room"
    assert store.token("living-room") == "AUTH:token"
    assert "1234" not in (tmp_path / "profiles.json").read_text(encoding="utf-8")
    assert "AUTH:token" not in (tmp_path / "profiles.json").read_text(encoding="utf-8")
    assert "1234" not in capsys.readouterr().out
