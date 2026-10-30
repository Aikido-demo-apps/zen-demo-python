from types import SimpleNamespace
import unittest
from unittest.mock import patch

with patch('aikido_zen.protect'):
    from flaskr import create_app
    from flaskr.test_llm import get_llm_client


class LLMClientTests(unittest.TestCase):
    def setUp(self):
        get_llm_client.cache_clear()
        self.addCleanup(get_llm_client.cache_clear)

    def test_repeated_requests_reuse_each_provider_client(self):
        client = create_app().test_client()
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='haiku'))],
            content=[SimpleNamespace(type='text', text='haiku')],
        )
        for provider, constructor, method in (
            ('openai', 'flaskr.test_llm.OpenAI', 'chat.completions.create'),
            ('anthropic', 'flaskr.test_llm.anthropic.Anthropic', 'messages.create'),
            ('mistral', 'mistralai.client.Mistral', 'chat.complete'),
        ):
            with self.subTest(provider=provider):
                with patch(constructor) as factory:
                    invoke = factory.return_value
                    for name in method.split('.'):
                        invoke = getattr(invoke, name)
                    invoke.return_value = response
                    for _ in range(2):
                        result = client.post('/test_llm', json={
                            'message': 'hello', 'provider': provider,
                        })
                        self.assertEqual(result.status_code, 200)
                        self.assertEqual(result.get_data(as_text=True), 'haiku')
                    factory.assert_called_once()
                    self.assertEqual(invoke.call_count, 2)

    def test_creating_app_does_not_create_provider_clients(self):
        with patch('flaskr.test_llm.OpenAI') as openai:
            with patch('flaskr.test_llm.anthropic.Anthropic') as anthropic:
                with patch('mistralai.client.Mistral') as mistral:
                    create_app()
                    openai.assert_not_called()
                    anthropic.assert_not_called()
                    mistral.assert_not_called()
