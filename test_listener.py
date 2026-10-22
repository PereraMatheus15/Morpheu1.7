import queue
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np

from listener import Listener


class ListenerTests(unittest.TestCase):
    def create_listener(self, **kwargs):
        model = Mock()
        with patch("listener.WhisperModel", return_value=model) as model_factory:
            listener = Listener(queue.Queue(), **kwargs)

        model_factory.assert_called_once_with(
            "base",
            device="cpu",
            compute_type="int8",
        )
        return listener, model

    def test_default_command_timeout_is_eight_seconds(self):
        listener, _ = self.create_listener()

        self.assertEqual(listener.command_timeout, 8.0)

    def test_wake_word_queues_wake_and_pauses_capture(self):
        listener, _ = self.create_listener()
        stream = Mock()
        listener._audio_stream = stream

        listener._process_transcript("ÁSSISTÉNTE?!")

        self.assertTrue(listener.aguardando_comando)
        self.assertFalse(listener._resume_event.is_set())
        stream.stop.assert_called_once()
        stream.close.assert_called_once()
        self.assertEqual(
            listener.command_queue.get_nowait(),
            {"type": "wake", "text": ""},
        )

    def test_partial_wake_word_does_not_activate(self):
        listener, _ = self.create_listener()

        listener._process_transcript("assistentes")
        listener._process_transcript("préassistente")

        self.assertFalse(listener.aguardando_comando)
        self.assertTrue(listener.command_queue.empty())

    def test_command_is_ignored_before_wake_and_accepted_after_wake(self):
        listener, _ = self.create_listener()

        listener._process_transcript("Que horas são?")
        self.assertTrue(listener.command_queue.empty())

        listener._process_transcript("assistente")
        listener.command_queue.get_nowait()
        listener.resume_after_audio()
        listener._process_transcript("Que horas são?")

        self.assertFalse(listener.aguardando_comando)
        self.assertFalse(listener._resume_event.is_set())
        self.assertEqual(
            listener.command_queue.get_nowait(),
            {"type": "command", "text": "que horas são?"},
        )

    def test_silence_timeout_returns_to_wake_word_state(self):
        listener, _ = self.create_listener()
        listener._process_transcript("assistente")
        listener.command_queue.get_nowait()
        listener.resume_after_audio()
        listener._command_deadline = time.monotonic() - 0.01

        listener._expire_command_wait()

        self.assertFalse(listener.aguardando_comando)
        self.assertIsNone(listener._command_deadline)
        self.assertTrue(listener.command_queue.empty())

    def test_timeout_before_speech_does_not_read_audio(self):
        listener, _ = self.create_listener()
        listener._record_chunk = Mock()

        audio = listener._capture_phrase(start_timeout=0)

        self.assertIsNone(audio)
        listener._record_chunk.assert_not_called()

    def test_timeout_does_not_interrupt_phrase_after_speech_starts(self):
        listener, _ = self.create_listener(
            chunk_duration=0.1,
            pause_duration=0.2,
        )
        chunks = [
            np.full(listener.chunk_size, 1000, dtype=np.int16),
            np.zeros(listener.chunk_size, dtype=np.int16),
            np.zeros(listener.chunk_size, dtype=np.int16),
        ]
        listener._record_chunk = Mock(side_effect=chunks)

        audio = listener._capture_phrase(start_timeout=0.001)

        self.assertIsNotNone(audio)
        self.assertEqual(audio.size, listener.chunk_size * 3)

    def test_phrase_capture_preserves_prebuffer_and_trailing_pause(self):
        listener, _ = self.create_listener(
            chunk_duration=0.1,
            pause_duration=0.2,
        )
        quiet_before_speech = np.full(
            listener.chunk_size,
            10,
            dtype=np.int16,
        )
        speech = np.full(listener.chunk_size, 1000, dtype=np.int16)
        quiet_after_speech = np.full(
            listener.chunk_size,
            10,
            dtype=np.int16,
        )
        listener._record_chunk = Mock(
            side_effect=[
                quiet_before_speech,
                quiet_before_speech,
                speech,
                quiet_after_speech,
                quiet_after_speech,
            ]
        )

        audio = listener._capture_phrase()

        self.assertIsNotNone(audio)
        self.assertEqual(audio.size, listener.chunk_size * 5)
        np.testing.assert_array_equal(
            audio[:listener.chunk_size],
            quiet_before_speech,
        )
        np.testing.assert_array_equal(
            audio[2 * listener.chunk_size:3 * listener.chunk_size],
            speech,
        )
        np.testing.assert_array_equal(
            audio[-listener.chunk_size:],
            quiet_after_speech,
        )

    def test_persistent_near_zero_signal_restarts_stream_once(self):
        listener, _ = self.create_listener(chunk_duration=0.1)
        listener._quiet_chunk_limit = 2
        stream = Mock(active=True)
        listener._audio_stream = stream
        silence = np.zeros(listener.chunk_size, dtype=np.int16)

        listener._is_speech(silence)
        listener._is_speech(silence)
        listener._is_speech(silence)

        stream.stop.assert_called_once()
        stream.close.assert_called_once()
        self.assertTrue(listener._quiet_recovery_attempted)
        listener._is_speech(np.full(listener.chunk_size, 500, dtype=np.int16))
        self.assertFalse(listener._quiet_recovery_attempted)

    def test_stream_failure_uses_backoff_instead_of_reopening_each_chunk(self):
        listener, _ = self.create_listener()
        with (
            patch("listener.time.monotonic", return_value=100.0),
            patch("listener.sd.query_devices", return_value={"max_input_channels": 1, "name": "USB"}),
            patch("listener.sd.InputStream", side_effect=OSError("device unavailable")) as input_stream,
        ):
            listener._record_chunk()
            listener._record_chunk()

        input_stream.assert_called_once()
        self.assertEqual(listener._stream_failures, 1)
        self.assertEqual(listener._stream_retry_after, 101.0)

    def test_invalid_transcription_does_not_send_empty_command(self):
        listener, _ = self.create_listener()
        listener._process_transcript("assistente")
        listener.command_queue.get_nowait()
        listener.resume_after_audio()

        listener._process_transcript("... !!!")

        self.assertTrue(listener.aguardando_comando)
        self.assertTrue(listener.command_queue.empty())

    def test_whisper_normalizes_audio_and_uses_portuguese_settings(self):
        listener, model = self.create_listener()
        model.transcribe.return_value = (
            iter(
                [
                    SimpleNamespace(text=" Que horas ", no_speech_prob=0.1),
                    SimpleNamespace(text=" são ", no_speech_prob=0.2),
                    SimpleNamespace(text=" alucinação ", no_speech_prob=0.9),
                ]
            ),
            None,
        )
        pcm_audio = np.array([32767, -32768, 0], dtype=np.int16)

        transcript = listener._recognize(pcm_audio)

        self.assertEqual(transcript, "Que horas são")
        model.transcribe.assert_called_once()
        normalized_audio = model.transcribe.call_args.args[0]
        np.testing.assert_allclose(
            normalized_audio,
            np.array([32767 / 32768, -1.0, 0.0], dtype=np.float32),
        )
        self.assertEqual(
            model.transcribe.call_args.kwargs,
            {
                "language": "pt",
                "beam_size": 3,
                "condition_on_previous_text": False,
                "vad_filter": True,
            },
        )

    def test_audio_stream_is_closed(self):
        listener, _ = self.create_listener()
        stream = Mock()
        listener._audio_stream = stream

        listener._close_audio_stream()

        stream.stop.assert_called_once()
        stream.close.assert_called_once()
        self.assertIsNone(listener._audio_stream)


if __name__ == "__main__":
    unittest.main()
