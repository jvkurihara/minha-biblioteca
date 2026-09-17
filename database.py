"""SQLite persistence for the personal reading library."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path


STATUSES = {"quero-ler", "lendo", "concluido"}
FIELDS = {"title", "author", "status", "rating"}


class ValidationError(ValueError):
    pass


@contextmanager
def connect(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize(db_path: Path) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'quero-ler'
                    CHECK(status IN ('quero-ler', 'lendo', 'concluido')),
                rating INTEGER CHECK(rating BETWEEN 1 AND 5),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )


def validate(payload: object, *, partial: bool = False) -> dict:
    if not isinstance(payload, dict):
        raise ValidationError("Envie um objeto JSON.")
    if not payload or (partial is False and not {"title", "author"} <= payload.keys()):
        raise ValidationError("Título e autor são obrigatórios.")
    if set(payload) - FIELDS:
        raise ValidationError("O pedido contém campos desconhecidos.")

    clean = {}
    for field in ("title", "author"):
        if field in payload:
            value = payload[field]
            if not isinstance(value, str) or not value.strip() or len(value.strip()) > 200:
                raise ValidationError(f"{field} deve ter entre 1 e 200 caracteres.")
            clean[field] = value.strip()
    if "status" in payload:
        if not isinstance(payload["status"], str) or payload["status"] not in STATUSES:
            raise ValidationError("Estado inválido.")
        clean["status"] = payload["status"]
    if "rating" in payload:
        rating = payload["rating"]
        if rating is not None and (type(rating) is not int or not 1 <= rating <= 5):
            raise ValidationError("A nota deve ser um inteiro de 1 a 5.")
        clean["rating"] = rating
    if clean.get("status", "quero-ler" if not partial else None) not in (None, "concluido") and clean.get("rating") is not None:
        raise ValidationError("A nota só pode ser usada em livros concluídos.")
    return clean


def list_books(db_path: Path) -> list[dict]:
    with connect(db_path) as connection:
        rows = connection.execute(
            "SELECT * FROM books ORDER BY updated_at DESC, id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_book(db_path: Path, book_id: int) -> dict | None:
    with connect(db_path) as connection:
        row = connection.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    return dict(row) if row else None


def create_book(db_path: Path, payload: object) -> dict:
    clean = validate(payload)
    with connect(db_path) as connection:
        cursor = connection.execute(
            "INSERT INTO books (title, author, status, rating) VALUES (?, ?, ?, ?)",
            (clean["title"], clean["author"], clean.get("status", "quero-ler"), clean.get("rating")),
        )
        book_id = cursor.lastrowid
    return get_book(db_path, book_id)


def update_book(db_path: Path, book_id: int, payload: object) -> dict | None:
    clean = validate(payload, partial=True)
    current = get_book(db_path, book_id)
    if current is None:
        return None
    merged = {**current, **clean}
    if merged["status"] != "concluido":
        if "rating" in clean and clean["rating"] is not None:
            raise ValidationError("A nota só pode ser usada em livros concluídos.")
        merged["rating"] = None
    with connect(db_path) as connection:
        connection.execute(
            """UPDATE books SET title = ?, author = ?, status = ?, rating = ?,
               updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
            (merged["title"], merged["author"], merged["status"], merged["rating"], book_id),
        )
    return get_book(db_path, book_id)


def delete_book(db_path: Path, book_id: int) -> bool:
    with connect(db_path) as connection:
        cursor = connection.execute("DELETE FROM books WHERE id = ?", (book_id,))
    return cursor.rowcount > 0
