import argparse
import asyncio
import json

from vizaio_conjure.cli import _launch


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
