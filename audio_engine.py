import asyncio
import edge_tts
import os
import pygame
from threading import Thread

class AudioEngine:
    def __init__(self):
        self.voice = "pt-BR-FranciscaNeural"
        self.temp_file = "temp_audio.mp3"
        pygame.mixer.init()

    def _play_audio(self, text):
        asyncio.run(self._generate_and_play(text))

    async def _generate_and_play(self, text):
        try:
            # Gera o áudio usando o motor neural da Microsoft
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(self.temp_file)
            
            # Reproduz com pygame
            pygame.mixer.music.load(self.temp_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            # Limpeza
            pygame.mixer.music.unload()
            if os.path.exists(self.temp_file):
                os.remove(self.temp_file)
        except Exception as e:
            print(f"Erro ao gerar áudio: {e}")

    def enqueue_text(self, text):
        # Roda em thread separada para não travar o loop principal
        Thread(target=self._play_audio, args=(text,), daemon=True).start()

    def interrupt(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()