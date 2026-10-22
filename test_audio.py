
import asyncio
import edge_tts
import pygame
import os

async def main():
    arquivo = "teste_voz.mp3"

    try:
        comunicacao = edge_tts.Communicate(
            "Olá! Eu sou o Morpheu. O sistema de áudio está funcionando.",
            "pt-BR-FranciscaNeural"
        )

        await comunicacao.save(arquivo)

        pygame.mixer.init()
        pygame.mixer.music.load(arquivo)
        pygame.mixer.music.play()

        print("Reproduzindo áudio...")

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.unload()
        print("Teste de áudio concluído.")

    except Exception as erro:
        print(f"Erro no teste: {erro}")

    finally:
        pygame.mixer.quit()

        if os.path.exists(arquivo):
            os.remove(arquivo)

asyncio.run(main())
