import unittest
from unittest.mock import Mock, patch

from aikido_zen.errors import (
    AikidoException,
    AikidoNoSQLInjection,
    AikidoPathTraversal,
    AikidoRateLimiting,
    AikidoShellInjection,
    AikidoSQLInjection,
    AikidoSSRF,
)
from aikido_zen.sinks import before

with patch("aikido_zen.protect"):
    from flaskr import create_app
    from flaskr.database import DatabaseHelper


class BlockingErrorTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["PROPAGATE_EXCEPTIONS"] = False
        self.client = self.app.test_client()

    def test_expected_blocks_return_403_without_executing_the_operation(self):
        for exception_type in (
            AikidoException,
            AikidoSQLInjection,
            AikidoNoSQLInjection,
            AikidoShellInjection,
            AikidoPathTraversal,
            AikidoSSRF,
        ):
            with self.subTest(exception_type=exception_type):
                operation = Mock()

                def reject(func, instance, args, kwargs):
                    raise exception_type()

                def create_pet(name):
                    return before(reject)(operation, None, (name,), {})

                with patch.object(DatabaseHelper, "create_pet_by_name", create_pet):
                    with patch.object(self.app, "log_exception") as log_exception:
                        response = self.client.post(
                            "/api/create", json={"name": "test"}
                        )
                self.assertEqual(response.status_code, 403)
                self.assertEqual(
                    response.get_data(as_text=True), "You are blocked by Zen."
                )
                operation.assert_not_called()
                log_exception.assert_not_called()

    def test_rate_limit_exception_returns_429(self):
        with patch.object(
            DatabaseHelper, "create_pet_by_name", side_effect=AikidoRateLimiting
        ):
            with patch.object(self.app, "log_exception") as log_exception:
                response = self.client.post("/api/create", json={"name": "test"})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(
            response.get_data(as_text=True), "You are rate limited by Zen."
        )
        log_exception.assert_not_called()

    def test_unexpected_exception_remains_a_logged_500(self):
        with patch.object(
            DatabaseHelper, "create_pet_by_name", side_effect=RuntimeError("failure")
        ):
            with patch.object(self.app, "log_exception") as log_exception:
                response = self.client.post("/api/create", json={"name": "test"})
        self.assertEqual(response.status_code, 500)
        log_exception.assert_called_once()

    def test_successful_request_is_unchanged(self):
        with patch.object(
            DatabaseHelper, "create_pet_by_name", return_value=1
        ) as create_pet:
            response = self.client.post("/api/create", json={"name": "test"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(as_text=True), "Success!")
        create_pet.assert_called_once_with("test")

    def test_missing_route_remains_404(self):
        response = self.client.get("/missing-file")
        self.assertEqual(response.status_code, 404)
