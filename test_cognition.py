import unittest
from unittest.mock import Mock, patch

from cognition import Cognition


class CognitionAuthenticationTests(unittest.TestCase):
    @patch("cognition.genai.Client")
    def test_placeholder_key_does_not_create_client(self, client):
        cognition = Cognition("your_gemini_api_key_here")

        client.assert_not_called()
        self.assertIsNone(cognition.ai_client)
        self.assertIn("GEMINI_API_KEY", cognition.ask("Pergunta"))

    def test_missing_key_returns_clear_message(self):
        cognition = Cognition(None)

        response = cognition.ask("Pergunta")

        self.assertIn("chave válida", response)

    def test_invalid_key_returns_clear_message_without_logging_exception(self):
        cognition = Cognition.__new__(Cognition)
        cognition.ai_client = Mock()
        cognition.chat_history = []
        cognition.max_history_messages = 20
        cognition.ai_client.models.generate_content.side_effect = Exception(
            "API_KEY_INVALID: secret-key-must-not-be-logged"
        )

        with self.assertLogs("morpheu", level="ERROR") as logs:
            response = cognition.ask("Pergunta")

        self.assertIn("foi recusada", response)
        self.assertNotIn("secret-key-must-not-be-logged", "\n".join(logs.output))


if __name__ == "__main__":
    unittest.main()
