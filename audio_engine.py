
import asyncio
import os
import subprocess
import sys
import tempfile
import threading
from queue import Queue, Empty

import edge_tts
import pygame
from logger import logger


class AudioEngine:
    def __init__(self):
        self.voice = "pt-BR-FranciscaNeural"
        self.queue = Queue()
        self._stop_event = threading.Event()
        self._worker = None
        self._last_tts_provider = None

        pygame.mixer.init()

        self._worker = threading.Thread(
            target=self._process_queue,
            daemon=True
        )
        self._worker.start()

    def _process_queue(self):
        while not self._stop_event.is_set():
            try:
                text = self.queue.get(timeout=0.2)
            except Empty:
                continue

            try:
                if text and not self._stop_event.is_set():
                    asyncio.run(self._generate_and_play(text))
            except Exception as exc:
                logger.error(f"Falha no processamento TTS: {type(exc).__name__}")
            finally:
                self.queue.task_done()

    async def _generate_and_play(self, text):
        arquivo = None

        try:
            arquivo = await self._generate_audio(text)
            if self._stop_event.is_set():
                return

            pygame.mixer.music.load(arquivo)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                if self._stop_event.is_set():
                    pygame.mixer.music.stop()
                    break

                pygame.time.Clock().tick(20)

        except Exception as exc:
            logger.error(f"Falha ao gerar ou reproduzir áudio: {type(exc).__name__}")

        finally:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except pygame.error as exc:
                logger.debug(f"Falha ao liberar áudio: {type(exc).__name__}")

            if arquivo and os.path.exists(arquivo):
                try:
                    os.remove(arquivo)
                except OSError as exc:
                    logger.warning(f"Não foi possível remover arquivo TTS: {type(exc).__name__}")

    async def _generate_audio(self, text):
        arquivo = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp:
                arquivo = temp.name

            await edge_tts.Communicate(text, self.voice).save(arquivo)
            self._last_tts_provider = "edge-tts"
            return arquivo
        except Exception as exc:
            if arquivo and os.path.exists(arquivo):
                try:
                    os.remove(arquivo)
                except OSError:
                    logger.warning("Não foi possível limpar o áudio Edge-TTS temporário.")

            status_code = getattr(exc, "status_code", getattr(exc, "status", None))
            if status_code == 403 or "403" in str(exc):
                logger.warning(
                    "Edge-TTS recusou a solicitação (HTTP 403); tentando voz local."
                )
            else:
                logger.warning(
                    f"Edge-TTS indisponível ({type(exc).__name__}); tentando voz local."
                )

        if sys.platform != "win32":
            self._last_tts_provider = None
            raise RuntimeError("A voz alternativa local só está disponível no Windows.")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
            arquivo = temp.name
        os.remove(arquivo)

        try:
            await asyncio.to_thread(self._synthesize_windows_speech, text, arquivo)
            if not os.path.exists(arquivo) or os.path.getsize(arquivo) == 0:
                raise RuntimeError("A voz local não gerou áudio.")
            self._last_tts_provider = "windows-sapi"
            logger.info("Síntese local do Windows concluída.")
            return arquivo
        except Exception:
            if os.path.exists(arquivo):
                os.remove(arquivo)
            self._last_tts_provider = None
            logger.error("Edge-TTS e voz local falharam ao gerar áudio.")
            raise

    @staticmethod
    def _synthesize_windows_speech(text, output_path):
        script = (
            "$ErrorActionPreference = 'Stop'; "
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$voices = $s.GetInstalledVoices() | Where-Object { "
            "$_.Enabled -and $_.VoiceInfo.Culture.Name -eq 'pt-BR' }; "
            "if ($voices) { $s.SelectVoice($voices[0].VoiceInfo.Name) }; "
            "$s.SetOutputToWaveFile($env:MORPHEU_TTS_OUTPUT); "
            "$s.Speak($env:MORPHEU_TTS_TEXT); $s.Dispose()"
        )
        environment = os.environ.copy()
        environment["MORPHEU_TTS_OUTPUT"] = output_path
        environment["MORPHEU_TTS_TEXT"] = text
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            check=True,
            timeout=30,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=environment,
        )

    def enqueue_text(self, text):
        if text and not self._stop_event.is_set():
            self.queue.put(text)

    def interrupt(self):
        # Interrompe o áudio atual e descarta mensagens pendentes.
        pygame.mixer.music.stop()

        # Descarta mensagens pendentes de forma sincronizada.
        with self.queue.mutex:
            quantidade = len(self.queue.queue)
            self.queue.queue.clear()
            self.queue.unfinished_tasks -= quantidade

            if self.queue.unfinished_tasks == 0:
                self.queue.all_tasks_done.notify_all()

    def shutdown(self):
        # Sinaliza o encerramento da thread de áudio.
        self._stop_event.set()

        # Interrompe a reprodução atual.
        pygame.mixer.music.stop()

        # Aguarda a thread finalizar.
        if self._worker is not None and self._worker.is_alive():
            self._worker.join(timeout=5.0)

        # Libera o mixer apenas após a thread terminar.
        if self._worker is None or not self._worker.is_alive():
            pygame.mixer.quit()
        else:
            logger.warning("Thread de áudio ainda ativa durante o encerramento.")
