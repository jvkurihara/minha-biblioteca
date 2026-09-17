import tempfile
import unittest
from pathlib import Path

from database import ValidationError, create_book, delete_book, initialize, list_books, update_book


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / 'library.db'
        initialize(self.db)

    def tearDown(self):
        self.temp.cleanup()

    def test_book_lifecycle(self):
        book = create_book(self.db, {'title': '  O Hobbit  ', 'author': 'Tolkien'})
        self.assertEqual(book['title'], 'O Hobbit')
        self.assertEqual(book['status'], 'quero-ler')
        updated = update_book(self.db, book['id'], {'status': 'concluido', 'rating': 5})
        self.assertEqual(updated['rating'], 5)
        self.assertEqual(len(list_books(self.db)), 1)
        self.assertTrue(delete_book(self.db, book['id']))
        self.assertEqual(list_books(self.db), [])

    def test_invalid_rating_and_unknown_fields(self):
        with self.assertRaises(ValidationError):
            create_book(self.db, {'title': 'A', 'author': 'B', 'status': 'lendo', 'rating': 5})
        with self.assertRaises(ValidationError):
            create_book(self.db, {'title': 'A', 'author': 'B', 'unexpected': 'x'})

    def test_rating_cleared_when_reopening_book(self):
        book = create_book(self.db, {'title': 'A', 'author': 'B', 'status': 'concluido', 'rating': 4})
        updated = update_book(self.db, book['id'], {'status': 'lendo'})
        self.assertIsNone(updated['rating'])


if __name__ == '__main__':
    unittest.main()

