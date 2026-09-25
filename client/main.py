"""
Client Main Entry Point
Module Owner: Rafay (Frontend / Desktop Client Module)

Launches the ExpenseMate desktop GUI client application.
"""

import argparse
from client.api_client import ApiClient
from client.ui.main_window import MainWindow


def main():
    parser = argparse.ArgumentParser(description="ExpenseMate Desktop Client")
    parser.add_argument(
        "--server-url",
        default="http://127.0.0.1:5000",
        help="URL of the ExpenseMate Flask API server (default: http://127.0.0.1:5000)",
    )
    args = parser.parse_args()

    api_client = ApiClient(base_url=args.server_url)
    app = MainWindow(api_client=api_client)
    app.mainloop()


if __name__ == "__main__":
    main()
