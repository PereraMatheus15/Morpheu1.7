import unittest
from unittest.mock import patch

from local_ops import executar_comando_local


class LocalCommandTests(unittest.TestCase):
    @patch("local_ops.os.system")
    def test_spoken_open_phrase_opens_notepad(self, system):
        response = executar_comando_local("Abra o bloco de notas.")

        system.assert_called_once_with("start notepad")
        self.assertIn("bloco de notas", response)

    @patch("local_ops.os.system")
    def test_youtube_falls_through_to_static_command(self, system):
        response = executar_comando_local("Abra o YouTube.")

        system.assert_not_called()
        self.assertEqual(response, "")


if __name__ == "__main__":
    unittest.main()
