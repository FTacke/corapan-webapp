#!/usr/bin/env python3
"""
Start Flask app with Waitress WSGI server (Production-ready for Windows).

Usage:
    python scripts/start_waitress.py [--host HOST] [--port PORT] [--threads THREADS]
"""

import os
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Start CO.RA.PAN Flask app with Waitress"
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind (default: 8000)"
    )
    parser.add_argument(
        "--threads", type=int, default=4, help="Worker threads (default: 4)"
    )
    args = parser.parse_args()

    # Set environment
    os.environ["FLASK_ENV"] = "production"
    os.environ.setdefault("BLS_BASE_URL", "http://localhost:8081/blacklab-server")

    # Import after env setup
    from src.app.main import app
    from waitress import serve

    print(
        f"Starting Waitress WSGI server on {args.host}:{args.port} (threads={args.threads})"
    )
    print(f"BLS_BASE_URL: {os.environ.get('BLS_BASE_URL')}")
    print("Press Ctrl+C to stop")

    serve(app, host=args.host, port=args.port, threads=args.threads)


if __name__ == "__main__":
    main()
