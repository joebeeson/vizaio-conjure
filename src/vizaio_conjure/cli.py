"""Command line entry point for the first milestone."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from vizaio import DeviceType, Vizio

from .client import ConjureClient
from .models import ConjureTarget
from .server import serve_directory


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vizaio-conjure")
    subparsers = parser.add_subparsers(dest="command", required=True)

    launch = subparsers.add_parser("launch", help="launch an HTTP(S) page in Conjure")
    launch.add_argument("url")
    launch.add_argument("--host", help="TV host, including port when required")
    launch.add_argument(
        "--auth-env",
        default="VIZAIO_AUTH",
        help="environment variable containing the paired TV token",
    )
    launch.add_argument("--app-id", default="17")
    launch.add_argument("--name-space", default="CONJURE")
    launch.add_argument("--dry-run", action="store_true")

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
    if not args.host:
        raise SystemExit("--host is required unless --dry-run is used")
    token = os.environ.get(args.auth_env)
    if not token:
        raise SystemExit(f"environment variable {args.auth_env} is not set")
    async with Vizio(host=args.host, device_type=DeviceType.TV, auth_token=token) as device:
        await ConjureClient(device).launch_url(target)
    return 0


def main() -> int:
    args = _parser().parse_args()
    if args.command == "serve":
        serve_directory(args.path, bind=args.bind, port=args.port)
        return 0
    return asyncio.run(_launch(args))


if __name__ == "__main__":
    raise SystemExit(main())
