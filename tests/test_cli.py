import argparse
import asyncio
import json
from pathlib import Path

from vizaio_conjure.cli import _launch
from vizaio_conjure.credentials import DeviceProfile, ProfileStore


def test_launch_dry_run_prints_normalized_target(capsys) -> None:
    args = argparse.Namespace(
        url="http://example.test/smoke",
        app_id="17",
        name_space="CONJURE",
        dry_run=True,
        host=None,
        auth_env="VIZAIO_AUTH",
    )

    assert asyncio.run(_launch(args)) == 0
    assert json.loads(capsys.readouterr().out) == {
        "url": "http://example.test/smoke",
        "app_id": "17",
        "name_space": 4,
    }


def test_launch_uses_saved_profile_token(monkeypatch, tmp_path: Path) -> None:
    class FakeCredentials:
        def __init__(self) -> None:
            self.values: dict[tuple[str, str], str] = {}

        def get_password(self, service_name: str, username: str) -> str | None:
            return self.values.get((service_name, username))

        def set_password(self, service_name: str, username: str, password: str) -> None:
            self.values[(service_name, username)] = password

        def delete_password(self, service_name: str, username: str) -> None:
            self.values.pop((service_name, username), None)

    store = ProfileStore(tmp_path / "profiles.json", credentials=FakeCredentials())
    store.save(
        DeviceProfile(
            name="living-room",
            host="tv.example:7345",
            device_id="device-id",
            device_name="vizaio-conjure",
        ),
        "AUTH:token",
    )

    class FakeVizio:
        instance: "FakeVizio | None" = None

        def __init__(self, *, host: str, device_type: object, auth_token: str) -> None:
            self.host = host
            self.device_type = device_type
            self.auth_token = auth_token
            self.config = None
            FakeVizio.instance = self

        async def __aenter__(self) -> "FakeVizio":
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def launch_app_config(self, config: object) -> None:
            self.config = config

    monkeypatch.setattr("vizaio_conjure.cli.ProfileStore", lambda: store)
    monkeypatch.setattr("vizaio_conjure.cli.Vizio", FakeVizio)
    args = argparse.Namespace(
        url="http://example.test/smoke",
        app_id="17",
        name_space="CONJURE",
        dry_run=False,
        host=None,
        device="living-room",
        auth_env="VIZAIO_AUTH",
    )

    assert asyncio.run(_launch(args)) == 0
    assert FakeVizio.instance is not None
    assert FakeVizio.instance.host == "tv.example:7345"
    assert FakeVizio.instance.auth_token == "AUTH:token"
    assert FakeVizio.instance.config.message == "http://example.test/smoke"
