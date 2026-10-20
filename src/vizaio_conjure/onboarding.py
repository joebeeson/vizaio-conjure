"""Pairing and discovery helpers for the interactive CLI."""

from __future__ import annotations

from collections.abc import Callable

from vizaio import DeviceType, Vizio
from vizaio.discovery import DiscoveredDevice, discover

from .credentials import DeviceProfile, ProfileStore


async def discover_devices(timeout: float = 5.0) -> list[DiscoveredDevice]:
    """Discover VIZIO devices using the upstream SSDP/Zeroconf adapter."""

    return await discover(timeout=timeout)


async def pair_device(
    host: str,
    *,
    name: str,
    device_name: str,
    device_id: str,
    store: ProfileStore,
    pin_reader: Callable[[str], str],
) -> DeviceProfile:
    """Pair a TV, save its token in the keyring, and return its profile."""

    async with Vizio(host=host, device_type=DeviceType.TV) as device:
        async with device.pair_session(device_id=device_id, device_name=device_name) as session:
            print("Pairing started. Enter the PIN shown on the TV.")
            pin = pin_reader("TV PIN (not stored): ")
            token = await session.complete(pin=pin)

    profile = DeviceProfile(
        name=name,
        host=host,
        device_id=device_id,
        device_name=device_name,
    )
    store.save(profile, token)
    return profile
