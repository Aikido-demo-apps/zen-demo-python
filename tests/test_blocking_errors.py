import unittest
from unittest.mock import Mock, patch

from aikido_zen.errors import (
    AikidoPathTraversal,
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
        dispatcher = patch.object(
            self.app, "handle_user_exception", wraps=self.app.handle_user_exception
        )
        self.exception_dispatch = dispatcher.start()
        self.addCleanup(dispatcher.stop)

    def blocking_call(self, error):
        self.exception_dispatch.reset_mock()
        operation = Mock()

        def reject(func, instance, args, kwargs):
            raise error

        def call(*args, **kwargs):
            return before(reject)(operation, None, args, kwargs)

        return call, operation

    def assert_handled_block(self, response, error, operation, log_exception):
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_data(as_text=True), f"Error: {error}")
        self.exception_dispatch.assert_called_once_with(error)
        operation.assert_not_called()
        log_exception.assert_not_called()

    def test_background_handler_does_not_swallow_unexpected_errors(self):
        for target in (
            "flaskr.Helpers.make_http_request",
            "flaskr.helpers.requests.get",
        ):
            with self.subTest(target=target):
                with patch("flaskr.threading.Thread") as thread:
                    response = self.client.post("/api/stored_ssrf_2", json={})
                self.assertEqual(response.status_code, 200)
                with patch("flaskr.time.sleep"):
                    with patch(
                        target,
                        side_effect=RuntimeError("unexpected background failure"),
                    ):
                        with self.assertRaisesRegex(
                            RuntimeError, "unexpected background failure"
                        ):
                            thread.call_args.kwargs["target"]()
                self.exception_dispatch.assert_not_called()

    def test_network_failures_use_flask_error_handling(self):
        for path, data in (
            ("/api/request", {"url": "http://example.test"}),
            ("/api/request2", {"url": "http://example.test"}),
            ("/api/request_different_port", {"url": "http://example.test", "port": 80}),
            ("/api/stored_ssrf", {"urlIndex": 0}),
        ):
            with self.subTest(path=path):
                self.exception_dispatch.reset_mock()
                error = OSError("network failure")
                with patch("flaskr.helpers.requests.get", side_effect=error):
                    with patch.object(self.app, "log_exception") as log_exception:
                        response = self.client.post(path, json=data)
                self.assertEqual(response.status_code, 500)
                self.exception_dispatch.assert_called_once_with(error)
                log_exception.assert_called_once()

    def test_file_failures_use_flask_error_handling(self):
        for path in ("/api/read", "/api/read2"):
            with self.subTest(path=path):
                self.exception_dispatch.reset_mock()
                error = FileNotFoundError("missing file")
                with patch("builtins.open", side_effect=error):
                    with patch.object(self.app, "log_exception") as log_exception:
                        response = self.client.get(path, query_string={"path": "test"})
                self.assertEqual(response.status_code, 500)
                self.exception_dispatch.assert_called_once_with(error)
                log_exception.assert_called_once()

    def test_sql_blocks_return_500_without_executing_the_query(self):
        for method, path, data in (
            ("POST", "/api/create", {"name": "test"}),
            ("GET", "/api/pets/1", None),
            ("GET", "/api/pets/", None),
            ("GET", "/clear", None),
        ):
            with self.subTest(path=path):
                error = AikidoSQLInjection("postgres")
                call, operation = self.blocking_call(error)
                with patch.object(DatabaseHelper, "get_db_connection") as connection:
                    cursor = (
                        connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
                    )
                    cursor.execute.side_effect = call
                    with patch.object(self.app, "log_exception") as log_exception:
                        response = self.client.open(path, method=method, json=data)
                self.assert_handled_block(response, error, operation, log_exception)

    def test_shell_blocks_are_handled_for_both_routes(self):
        for method, path, data in (
            ("POST", "/api/execute", {"userCommand": "test"}),
            ("GET", "/api/execute/test", None),
        ):
            with self.subTest(path=path):
                error = AikidoShellInjection()
                call, operation = self.blocking_call(error)
                with patch("flaskr.helpers.subprocess.Popen", side_effect=call):
                    with patch.object(self.app, "log_exception") as log_exception:
                        response = self.client.open(path, method=method, json=data)
                self.assert_handled_block(response, error, operation, log_exception)

    def test_ssrf_helpers_preserve_handled_500_and_error_message(self):
        for path, data in (
            ("/api/request", {"url": "http://blocked.example"}),
            ("/api/request2", {"url": "http://blocked.example"}),
            (
                "/api/request_different_port",
                {"url": "http://blocked.example", "port": 80},
            ),
            ("/api/stored_ssrf", {"urlIndex": 0}),
        ):
            with self.subTest(path=path):
                error = AikidoSSRF(
                    "Zen has blocked an outbound connection to blocked.example"
                )
                call, operation = self.blocking_call(error)
                with patch("flaskr.helpers.requests.get", side_effect=call):
                    with patch.object(self.app, "log_exception") as log_exception:
                        response = self.client.post(path, json=data)
                self.assert_handled_block(response, error, operation, log_exception)

    def test_file_helpers_preserve_handled_500(self):
        for path in ("/api/read", "/api/read2"):
            with self.subTest(path=path):
                error = AikidoPathTraversal()
                call, operation = self.blocking_call(error)
                with patch("builtins.open", side_effect=call):
                    with patch.object(self.app, "log_exception") as log_exception:
                        response = self.client.get(path, query_string={"path": "test"})
                self.assert_handled_block(response, error, operation, log_exception)

    def test_background_ssrf_block_remains_handled_after_response(self):
        call, operation = self.blocking_call(AikidoSSRF())
        with patch("flaskr.threading.Thread") as thread:
            response = self.client.post("/api/stored_ssrf_2", json={})
        self.assertEqual(response.status_code, 200)
        thread.return_value.start.assert_called_once()
        with patch("flaskr.time.sleep"):
            with patch("flaskr.helpers.requests.get", side_effect=call):
                thread.call_args.kwargs["target"]()
        operation.assert_not_called()
        self.exception_dispatch.assert_not_called()

    def test_file_path_construction_blocks_are_handled(self):
        for path, target in (("/api/read", "Path"), ("/api/read2", "os")):
            with self.subTest(path=path):
                error = AikidoPathTraversal()
                call, operation = self.blocking_call(error)
                with patch(f"flaskr.helpers.{target}") as builder:
                    if target == "Path":
                        builder.return_value.__truediv__.side_effect = call
                    else:
                        builder.path.join.side_effect = call
                    with patch.object(self.app, "log_exception") as log_exception:
                        response = self.client.get(path, query_string={"path": "test"})
                self.assert_handled_block(response, error, operation, log_exception)

    def test_llm_zen_block_reaches_shared_handler(self):
        error = AikidoSSRF()
        call, operation = self.blocking_call(error)
        with patch("flaskr.test_llm.OpenAI") as client:
            client.return_value.chat.completions.create.side_effect = call
            with patch.object(self.app, "log_exception") as log_exception:
                response = self.client.post(
                    "/test_llm", json={"message": "test", "provider": "openai"}
                )
        self.assert_handled_block(response, error, operation, log_exception)

    def test_ordinary_llm_error_uses_flask_error_handling(self):
        error = RuntimeError("provider failure")
        with patch("flaskr.test_llm.OpenAI", side_effect=error):
            with patch.object(self.app, "log_exception") as log_exception:
                response = self.client.post(
                    "/test_llm", json={"message": "test", "provider": "openai"}
                )
        self.assertEqual(response.status_code, 500)
        self.assertFalse(response.is_json)
        self.exception_dispatch.assert_called_once_with(error)
        log_exception.assert_called_once()

    def test_llm_input_validation_remains_400(self):
        response = self.client.post(
            "/test_llm", json={"message": "x" * 513, "provider": "openai"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"error": "Message too long"})
        self.exception_dispatch.assert_not_called()

    def test_policy_block_and_rate_limit_responses_are_unchanged(self):
        for result, status in (
            ({"block": True, "type": "blocked", "trigger": "user"}, 403),
            (
                {
                    "block": True,
                    "type": "ratelimited",
                    "trigger": "ip",
                    "ip": "192.0.2.1",
                },
                429,
            ),
        ):
            with self.subTest(status=status):
                with patch(
                    "aikido_zen.middleware.flask.should_block_request",
                    return_value=result,
                ):
                    response = self.client.get("/test_ratelimiting_1")
                self.assertEqual(response.status_code, status)

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

    def test_missing_pet_remains_404(self):
        with patch.object(DatabaseHelper, "get_db_connection") as connection:
            cursor = (
                connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
            )
            cursor.fetchone.return_value = None
            response = self.client.get("/api/pets/1")
        self.assertEqual(response.status_code, 404)

    def test_database_failures_use_flask_error_handling(self):
        for method, path, data in (
            ("POST", "/api/create", {"name": "test"}),
            ("GET", "/api/pets/1", None),
            ("GET", "/api/pets/", None),
            ("GET", "/clear", None),
        ):
            with self.subTest(path=path):
                self.exception_dispatch.reset_mock()
                error = RuntimeError("database failure")
                with patch.object(DatabaseHelper, "get_db_connection") as connection:
                    cursor = (
                        connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
                    )
                    cursor.execute.side_effect = error
                    with patch.object(self.app, "log_exception") as log_exception:
                        response = self.client.open(path, method=method, json=data)
                self.assertEqual(response.status_code, 500)
                self.exception_dispatch.assert_called_once_with(error)
                log_exception.assert_called_once()

    def test_failed_queries_return_connections_to_the_pool(self):
        for error in (RuntimeError("database failure"), AikidoSQLInjection("postgres")):
            with self.subTest(error_type=type(error)):
                with patch.object(DatabaseHelper, "_get_db_pool") as get_pool:
                    pool = get_pool.return_value
                    connection = pool.getconn.return_value
                    cursor = connection.cursor.return_value.__enter__.return_value
                    cursor.execute.side_effect = error
                    with patch.object(self.app, "log_exception"):
                        response = self.client.get("/api/pets/1")
                self.assertEqual(response.status_code, 500)
                pool.putconn.assert_called_once_with(connection)
