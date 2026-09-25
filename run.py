"""
ExpenseMate Application Runner
Integrates Hamza's Backend Module and Rafay's Frontend Module.

Single-command entry point:
- Initializes SQLite database
- Starts the Flask API server
- Ensures client-server connectivity
- Launches the desktop GUI client
- Cleans up server resources upon exit
"""

import sys
import time
import argparse
import threading
from typing import Optional
from werkzeug.serving import make_server

from server.database import init_db, DEFAULT_DB_PATH
from server.app import create_app
from client.api_client import ApiClient
from client.ui.main_window import MainWindow


class ServerThread(threading.Thread):
    """Runs the Werkzeug/Flask HTTP server in a controllable background thread."""

    def __init__(self, host: str = "127.0.0.1", port: int = 5000, db_path: Optional[str] = None):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.app = create_app(db_path=db_path)
        self.server = make_server(self.host, self.port, self.app, threaded=True)

    def run(self):
        print(f"[ExpenseMate Server] Listening on http://{self.host}:{self.port}")
        self.server.serve_forever()

    def shutdown(self):
        print("[ExpenseMate Server] Shutting down...")
        self.server.shutdown()


def wait_for_server(api_client: ApiClient, timeout: float = 5.0) -> bool:
    """Poll health endpoint until server responds or timeout occurs."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        ok, _ = api_client.check_health()
        if ok:
            return True
        time.sleep(0.1)
    return False


def main():
    parser = argparse.ArgumentParser(description="ExpenseMate — Personal Expense Manager")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="Server port (default: 5000)")
    parser.add_argument("--server-only", action="store_true", help="Run only the Flask API server")
    parser.add_argument("--client-only", action="store_true", help="Run only the desktop client GUI")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to SQLite database file")
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"

    # 1. Always ensure database schema is initialized
    print(f"[ExpenseMate] Initializing database at: {args.db_path}")
    init_db(args.db_path)

    # Mode A: Server Only
    if args.server_only:
        app = create_app(db_path=args.db_path)
        print(f"[ExpenseMate] Starting server-only mode on {base_url}")
        app.run(host=args.host, port=args.port, debug=False)
        return

    # Mode B: Client Only (Connecting to existing external server)
    if args.client_only:
        print(f"[ExpenseMate] Launching client connecting to {base_url}")
        api_client = ApiClient(base_url=base_url)
        gui = MainWindow(api_client=api_client)
        gui.mainloop()
        return

    # Mode C: Full Application (Server + Desktop Client together)
    print("[ExpenseMate] Starting Flask server in background thread...")
    server_thread = ServerThread(host=args.host, port=args.port, db_path=args.db_path)
    server_thread.start()

    api_client = ApiClient(base_url=base_url)

    print("[ExpenseMate] Waiting for server readiness...")
    if not wait_for_server(api_client, timeout=6.0):
        print(f"[ExpenseMate Error] Server failed to respond at {base_url} within 6 seconds.", file=sys.stderr)
        server_thread.shutdown()
        sys.exit(1)

    print("[ExpenseMate] Server is healthy. Launching desktop GUI client...")
    try:
        gui = MainWindow(api_client=api_client)
        gui.mainloop()
    finally:
        print("[ExpenseMate] Desktop client closed. Terminating server thread...")
        server_thread.shutdown()
        server_thread.join(timeout=2.0)
        print("[ExpenseMate] Goodbye!")


if __name__ == "__main__":
    main()
