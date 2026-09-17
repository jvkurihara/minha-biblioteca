import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app import Handler
from database import initialize


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        db_path = Path(self.temp.name) / 'library.db'
        initialize(db_path)
        handler = type('TestHandler', (Handler,), {'db_path': db_path})
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def call(self, method, path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        request = Request(self.base + path, data=data, method=method,
                          headers={'Content-Type': 'application/json'})
        try:
            response = urlopen(request)
        except HTTPError as error:
            response = error
        with response:
            body = response.read()
            return response.status, json.loads(body) if body else None

    def test_crud_over_http(self):
        status, book = self.call('POST', '/api/books', {'title': 'Duna', 'author': 'Frank Herbert'})
        self.assertEqual(status, 201)
        self.assertEqual(self.call('GET', '/api/books')[1][0]['title'], 'Duna')
        status, edited = self.call('PATCH', f"/api/books/{book['id']}",
                                   {'status': 'concluido', 'rating': 5})
        self.assertEqual((status, edited['rating']), (200, 5))
        self.assertEqual(self.call('DELETE', f"/api/books/{book['id']}")[0], 204)
        self.assertEqual(self.call('GET', '/api/books')[1], [])

    def test_validation_error(self):
        status, response = self.call('POST', '/api/books', {'title': '', 'author': 'A'})
        self.assertEqual(status, 400)
        self.assertIn('error', response)


if __name__ == '__main__':
    unittest.main()
