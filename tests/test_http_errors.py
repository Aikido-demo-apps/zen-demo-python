import unittest
from weakref import ref
from unittest.mock import patch

from flask import abort, request
from werkzeug.test import create_environ

with patch('aikido_zen.protect'):
    from flaskr import create_app


class HTTPErrorTests(unittest.TestCase):
    def test_http_errors_raised_by_views_release_the_request(self):
        app = create_app()
        requests = []

        @app.before_request
        def record_request():
            requests.append(ref(request._get_current_object()))

        @app.get('/view-error/<int:status>')
        def view_error(status):
            abort(status)

        for status in (400, 403, 404, 405, 500):
            with self.subTest(status=status):
                environ = create_environ('/view-error/' + str(status))
                environ['REMOTE_ADDR'] = '127.0.0.1'
                response_status = []
                response = app(
                    environ, lambda status, headers: response_status.append(status)
                )
                try:
                    b''.join(response)
                finally:
                    response.close()
                self.assertEqual(response_status, ['400 BAD REQUEST'])
                self.assertIsNone(requests[-1]())

    def test_http_errors_return_400(self):
        client = create_app().test_client()
        response = client.get('/missing-http-error-test')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Not Found', response.get_data(as_text=True))
        response.close()

        response = client.post('/test_bot_blocking')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Method Not Allowed', response.get_data(as_text=True))
        response.close()
