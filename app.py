"""Dependency-free HTTP server and JSON API for Minha Biblioteca."""

from __future__ import annotations

import json
import os
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from database import ValidationError, create_book, delete_book, initialize, list_books, update_book


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
DB_PATH = Path(os.environ.get("LIBRARY_DB", ROOT / "data" / "library.db"))
BOOK_ROUTE = re.compile(r"^/api/books/([1-9][0-9]*)$")
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
}


class Handler(BaseHTTPRequestHandler):
    db_path = DB_PATH

    def respond_json(self, status: HTTPStatus, data: object) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> object:
        length = int(self.headers.get("Content-Length", "0"))
        if length < 1 or length > 16_384:
            raise ValidationError("O pedido deve ter entre 1 e 16384 bytes.")
        try:
            return json.loads(self.rfile.read(length))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValidationError("JSON inválido.") from exc

    def route(self) -> str:
        return urlsplit(self.path).path

    def do_GET(self) -> None:
        path = self.route()
        if path == "/api/books":
            self.respond_json(HTTPStatus.OK, list_books(self.db_path))
        elif path in STATIC_FILES:
            filename, content_type = STATIC_FILES[path]
            body = (STATIC / filename).read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.respond_json(HTTPStatus.NOT_FOUND, {"error": "Rota não encontrada."})

    def do_POST(self) -> None:
        if self.route() != "/api/books":
            self.respond_json(HTTPStatus.NOT_FOUND, {"error": "Rota não encontrada."})
            return
        try:
            book = create_book(self.db_path, self.read_json())
        except (ValidationError, ValueError) as exc:
            self.respond_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        self.respond_json(HTTPStatus.CREATED, book)

    def do_PATCH(self) -> None:
        match = BOOK_ROUTE.fullmatch(self.route())
        if not match:
            self.respond_json(HTTPStatus.NOT_FOUND, {"error": "Rota não encontrada."})
            return
        try:
            book = update_book(self.db_path, int(match.group(1)), self.read_json())
        except (ValidationError, ValueError) as exc:
            self.respond_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        if book is None:
            self.respond_json(HTTPStatus.NOT_FOUND, {"error": "Livro não encontrado."})
        else:
            self.respond_json(HTTPStatus.OK, book)

    def do_DELETE(self) -> None:
        match = BOOK_ROUTE.fullmatch(self.route())
        if not match:
            self.respond_json(HTTPStatus.NOT_FOUND, {"error": "Rota não encontrada."})
        elif delete_book(self.db_path, int(match.group(1))):
            self.send_response(HTTPStatus.NO_CONTENT)
            self.send_header("Content-Length", "0")
            self.end_headers()
        else:
            self.respond_json(HTTPStatus.NOT_FOUND, {"error": "Livro não encontrado."})


def main() -> None:
    initialize(DB_PATH)
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Minha Biblioteca: http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nAté logo!")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

