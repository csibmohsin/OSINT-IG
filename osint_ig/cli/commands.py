"""Command-line interface for OSINT IG.

Usage:
    python -m osint_ig serve [--host 127.0.0.1] [--port 8000] [--reload]
    python -m osint_ig auth [--sessionid <cookie>] [--username <handle>]
    python -m osint_ig info
"""
import argparse
import getpass
import sys

from osint_ig import (
    __author__,
    __organization_full__,
    __product__,
    __tagline__,
    __version__,
)


def _cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run(
        "osint_ig.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


def _cmd_auth(args: argparse.Namespace) -> int:
    from osint_ig.core.exceptions import ProviderError
    from osint_ig.instagram.auth import (
        login_with_credentials,
        save_session_by_sessionid,
    )

    if args.sessionid:
        try:
            res = save_session_by_sessionid(args.sessionid.strip())
            print(f"[OK] Authenticated via sessionid as @{res.get('username')} (ID: {res.get('user_id')}).")
            return 0
        except ProviderError as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 1

    username = args.username or input("Instagram username: ").strip()
    password = getpass.getpass("Instagram password: ")
    try:
        res = login_with_credentials(username, password)
        print(f"[OK] Authenticated as @{res.get('username')} (ID: {res.get('user_id')}).")
        return 0
    except ProviderError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        print("Tip: If Instagram challenges password login, pass --sessionid <cookie> or configure it in Settings.", file=sys.stderr)
        return 1


def _cmd_info(_args: argparse.Namespace) -> int:
    print(f"{__product__} v{__version__} — {__tagline__}")
    print(f"Developed by {__author__} | {__organization_full__}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="osint-ig",
        description=f"{__product__} — {__tagline__}",
    )
    sub = parser.add_subparsers(dest="command")

    serve_p = sub.add_parser("serve", help="Start the local OSINT IG web server")
    serve_p.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    serve_p.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    serve_p.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    serve_p.set_defaults(func=_cmd_serve)

    auth_p = sub.add_parser("auth", help="Authenticate and save an Instagram session")
    auth_p.add_argument("--sessionid", help="Browser Instagram sessionid cookie")
    auth_p.add_argument("--username", help="Instagram username (prompts for password)")
    auth_p.set_defaults(func=_cmd_auth)

    info_p = sub.add_parser("info", help="Display OSINT IG version and attribution")
    info_p.set_defaults(func=_cmd_info)

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        return _cmd_serve(argparse.Namespace(host="127.0.0.1", port=8000, reload=False))
    return args.func(args)
