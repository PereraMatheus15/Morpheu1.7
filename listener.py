import queue
import re
import threading
import time
import unicodedata
from collections import deque
from math import ceil
from typing import Optional

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from logger import logger


class Listener(threading.Thread):
    def __init__(
        self,
        command_queue: queue.Queue,
        wake_word: str = "assistente",
        energy_threshold: int = 400,
        sample_rate: int = 16000,
        chunk_duration: float = 0.1,
        max_phrase_duration: float = 10.0,
        pause_duration: float = 0.8,
        command_timeout: float = 8.0,
    ) -> None:
        super().__init__(daemon=True, name="Listener")
        self.command_queue = command_queue
        self.wake_word = self._normalize_text(wake_word)
        self.aguardando_comando = False
        self.energy_threshold = energy_threshold
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.max_phrase_duration = max_phrase_duration
        self.pause_duration = pause_duration
        self.command_timeout = command_timeout
        self._command_deadline: Optional[float] = None
        self.channels = 1
        self._stop_event = threading.Event()
        self._resume_event = threading.Event()
        self._resume_event.set()
        self._state_lock = threading.Lock()
        self._audio_stream = None
        self._input_device = 1
        self._stream_failures = 0
        self._stream_retry_after = 0.0
        self._quiet_chunks = 0
        self._quiet_recovery_attempted = False
        self._quiet_chunk_limit = max(1, ceil(5.0 / self.chunk_duration))
        self.chunk_size = int(self.sample_rate * self.chunk_duration)
        self.whisper_model = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8",
        )
        logger.info("Faster-Whisper carregado.")

    def run(self) -> None:
        try:
            while not self._stop_event.is_set():
                try:
                    if not self._wait_until_resumed():
                        break

                    remaining_timeout = self._remaining_command_timeout()
                    audio = self._capture_phrase(start_timeout=remaining_timeout)

                    if self._stop_event.is_set():
                        break

                    if audio is None:
                        self._expire_command_wait()
                        continue

                    if not self._resume_event.is_set():
                        continue

                    frase = self._recognize(audio)
                    if self._stop_event.is_set() or not self._resume_event.is_set():
                        continue

                    if not frase:
                        logger.debug("Transcrição vazia ou inválida; ignorada.")
                        self._expire_command_wait()
                        continue

                    logger.info(f"Texto reconhecido: {frase}")
                    self._process_transcript(frase)
                except Exception as exc:
                    logger.error(f"Falha no Listener: {exc}", exc_info=True)
                    if not self._stop_event.is_set():
                        time.sleep(0.5)
        finally:
            self._close_audio_stream()

    def stop(self) -> None:
        self._stop_event.set()
        self._resume_event.set()

    def resume_after_audio(self) -> None:
        with self._state_lock:
            if self.aguardando_comando:
                self._command_deadline = time.monotonic() + self.command_timeout
                logger.info("Aguardando comando.")
            else:
                logger.info("Retornando ao modo de espera.")
                logger.info("Aguardando palavra de ativação.")
            self._resume_event.set()

    def _process_transcript(self, transcript: str) -> None:
        normalized = self._normalize_text(transcript)

        if not normalized:
            logger.debug("Transcrição vazia após normalização; ignorada.")
            return

        command = None

        with self._state_lock:
            if not self.aguardando_comando:
                words = normalized.split()

                if self.wake_word not in words:
                    logger.debug(
                        f"Ignorado sem palavra de ativação: {transcript}"
                    )
                    return

                logger.info("Palavra de ativação detectada: assistente")

                # Verifica se existe um comando após a palavra de ativação.
                wake_index = words.index(self.wake_word)
                command_words = words[wake_index + 1:]
                direct_command = " ".join(command_words).strip()

                if direct_command:
                    # Modo direto: "Assistente, que horas são?"
                    self.aguardando_comando = False
                    self._command_deadline = None
                    self._resume_event.clear()
                    self._close_audio_stream()
                    command = direct_command
                    self.command_queue.put({
                        "type": "command",
                        "text": command,
                    })
                else:
                    # Modo tradicional: "Assistente" e depois o comando.
                    self.aguardando_comando = True
                    self._command_deadline = None
                    self._resume_event.clear()
                    self._close_audio_stream()
                    self.command_queue.put({
                        "type": "wake",
                        "text": "",
                    })
                    return
            else:
                # Comando recebido após ativação.
                self.aguardando_comando = False
                self._command_deadline = None
                self._resume_event.clear()
                self._close_audio_stream()
                command = " ".join(transcript.casefold().split())
                self.command_queue.put({
                    "type": "command",
                    "text": command,
                })

        if command:
            logger.info(f"Comando reconhecido: {command}")
            logger.info("Comando enviado para processamento.")

    @staticmethod
    def _normalize_text(text: str) -> str:
        decomposed = unicodedata.normalize("NFKD", text.casefold())
        without_accents = "".join(
            char for char in decomposed if not unicodedata.combining(char)
        )
        return " ".join(re.findall(r"[^\W_]+", without_accents, re.UNICODE))

    def _remaining_command_timeout(self) -> Optional[float]:
        with self._state_lock:
            if not self.aguardando_comando or self._command_deadline is None:
                return None
            return max(0.0, self._command_deadline - time.monotonic())

    def _expire_command_wait(self) -> None:
        with self._state_lock:
            if (
                not self.aguardando_comando
                or self._command_deadline is None
                or time.monotonic() < self._command_deadline
            ):
                return

            self.aguardando_comando = False
            self._command_deadline = None
            logger.info("Tempo limite aguardando comando; retornando ao modo de espera.")

    def _wait_until_resumed(self) -> bool:
        while not self._stop_event.is_set():
            if self._resume_event.wait(timeout=0.1):
                return True
        return False

    def _capture_phrase(
        self,
        start_timeout: Optional[float] = None,
    ) -> Optional[np.ndarray]:
        try:
            if self.sample_rate != 16000 or self.channels != 1:
                raise ValueError("Faster-Whisper requer áudio mono a 16 kHz.")

            buffer_size = max(1, ceil(0.3 / self.chunk_duration))
            pre_buffer = deque(maxlen=buffer_size)
            started_at = time.monotonic()

            while not self._stop_event.is_set():
                if not self._resume_event.is_set():
                    return None
                if (
                    start_timeout is not None
                    and time.monotonic() - started_at >= start_timeout
                ):
                    return None

                chunk = self._record_chunk()
                if not self._resume_event.is_set():
                    return None
                pre_buffer.append(chunk)

                if self._is_speech(chunk):
                    phrase_chunks = list(pre_buffer)
                    break

            if self._stop_event.is_set():
                return None
            if not self._resume_event.is_set():
                return None

            silence_chunks = 0
            max_silence_chunks = max(
                1, ceil(self.pause_duration / self.chunk_duration)
            )
            max_chunks = max(
                1, ceil(self.max_phrase_duration / self.chunk_duration)
            )

            while (
                len(phrase_chunks) < max_chunks
                and not self._stop_event.is_set()
            ):
                if not self._resume_event.is_set():
                    return None
                chunk = self._record_chunk()
                if not self._resume_event.is_set():
                    return None
                phrase_chunks.append(chunk)

                if self._is_speech(chunk):
                    silence_chunks = 0
                else:
                    silence_chunks += 1

                    if silence_chunks >= max_silence_chunks:
                        break

            return np.concatenate(phrase_chunks, axis=0)

        except Exception as exc:
            logger.error(f"Erro de captura: {exc}")
            time.sleep(0.5)
            return None

    def _record_chunk(self) -> np.ndarray:
        if self._audio_stream is None and time.monotonic() < self._stream_retry_after:
            return np.zeros(self.chunk_size, dtype=np.int16)

        try:
            if self._audio_stream is None:
                self._input_device = self._select_input_device()
                device_info = sd.query_devices(self._input_device)
                self._audio_stream = sd.InputStream(
                    device=self._input_device,
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype="int16",
                    blocksize=self.chunk_size,
                )
                self._audio_stream.start()
                self._stream_failures = 0
                self._stream_retry_after = 0.0
                logger.info(
                    f"Microfone ativo: dispositivo {self._input_device} "
                    f"({device_info['name']})."
                )

            if not self._audio_stream.active:
                raise RuntimeError("O stream do microfone está inativo.")

            audio, overflowed = self._audio_stream.read(
                self.chunk_size
            )

            if overflowed:
                logger.warning("Overflow na captura de áudio.")

            if audio.shape != (self.chunk_size, self.channels):
                raise RuntimeError(
                    f"Formato inesperado do áudio capturado: {audio.shape}."
                )

            return audio[:, 0].copy()
        except Exception as exc:
            logger.error(f"Falha ao gravar áudio: {exc}")
            self._close_audio_stream()
            self._stream_failures += 1
            retry_delay = min(2 ** (self._stream_failures - 1), 30)
            self._stream_retry_after = time.monotonic() + retry_delay
            logger.warning(
                f"Nova tentativa de abrir o microfone em {retry_delay} s."
            )
            return np.zeros(self.chunk_size, dtype=np.int16)

    def _select_input_device(self) -> int:
        try:
            info = sd.query_devices(self._input_device)
            if info["max_input_channels"] >= self.channels:
                return self._input_device
        except Exception as exc:
            logger.warning(
                f"Dispositivo de entrada {self._input_device} indisponível "
                f"({type(exc).__name__}); procurando entrada padrão."
            )

        default_device = sd.default.device[0]
        if default_device is not None and default_device >= 0:
            info = sd.query_devices(default_device)
            if info["max_input_channels"] >= self.channels:
                logger.warning(f"Usando dispositivo de entrada padrão {default_device}.")
                return int(default_device)

        for index, info in enumerate(sd.query_devices()):
            if info["max_input_channels"] >= self.channels:
                logger.warning(f"Usando dispositivo de entrada disponível {index}.")
                return index

        raise RuntimeError("Nenhum dispositivo de entrada de áudio está disponível.")

    def _close_audio_stream(self) -> None:
        if self._audio_stream is None:
            return

        stream = self._audio_stream
        self._audio_stream = None
        try:
            stream.stop()
        except Exception as exc:
            logger.error(f"Falha ao parar stream do microfone: {exc}")
        try:
            stream.close()
            logger.info("Stream do microfone encerrado.")
        except Exception as exc:
            logger.error(f"Falha ao fechar stream do microfone: {exc}")

    def _is_speech(self, chunk: np.ndarray) -> bool:
        if chunk.size == 0:
            return False

        audio = chunk.astype(np.float32)
        energy = float(np.mean(np.abs(audio)))

        if energy >= self.energy_threshold:
            self._quiet_chunks = 0
            self._quiet_recovery_attempted = False
            return True

        if energy < 1.0:
            self._quiet_chunks += 1
            if (
                self._quiet_chunks >= self._quiet_chunk_limit
                and not self._quiet_recovery_attempted
            ):
                active = (
                    self._audio_stream is not None
                    and self._audio_stream.active
                )
                logger.warning(
                    "Sinal do microfone quase zerado por 5 s "
                    f"(stream ativo={active}, dispositivo={self._input_device}); "
                    "verificando a captura e tentando uma recuperação controlada."
                )
                self._quiet_recovery_attempted = True
                if self._audio_stream is not None:
                    self._close_audio_stream()
                    self._stream_retry_after = 0.0

        return False

    def _recognize(self, audio: np.ndarray) -> str:
        try:
            pcm_audio = np.asarray(audio, dtype=np.int16)
            normalized_audio = pcm_audio.astype(np.float32) / 32768.0
            segments, _ = self.whisper_model.transcribe(
                normalized_audio,
                language="pt",
                beam_size=3,
                condition_on_previous_text=False,
                vad_filter=True,
            )

            transcript_parts = []
            for segment in segments:
                text = segment.text.strip()
                if text and getattr(segment, "no_speech_prob", 0.0) < 0.6:
                    transcript_parts.append(text)

            return " ".join(transcript_parts).strip()

        except Exception as exc:
            logger.error(f"Erro no reconhecimento Faster-Whisper: {exc}", exc_info=True)
            return ""
