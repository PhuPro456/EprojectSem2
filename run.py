"""One-command launcher for BookStore Pro.

    python run.py                 start everything (Postgres in Docker + API + website)
    python run.py --sqlite        skip Docker, use backend/dev.db instead
    python run.py --port 8080     serve on another port
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
DEFAULT_PORT = 8000


def log(message: str) -> None:
    print(f"[run] {message}", flush=True)


def fail(message: str, hint: str | None = None) -> None:
    print(f"\n[run] ERROR: {message}", file=sys.stderr, flush=True)
    if hint:
        print(f"[run]        {hint}", file=sys.stderr, flush=True)
    raise SystemExit(1)


def find_env_file() -> Path | None:
    for candidate in (ROOT / ".env", BACKEND / ".env"):
        if candidate.is_file():
            return candidate
    return None


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


def python_exe() -> str:
    for candidate in (
        ROOT / ".venv" / "Scripts" / "python.exe",
        ROOT / ".venv" / "bin" / "python",
    ):
        if candidate.is_file():
            return str(candidate)
    return sys.executable


def wait_for_port(host: str, port: int, timeout: float) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as probe:
            probe.settimeout(1.5)
            if probe.connect_ex((host, port)) == 0:
                return True
        time.sleep(1)
    return False


def docker_available() -> bool:
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=ROOT,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def start_postgres(database_url: str) -> None:
    parsed = urlparse(database_url.replace("postgresql+psycopg://", "postgresql://"))
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432

    if wait_for_port(host, port, 2):
        log(f"Postgres already accepting connections on {host}:{port}")
        return

    if not docker_available():
        fail(
            "Docker is not reachable, but .env points at Postgres.",
            "Start Docker Desktop, or run: python run.py --sqlite",
        )

    log("Starting Postgres container (docker compose up -d postgres)...")
    result = subprocess.run(
        # Only the database: the api/frontend services would claim ports 8000
        # and 3000, which belong to the server started below.
        ["docker", "compose", "up", "-d", "postgres"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if result.returncode != 0:
        fail(
            "docker compose up -d postgres failed.",
            (result.stderr or result.stdout).strip()[-500:]
            or "Run it manually to see the full error.",
        )

    log(f"Waiting for Postgres on {host}:{port}...")
    if not wait_for_port(host, port, 90):
        fail(
            f"Postgres did not become reachable on {host}:{port}.",
            "Check: docker compose logs postgres   (or run: python run.py --sqlite)",
        )
    log("Postgres is ready")


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the BookStore Pro website")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument(
        "--sqlite",
        action="store_true",
        help="use backend/dev.db instead of the Docker Postgres",
    )
    parser.add_argument("--no-reload", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    env = os.environ.copy()
    env_path = find_env_file()

    if args.sqlite:
        env["DATABASE_URL"] = "sqlite:///./dev.db"
        env.setdefault(
            "SECRET_KEY", "dev-only-secret-key-with-at-least-32-characters"
        )
        log("Using SQLite (backend/dev.db) - Docker not required")
    else:
        if env_path is None:
            fail(
                "No .env file found.",
                "Create one first:  copy .env.example .env   (then edit SECRET_KEY)",
            )
        config = read_env(env_path)
        database_url = config.get("DATABASE_URL", "")
        if not config.get("SECRET_KEY"):
            fail(
                f"{env_path.name} has no SECRET_KEY.",
                'Generate one: python -c "import secrets; print(secrets.token_hex(32))"',
            )
        if database_url.startswith("postgres"):
            start_postgres(database_url)
        else:
            log(f"Using {database_url.split('://', 1)[0]} from {env_path.name}")

    if not BACKEND.is_dir():
        fail("backend/ folder is missing - run this script from the project root.")

    if wait_for_port(args.host, args.port, 1):
        fail(
            f"Port {args.port} is already in use.",
            "If the Docker stack is running, open http://localhost:3000 (website) "
            f"or http://localhost:{args.port}/docs (API) instead of starting a second "
            f"server - or use: python run.py --port {args.port + 1}",
        )

    url = f"http://{args.host}:{args.port}/"
    command = [
        python_exe(),
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    if not args.no_reload:
        command.append("--reload")

    log(f"Website will open at {url}")
    log("Admin demo login: admin@bookstorepro.com / admin-password-123")
    log("Press Ctrl+C to stop")

    if not args.no_browser:
        # Give uvicorn a moment so the tab does not hit a dead port.
        threading.Timer(3.0, webbrowser.open, args=(url,)).start()

    try:
        subprocess.run(command, cwd=BACKEND, env=env)
    except KeyboardInterrupt:
        log("Stopped")


if __name__ == "__main__":
    main()
