import asyncio
import os
import unittest
from unittest.mock import AsyncMock, Mock, patch

from audio_engine import AudioEngine


class AudioGenerationTests(unittest.TestCase):
    def make_engine(self):
        engine = AudioEngine.__new__(AudioEngine)
        engine.voice = "pt-BR-FranciscaNeural"
        engine._last_tts_provider = None
        return engine

    def test_edge_failure_falls_back_to_local_windows_speech(self):
        engine = self.make_engine()

        def write_local_audio(_text, path):
            with open(path, "wb") as audio_file:
                audio_file.write(b"RIFF-mocked-wave")

        with (
            patch("audio_engine.sys.platform", "win32"),
            patch(
                "audio_engine.edge_tts.Communicate",
                side_effect=Exception("HTTP 403"),
            ),
            patch.object(
                engine,
                "_synthesize_windows_speech",
                side_effect=write_local_audio,
            ),
        ):
            path = asyncio.run(engine._generate_audio("Estou ouvindo."))

        try:
            self.assertEqual(engine._last_tts_provider, "windows-sapi")
            self.assertGreater(os.path.getsize(path), 0)
        finally:
            os.remove(path)

    def test_successful_edge_synthesis_does_not_use_fallback(self):
        engine = self.make_engine()
        communication = Mock()

        async def write_edge_audio(path):
            with open(path, "wb") as audio_file:
                audio_file.write(b"mocked-edge-audio")

        communication.save = AsyncMock(side_effect=write_edge_audio)
        with (
            patch("audio_engine.edge_tts.Communicate", return_value=communication),
            patch.object(engine, "_synthesize_windows_speech") as local_synthesis,
        ):
            path = asyncio.run(engine._generate_audio("Estou ouvindo."))

        try:
            self.assertEqual(engine._last_tts_provider, "edge-tts")
            self.assertGreater(os.path.getsize(path), 0)
            local_synthesis.assert_not_called()
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
