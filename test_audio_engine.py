
import time
from audio_engine import AudioEngine

engine = AudioEngine()

try:
    print("Teste de interrupção iniciado...")

    engine.enqueue_text(
        "Esta é uma mensagem longa para testar se o Morpheu consegue interromper "
        "a reprodução de áudio imediatamente quando recebe um comando de parada."
    )

    time.sleep(2)

    print("Enviando comando de interrupção...")
    engine.interrupt()

    print("Interrupção solicitada.")

finally:
    engine.shutdown()
