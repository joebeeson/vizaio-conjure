"""Command line entry point for the first milestone."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import asdict
from getpass import getpass
from pathlib import Path

from keyring.errors import KeyringError
from vizaio import DeviceType, Vizio

from .client import ConjureClient
from .credentials import ProfileStore
from .models import ConjureTarget
from .onboarding import discover_devices, pair_device
from .server import serve_directory


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vizaio-conjure")
    subparsers = parser.add_subparsers(dest="command", required=True)

    launch = subparsers.add_parser("launch", help="launch an HTTP(S) page in Conjure")
    launch.add_argument("url")
    launch.add_argument("--host", help="TV host, including port when required")
    launch.add_argument("--device", help="saved profile alias from `devices list`")
    launch.add_argument(
        "--auth-env",
        default="VIZAIO_AUTH",
        help="environment variable containing the paired TV token",
    )
    launch.add_argument("--app-id", default="17")
    launch.add_argument("--name-space", default="CONJURE")
    launch.add_argument("--dry-run", action="store_true")

    discover = subparsers.add_parser("discover", help="find VIZIO devices on the local network")
    discover.add_argument("--timeout", type=float, default=5.0)
    discover.add_argument("--json", action="store_true", dest="as_json")

    pair = subparsers.add_parser("pair", help="pair a TV and save its token in the OS keyring")
    pair.add_argument("host", help="TV hostname or address, including port when required")
    pair.add_argument("--name", default="default", help="local profile alias")
    pair.add_argument(
        "--device-name",
        default="vizaio-conjure",
        help="name presented to the TV during pairing",
    )
    pair.add_argument("--device-id", help="stable pairing identity; generated when omitted")

    devices = subparsers.add_parser("devices", help="manage saved TV profiles")
    device_subparsers = devices.add_subparsers(dest="devices_command", required=True)
    devices_list = device_subparsers.add_parser("list", help="list profiles without secrets")
    devices_list.add_argument("--json", action="store_true", dest="as_json")
    devices_remove = device_subparsers.add_parser(
        "remove", help="remove a profile and keyring token"
    )
    devices_remove.add_argument("name")
    devices_test = device_subparsers.add_parser("test", help="verify a saved profile token")
    devices_test.add_argument("name")

    serve = subparsers.add_parser("serve", help="serve a directory for a TV to load")
    serve.add_argument("path", type=Path)
    serve.add_argument("--bind", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=8765)
    return parser


async def _launch(args: argparse.Namespace) -> int:
    target = ConjureTarget(args.url, app_id=args.app_id, name_space=args.name_space)
    if args.dry_run:
        print(
            json.dumps({"url": target.url, "app_id": target.app_id, "name_space": target.namespace})
        )
        return 0
    profile_store = ProfileStore()
    profile = None
    if getattr(args, "device", None):
        if args.host:
            raise SystemExit("--host and --device cannot be used together")
        try:
            profile = profile_store.get(args.device)
        except KeyError as exc:
            raise SystemExit(str(exc)) from exc
        host = profile.host
        try:
            token = profile_store.token(profile.name)
        except KeyringError as exc:
            raise SystemExit(
                "OS keyring is unavailable; configure a keyring backend and retry"
            ) from exc
        if not token:
            raise SystemExit(f"profile {profile.name!r} has no keyring token; pair it again")
    else:
        if not args.host:
            raise SystemExit("--host or --device is required unless --dry-run is used")
        host = args.host
        token = os.environ.get(args.auth_env)
    if not token:
        if profile is not None:
            raise SystemExit(f"profile {profile.name!r} has no keyring token; pair it again")
        raise SystemExit(f"environment variable {args.auth_env} is not set")
    async with Vizio(host=host, device_type=DeviceType.TV, auth_token=token) as device:
        await ConjureClient(device).launch_url(target)
    return 0


async def _discover(args: argparse.Namespace) -> int:
    devices = await discover_devices(timeout=args.timeout)
    if args.as_json:
        print(json.dumps([asdict(device) for device in devices], sort_keys=True))
    elif devices:
        for device in devices:
            label = device.name or device.model or "VIZIO device"
            print(f"{label}: {device.ip}:{device.port} ({device.model or 'model unknown'})")
    else:
        print("No VIZIO devices found. Try an explicit hostname or IP address.")
    return 0


async def _pair(args: argparse.Namespace) -> int:
    store = ProfileStore()
    device_id = args.device_id or store.device_id(args.name)
    try:
        profile = await pair_device(
            args.host,
            name=args.name,
            device_name=args.device_name,
            device_id=device_id,
            store=store,
            pin_reader=getpass,
        )
    except (KeyringError, ValueError) as exc:
        if isinstance(exc, KeyringError):
            raise SystemExit(
                "OS keyring is unavailable; configure a keyring backend and retry"
            ) from exc
        raise SystemExit(str(exc)) from exc
    print(f"Paired {profile.name!r} at {profile.host}; token stored in the OS keyring.")
    return 0


async def _devices(args: argparse.Namespace) -> int:
    store = ProfileStore()
    if args.devices_command == "list":
        profiles = store.profiles()
        if args.as_json:
            print(json.dumps([asdict(profile) for profile in profiles], sort_keys=True))
        elif profiles:
            for profile in profiles:
                print(f"{profile.name}: {profile.host} ({profile.device_name})")
        else:
            print("No saved VIZIO profiles.")
        return 0
    if args.devices_command == "remove":
        try:
            store.delete(args.name)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        print(f"Removed profile {args.name!r}.")
        return 0
    try:
        profile = store.get(args.name)
    except KeyError as exc:
        raise SystemExit(str(exc)) from exc
    try:
        token = store.token(profile.name)
    except KeyringError as exc:
        raise SystemExit(
            "OS keyring is unavailable; configure a keyring backend and retry"
        ) from exc
    if not token:
        raise SystemExit(f"profile {profile.name!r} has no keyring token; pair it again")
    async with Vizio(host=profile.host, device_type=DeviceType.TV, auth_token=token) as device:
        await device.ping_auth()
    print(f"Profile {profile.name!r} authenticated successfully.")
    return 0


def main() -> int:
    args = _parser().parse_args()
    if args.command == "serve":
        serve_directory(args.path, bind=args.bind, port=args.port)
        return 0
    if args.command == "discover":
        return asyncio.run(_discover(args))
    if args.command == "pair":
        return asyncio.run(_pair(args))
    if args.command == "devices":
        return asyncio.run(_devices(args))
    return asyncio.run(_launch(args))


if __name__ == "__main__":
    raise SystemExit(main())
