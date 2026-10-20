"""Small adapter around the upstream :mod:`vizaio` control client."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol

from vizaio import AppConfig

from .models import ConjureTarget


class ConjureDevice(Protocol):
    """Minimum upstream surface required by the Conjure adapter."""

    async def launch_app_config(self, config: AppConfig) -> None:
        """Launch a raw SmartCast app configuration."""

        ...


class ConjureClient:
    """Launch Conjure targets through an existing ``vizaio`` device."""

    def __init__(self, device: ConjureDevice) -> None:
        self._device = device

    async def launch_url(self, target: ConjureTarget | str) -> ConjureTarget:
        """Launch a validated target and return the normalized target."""

        normalized = target if isinstance(target, ConjureTarget) else ConjureTarget(target)
        await self._device.launch_app_config(
            AppConfig(
                app_id=normalized.app_id,
                name_space=normalized.namespace,
                message=normalized.url,
            )
        )
        return normalized


LaunchFactory = Callable[[], Awaitable[ConjureDevice]]
