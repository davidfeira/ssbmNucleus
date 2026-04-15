import argparse
import os
import socketserver
import sys
import webbrowser
from http.server import SimpleHTTPRequestHandler
from pathlib import Path


DEFAULT_PORT = 4173
REPO_ROOT = Path(__file__).resolve().parents[2]


class ReusableThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the local markdown wiki.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind to.")
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the wiki in the default browser after the server starts.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.chdir(REPO_ROOT)

    handler = lambda *handler_args, **handler_kwargs: SimpleHTTPRequestHandler(
        *handler_args,
        directory=str(REPO_ROOT),
        **handler_kwargs,
    )

    with ReusableThreadingTCPServer(("127.0.0.1", args.port), handler) as server:
        url = f"http://127.0.0.1:{args.port}/wiki/"
        print(f"Serving repo root from: {REPO_ROOT}")
        print(f"Open the wiki at: {url}")
        print("Press Ctrl+C to stop.")

        if args.open:
            webbrowser.open(url)

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping wiki server.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
