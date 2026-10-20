from dataclasses import dataclass

import pytest
from vizaio import AppConfig

from vizaio_conjure import ConjureClient, ConjureTarget


@dataclass
class FakeDevice:
    calls: list[AppConfig]
    error: Exception | None = None

    async def launch_app_config(self, config: AppConfig) -> None:
        if self.error:
            raise self.error
        self.calls.append(config)


@pytest.mark.asyncio
async def test_launch_maps_target_to_upstream_config() -> None:
    device = FakeDevice([])
    target = await ConjureClient(device).launch_url("http://example.test/smoke")
    assert target.namespace == 4
    assert device.calls == [
        AppConfig(app_id="17", name_space=4, message="http://example.test/smoke")
    ]


@pytest.mark.asyncio
async def test_upstream_errors_are_preserved() -> None:
    error = RuntimeError("TV rejected launch")
    device = FakeDevice([], error=error)
    with pytest.raises(RuntimeError, match="TV rejected launch"):
        await ConjureClient(device).launch_url(ConjureTarget("https://example.test/"))
