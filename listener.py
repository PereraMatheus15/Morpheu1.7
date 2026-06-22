import queue
import threading
import time

import speech_recognition as sr
from logger import logger


class Listener(threading.Thread):
    def __init__(
        self,
        command_queue: queue.Queue,
        wake_word: str = "jarvis",
        energy_threshold: int = 250,
    ) -> None:
        super().__init__(daemon=True, name="Listener")
        self.command_queue = command_queue
        self.wake_word = wake_word.lower()
        self.energy_threshold = energy_threshold
        self._stop_event = threading.Event()
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.energy_threshold = self.energy_threshold
        self.recognizer.pause_threshold = 1.2

    def run(self) -> None:
        while not self._stop_event.is_set():
            logger.info(f"Listener ativo. Thread alive={self.is_alive()}")
            try:
                with sr.Microphone() as source:
                    logger.info("Monitorando ambiente em silêncio")
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.8)

                    while not self._stop_event.is_set():
                        logger.info("Listener aguardando fala")
                        try:
                            audio = self.recognizer.listen(
                                source,
                                timeout=None,
                                phrase_time_limit=10,
                            )
                            logger.info("Áudio capturado")
                        except Exception as exc:
                            logger.error(f"Erro de captura: {exc}")
                            time.sleep(0.5)
                            continue

                        frase = self._recognize(audio)
                        if not frase:
                            logger.debug("Nenhuma frase reconhecida")
                            continue

                        logger.info(f"Texto reconhecido: {frase}")
                        if self.wake_word in frase:
                            logger.info(f"Wake word detectada: {frase}")
                            self.command_queue.put({"type": "wake", "text": frase})
                        else:
                            logger.debug(f"Ignorado sem wake-word: {frase}")
            except Exception as exc:
                logger.error(f"Falha de microfone: {exc}")
                time.sleep(1.0)

    def stop(self) -> None:
        self._stop_event.set()

    def _recognize(self, audio: sr.AudioData) -> str:
        try:
            resultado = self.recognizer.recognize_google(audio, language="pt-BR")
            return resultado.lower()
        except sr.UnknownValueError:
            return ""
        except Exception as exc:
            logger.error(f"Reconhecimento falhou: {exc}")
            return ""
